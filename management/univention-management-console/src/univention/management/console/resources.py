#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  session handling
#
# Copyright 2006-2022 Univention GmbH
#
# https://www.univention.de/
#
# All rights reserved.
#
# The source code of this program is made available
# under the terms of the GNU Affero General Public License version 3
# (GNU AGPL V3) as published by the Free Software Foundation.
#
# Binary versions of this program provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention and not subject to the GNU AGPL V3.
#
# In the case you use this program under the terms of the GNU AGPL V3,
# the program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <https://www.gnu.org/licenses/>.

"""Implements several helper classes to handle the state of a session
and the communication with the module processes"""

import base64
import os
import time
import json
import gzip
import re
import pipes

from ipaddress import ip_address
import ldap
import six

import tornado
import tornado.gen
import tornado.web
import tornado.httpclient
import tornado.curl_httpclient
from tornado.web import HTTPError
import pycurl
from six.moves.http_client import REQUEST_ENTITY_TOO_LARGE, LENGTH_REQUIRED, NOT_FOUND, BAD_REQUEST, UNAUTHORIZED, SERVICE_UNAVAILABLE

import univention.admin.uexceptions as udm_errors

from univention.lib.i18n import Locale
from .protocol.message import Request
from .resource import Resource, UMC_HTTPError
from .pam import PamAuth, PasswordChangeFailed
from .log import CORE
from .locales import I18N, I18N_Manager
from .config import MODULE_INACTIVITY_TIMER, MODULE_COMMAND, ucr, get_int
from .error import UMC_Error, BadRequest, Forbidden, BadGateway
from .ldap import reset_cache as reset_ldap_connection_cache
from .session import moduleManager, categoryManager
from .modules.sanitizers import StringSanitizer, DictSanitizer, ListSanitizer
from .modules.decorators import copy_function_meta_data, sanitize_args

try:
	from time import monotonic
except ImportError:
	from monotonic import monotonic

REQUEST_ENTITY_TOO_LARGE, LENGTH_REQUIRED, NOT_FOUND, BAD_REQUEST, UNAUTHORIZED, SERVICE_UNAVAILABLE = int(REQUEST_ENTITY_TOO_LARGE), int(LENGTH_REQUIRED), int(NOT_FOUND), int(BAD_REQUEST), int(UNAUTHORIZED), int(SERVICE_UNAVAILABLE)

SessionHandler = None


def sanitize(*sargs, **skwargs):
	defaults = {'default': {}, 'required': True, 'may_change_value': True}
	if sargs:
		defaults.update(skwargs)
		sanitizer = ListSanitizer(sargs[0], **defaults)
	else:
		sanitizer = DictSanitizer(skwargs, **defaults)

	def _decorator(function):
		def _response(self, *args, **kwargs):
			self.request.body_arguments = sanitize_args(sanitizer, 'request.options', {'request.options': self.request.body_arguments})
			return function(self, *args, **kwargs)
		copy_function_meta_data(function, _response)
		return _response
	return _decorator


class NotFound(HTTPError):

	def __init__(self):
		super(NotFound, self).__init__(404)


class CouldNotConnect(Exception):
	pass


def allow_unauthorized(func):
	return func


class ModuleProcess(object):

	"""handles the communication with a UMC module process

	:param str module: name of the module to start
	:param str debug: debug level as a string
	:param str locale: locale to use for the module process
	"""

	def __init__(self, module, debug='0', locale=None):
		self.name = module
		self.socket = '/run/univention-management-console/%u-%lu.socket' % (os.getpid(), int(time.time() * 1000))
		modxmllist = moduleManager[module]
		python = '/usr/bin/python3' if any(modxml.python_version == 3 for modxml in modxmllist) else '/usr/bin/python2.7'
		args = [python, MODULE_COMMAND, '-m', module, '-s', self.socket, '-d', str(debug)]
		for modxml in modxmllist:
			if modxml.notifier:
				args.extend(['-n', modxml.notifier])
				break
		if locale:
			args.extend(('-l', '%s' % locale))

		CORE.process('running: %s' % ' '.join(pipes.quote(x) for x in args))
		self.__process = tornado.process.Subprocess(args)  # , stderr=tornado.process.Subprocess.STREAM)
		# self.__process.initialize()
		self.set_exit_callback(self._died)  # default
		self._client = tornado.httpclient.AsyncHTTPClient()

		self._inactivity_timer = None
		self._inactivity_counter = 0
		self._connect_timer = None
		self.__killtimer = None

	def set_exit_callback(self, callback):
		self.__process.set_exit_callback(callback)

	@tornado.gen.coroutine
	def connect(self, connect_retries=0):
		if os.path.exists(self.socket):
			raise tornado.gen.Return(True)
		elif connect_retries > 200:
			raise CouldNotConnect('timeout exceeded')
		elif self.__process and self.__process.proc.poll() is not None:
			raise CouldNotConnect('process died')
		else:
			if not connect_retries % 50:
				CORE.info('No connection to module process yet')
			connect_retries += 1
			yield tornado.gen.sleep(0.05)
			yield self.connect(connect_retries)

	@tornado.gen.coroutine
	def request(self, method, uri, headers=None, body=None):
		if uri.startswith('https://'):
			uri = 'http://' + uri[8:]
		request = tornado.httpclient.HTTPRequest(
			uri,
			method=method,
			body=body,
			headers=headers,
			allow_nonstandard_methods=True,
			follow_redirects=False,
			connect_timeout=10.0,
			request_timeout=get_int('umc/http/response-timeout', 310) + 2,  # never!
			prepare_curl_callback=lambda curl: curl.setopt(pycurl.UNIX_SOCKET_PATH, self.socket),
		)
		# watch the module's activity and kill it after X seconds inactivity
		self.reset_inactivity_timer()

		try:
			response = yield self._client.fetch(request, raise_error=True)
		except tornado.curl_httpclient.CurlError as exc:
			CORE.warn('Reaching module failed: %s' % (exc,))
			raise CouldNotConnect(exc)
		except tornado.httpclient.HTTPError as exc:
			response = exc.response
			if response is None:  # (599, 'Timeout while connecting', None)
				raise CouldNotConnect(exc)
		except ValueError as exc:  # HTTP GET request with body
			CORE.warn('Reaching module failed: %s' % (exc,))
			raise BadRequest(str(exc))

		self.reset_inactivity_timer()
		raise tornado.gen.Return(response)

	def stop(self):
		# type: () -> None
		CORE.process('ModuleProcess: stopping %r' % (self.pid(),))
		if self.__process:
			tornado.ioloop.IOLoop.instance().add_callback(self.stop_process)

	@tornado.gen.coroutine
	def stop_process(self):
		proc = self.__process.proc
		if proc.poll() is None:
			proc.terminate()
		yield tornado.gen.sleep(3.0)
		if proc.poll() is None:
			proc.kill()
		# TODO: if not succeeds, kill all childs
		CORE.info('ModuleProcess: child stopped')
		self.__process = None

	def _died(self, returncode):
		# type: (int) -> None
		pid = self.pid()
		CORE.process('ModuleProcess: child %d (%s) exited with %d' % (pid, self.name, returncode))
		# if killtimer has been set then remove it
		ioloop = tornado.ioloop.IOLoop.current()
		if self.__killtimer:
			CORE.info('Stopping kill timer)')
			ioloop.remove_timeout(self.__killtimer)
			self.__killtimer = None
#		return
#		self.invalidate_all_requests()
#		if self._inactivity_timer is not None:
#			CORE.warn('Remove inactivity timer')
#			ioloop.remove_timeout(self._inactivity_timer)
#
#	def invalidate_all_requests(self):
#		raise BadGateway('%s: %s' % (self._('Module process died unexpectedly'), self.name))

	def pid(self):
		# type: () -> int
		"""Returns process ID of module process"""
		if self.__process is None:
			return 0
		return self.__process.pid

	def reset_inactivity_timer(self):
		"""Resets the inactivity timer. This timer watches the
		inactivity of the module process. If the module did not receive
		a request for MODULE_INACTIVITY_TIMER seconds the module process
		is shut down to save resources. The timer ticks each seconds to
		handle glitches of the system clock.
		"""
		if self._inactivity_timer is None:
			ioloop = tornado.ioloop.IOLoop.current()
			self._inactivity_timer = ioloop.call_later(1000, self._inactivitiy_tick)

		self._inactivity_counter = MODULE_INACTIVITY_TIMER

	def _inactivitiy_tick(self):
		if self._inactivity_counter > 0:
			self._inactivity_counter -= 1000
			return True
		if self._mod_inactive(self):  # open requests -> waiting
			self._inactivity_counter = MODULE_INACTIVITY_TIMER
			return True

		self._inactivity_timer = None
		self._inactivity_counter = 0

		return False

	def _mod_inactive(self):
		CORE.info('The module %s is inactive for too long. Sending EXIT request to module' % self.name)
		if self.openRequests:
			CORE.info('There are unfinished requests. Waiting for %s' % ', '.join(self.openRequests))
			return True

		# mark as internal so the response will not be forwarded to the client
		req = Request('EXIT', arguments=[self.name, 'internal'])
		self.handle_request_exit(req)

		return False


class Index(Resource):
	"""Redirect to correct path when bypassing gateway"""

	def get(self):
		self.redirect('/univention/', status=305)

	def post(self, path):
		return self.get(path)


class Logout(Resource):
	"""Logout a user"""

	def get(self, **kwargs):
		session = self.current_user
		if session.saml is not None:
			return self.redirect('/univention/saml/logout', status=303)
		self.expire_session()
		self.redirect(ucr.get('umc/logout/location') or '/univention/', status=303)

	def post(self, path):
		return self.get(path)


class Nothing(Resource):

	def prepare(self, *args, **kwargs):
		super(Nothing, self).prepare(*args, **kwargs)
		raise NotFound()


class SessionInfo(Resource):
	"""Get information about the current session"""

	def get(self):
		info = {}
		session = self.current_user
		if not session.authenticated:
			raise HTTPError(int(UNAUTHORIZED))
		info['username'] = session.user.username
		info['auth_type'] = session.get_umc_auth_type()  # prior: session.saml and 'SAML'
		info['remaining'] = int(session.session_end_time - monotonic())
		self.content_negotiation(info)

	def post(self):
		return self.get()


class GetIPAddress(Resource):
	"""Get the most likely IP address of the client"""

	def get(self):
		try:
			addresses = self.addresses
		except ValueError:
			# hacking attempt
			addresses = [self.request.remote_ip]
		self.content_negotiation(addresses, False)

	@property
	def addresses(self):
		addresses = self.request.headers.get('X-Forwarded-For', self.request.remote_ip).split(',') + [self.request.remote_ip]
		addresses = set(ip_address(x.decode('ASCII', 'ignore').strip() if isinstance(x, bytes) else x.strip()) for x in addresses)
		addresses.discard(ip_address(u'::1'))
		addresses.discard(ip_address(u'127.0.0.1'))
		return tuple(address.exploded for address in addresses)

	def post(self):
		return self.get()


class NewSession(Resource):
	"""Drop all information from the current session - like a relogin"""

	def get(self):
		session = self.current_user
		session.renew()
		self.content_negotiation(None)


class Auth(Resource):
	"""Authenticate the user via PAM - either via plain password or via SAML message"""

	def parse_authorization(self):
		return  # do not call super method: prevent basic auth

	@tornado.gen.coroutine
	def post(self):
		#request.body = sanitize_args(DictSanitizer(dict(
		#	username=StringSanitizer(required=True),
		#	password=StringSanitizer(required=True),
		#	auth_type=StringSanitizer(allow_none=True),
		#	new_password=StringSanitizer(required=False, allow_none=True),
		#)), 'request', {'request': request.body})

		try:
			content_length = int(self.request.headers.get("Content-Length", 0))
		except ValueError:
			content_length = None
		if not content_length and content_length != 0:
			CORE.process('auth: missing Content-Length header')
			raise HTTPError(LENGTH_REQUIRED)

		if self.request.method in ('POST', 'PUT'):
			max_length = 2000 * 1024
			if content_length >= max_length:  # prevent some DoS
				raise HTTPError(REQUEST_ENTITY_TOO_LARGE, 'Request data is too large, allowed length is %d' % max_length)

		CORE.info('Reloading resources: UCR, modules, categories')
		ucr.load()
		moduleManager.load()
		categoryManager.load()

		self.request.body_arguments['auth_type'] = None
		self.request.body_arguments['locale'] = self.locale.code
		session = self.current_user
		result = yield session.authenticate(self.request.body_arguments)

		# create a sessionid if the user is not yet authenticated
		sessionid = self.create_sessionid(True)
		self.set_session(sessionid, session.user.username, password=session.user.password)
		self.set_status(result.status)
		if result.message:
			self.set_header('X-UMC-Message', json.dumps(result.message))
		self.content_negotiation(result.result)

	get = post


class Modules(Resource):
	"""Get a list of available modules"""

	def prepare(self):
		super(Modules, self).prepare()
		self.i18n = I18N_Manager()  # TODO: move into a session class
		self.i18n['umc-core'] = I18N()
		self.i18n.set_locale(self.locale.code)

	@allow_unauthorized
	def get(self):
		categoryManager.load()
		moduleManager.load()
		if self.get_argument('reload', False):
			CORE.info('Reloading ACLs for existing session')
			self.current_user.acls._reload_acls_and_permitted_commands()

		permitted_commands = list(self.current_user.acls.get_permitted_commands(moduleManager).values())

		favorites = self._get_user_favorites()
		modules = [
			self._module_definition(module, favorites)
			for module in permitted_commands
			if not module.flavors
		]
		modules.extend([
			self._flavor_definition(module, flavor, favorites)
			for module in permitted_commands
			for flavor in module.flavors
		])

		CORE.info('Modules: %s' % (modules,))
		self.content_negotiation({'modules': modules}, wrap=False)

	def _flavor_definition(self, module, flavor, favorites):
		favcat = []
		if '%s:%s' % (module.id, flavor.id) in favorites:
			favcat.append('_favorites_')

		translationId = flavor.translationId or module.id
		return {
			'id': module.id,
			'flavor': flavor.id,
			'name': self.i18n._(flavor.name, translationId),
			'url': self.i18n._(module.url, translationId),
			'description': self.i18n._(flavor.description, translationId),
			'icon': flavor.icon,
			'categories': (flavor.categories or (module.categories if not flavor.hidden else [])) + favcat,
			'priority': flavor.priority,
			'keywords': list(set(flavor.keywords + [self.i18n._(keyword, translationId) for keyword in flavor.keywords])),
			'version': flavor.version,
		}

	def _module_definition(self, module, favorites):
		favcat = []
		if module.id in favorites:
			favcat.append('_favorites_')
		translationId = module.translationId or module.id
		return {
			'id': module.id,
			'name': self.i18n._(module.name, translationId),
			'url': self.i18n._(module.url, translationId),
			'description': self.i18n._(module.description, translationId),
			'icon': module.icon,
			'categories': module.categories + favcat,
			'priority': module.priority,
			'keywords': list(set(module.keywords + [self.i18n._(keyword, translationId) for keyword in module.keywords])),
			'version': module.version,
		}

	def _get_user_favorites(self):
		if not self.current_user.user.user_dn:  # user not authenticated or no LDAP user
			return set(ucr.get('umc/web/favorites/default', '').split(','))
		lo = self.current_user.user.get_user_ldap_connection(no_cache=True)
		favorites = self._get_user_preferences(lo).setdefault('favorites', ucr.get('umc/web/favorites/default', '')).strip()
		return set(favorites.split(','))

	def _get_user_preferences(self, lo):
		user_dn = self.current_user.user.user_dn
		if not user_dn or not lo:
			return {}
		try:
			preferences = lo.get(user_dn, ['univentionUMCProperty']).get('univentionUMCProperty', [])
		except (ldap.LDAPError, udm_errors.base) as exc:
			CORE.warn('Failed to retrieve user preferences: %s' % (exc,))
			return {}
		preferences = (val.decode('utf-8', 'replace') for val in preferences)
		return dict(val.split(u'=', 1) if u'=' in val else (val, u'') for val in preferences)

	post = get


class Categories(Resource):
	"""Get a list of available categories"""

	def prepare(self):
		super(Categories, self).prepare()
		self.i18n = I18N_Manager()  # TODO: move into a session class
		self.i18n['umc-core'] = I18N()
		self.i18n.set_locale(self.locale.code)

	@allow_unauthorized
	def get(self):
		categoryManager.load()
		ucr.load()
		_ucr_dict = dict(ucr.items())
		categories = []
		for category in categoryManager.values():
			categories.append({
				'id': category.id,
				'icon': category.icon,
				'color': category.color,
				'name': self.i18n._(category.name, category.domain).format(**_ucr_dict),
				'priority': category.priority
			})
		CORE.info('Categories: %s' % (categories,))
		self.content_negotiation({'categories': categories}, wrap=False)

	post = get


class SetLocale(Resource):
	"""Set the locale for the session.

	.. deprecated:: 5.0
		set language via `Accept-Language` HTTP header
	"""

	@sanitize(locale=StringSanitizer(required=True))
	def post(self, locale):
		locale = self.request.body_arguments['locale']
		# self.update_language([locale])
		locale


class Upload(Resource):
	"""Handle generic file upload which is not targeted for any module"""

	def post(self):
		"""Handles a file UPLOAD request, respond with a base64 representation of the content."""

		result = []
		for name, file_objs in self.request.files.items():
			for file_obj in file_objs:
				# don't accept files bigger than umc/server/upload/max
				max_size = int(ucr.get('umc/server/upload/max', 64)) * 1024
				if len(file_obj['body']) > max_size:
					raise BadRequest('filesize is too large, maximum allowed filesize is %d' % (max_size,))

				b64buf = base64.b64encode(file_obj['body']).decode('ASCII')
				result.append({'filename': file_obj['filename'], 'name': name, 'content': b64buf})

		self.content_negotiation(result)


class Command(Resource):
	"""Gateway for command/upload requests to UMC module processes"""

	def error_handling(self, etype, exc, etraceback):
		super(Command, self).error_handling(etype, exc, etraceback)
		# make sure that the UMC login dialog is shown if e.g. restarting the UMC-Server during active sessions
		if isinstance(exc, UMC_Error) and exc.status == 403:
			exc.status = 401

	@tornado.gen.coroutine
	def get(self, umcp_command, command):
		"""Handles a COMMAND request. The request must contain a valid
		and known command that can be accessed by the current user. If
		access to the command is prohibited the request is answered as a
		forbidden command.

		If there is no running module process for the given command a
		new one is started and the request is added to a queue of
		requests that will be passed on when the process is ready.

		If a module process is already running the request is passed on
		and the inactivity timer is reset.
		"""
		session = self.current_user
		acls = session.acls

		# module_name = acls.get_module_providing(moduleManager, command)  # TODO: remove
		module_name = acls.get_module_providing(moduleManager, command)
		if not module_name:
			CORE.warn('No module provides %s' % (command))
			raise Forbidden()

		CORE.info('Checking ACLs for %s (%s)' % (command, module_name))
		if not acls.is_command_allowed(self.request, command):
			CORE.warn('Command %s is not allowed' % (command))
			raise Forbidden()

		methodname = acls.get_method_name(moduleManager, module_name, command)
		if not methodname:
			CORE.warn('Command %s does not exists' % (command))
			raise Forbidden()

		headers = self.get_request_header(session, methodname, umcp_command)

		locale = str(Locale(self.locale.code))
		process = session.processes.get_process(module_name, locale)
		CORE.info('Passing request to module %s' % (module_name,))

		try:
			yield process.connect()
			# send first command
			response = yield process.request(self.request.method, self.request.full_url(), body=self.request.body or None, headers=headers)
		except CouldNotConnect as exc:
			# (happens during starting the service and subprocesses when the UNIX sockets aren't available yet)
			# cleanup module
			session.processes.stop_process(module_name)
			# TODO: read stderr
			raise BadGateway('%s: %s: %s' % (self._('Connection to module process failed'), module_name, exc))
		else:
			CORE.process('Recevied response %s' % (response.code,))
			self.set_status(response.code, response.reason)
			self._headers = tornado.httputil.HTTPHeaders()

			for header, v in response.headers.get_all():
				if header.title() not in ('Content-Length', 'Transfer-Encoding', 'Content-Encoding', 'Connection', 'X-Http-Reason', 'Range', 'Trailer', 'Server', 'Set-Cookie'):
					self.add_header(header, v)

			if response.code >= 400 and response.headers.get('Content-Type', '').startswith('application/json'):
				body = json.loads(response.body)
				message = json.loads(response.headers.get('X-UMC-Message', 'null'))
				exc = UMC_HTTPError(response.code, message=message, body=body.get('result'), error=body.get('error'), reason=response.reason)
				self.write_error(response.code, (UMC_HTTPError, exc, None))
				return

			if response.body:
				self.set_header('Content-Length', str(len(response.body)))
				self.write(response.body)
			self.finish()

	def get_request_header(self, session, methodname, umcp_command):
		headers = dict(self.request.headers)
		for header in ('Content-Length', 'Transfer-Encoding', 'Content-Encoding', 'Connection', 'X-Http-Reason', 'Range', 'Trailer', 'Server', 'Set-Cookie'):
			headers.pop(header, None)
		headers['Cookie'] = '; '.join([m.OutputString(attrs=[]) for name, m in self.cookies.items() if not name.startswith('UMCUsername')])
		headers['X-User-Dn'] = json.dumps(session.user.user_dn)
		#headers['X-UMC-Flavor'] = None
		# Forwarded=self.get_ip_address() ?
		headers['Authorization'] = 'basic ' + base64.b64encode(('%s:%s' % (session.user.username, session.get_umc_password())).encode('ISO8859-1')).decode('ASCII')
		headers['X-UMC-Method'] = methodname
		headers['X-UMC-Command'] = umcp_command.upper()
		auth_type = session.get_umc_auth_type()
		if auth_type:
			headers['X-UMC-AuthType'] = auth_type
		return headers

	@tornado.web.asynchronous
	def post(self, *args):
		return self.get(*args)

	@tornado.web.asynchronous
	def put(self, *args):
		return self.get(*args)

	@tornado.web.asynchronous
	def delete(self, *args):
		return self.get(*args)

	@tornado.web.asynchronous
	def patch(self, *args):
		return self.get(*args)

	@tornado.web.asynchronous
	def options(self, *args):
		return self.get(*args)


class UCR(Resource):
	"""Get UCR Variables matching a pattern"""

	@sanitize(StringSanitizer(required=True))
	def get(self):
		ucr.load()
		result = {}
		for value in self.request.body_arguments:
			if value.endswith('*'):
				value = value[:-1]
				result.update(dict((x, ucr.get(x)) for x in ucr.keys() if x.startswith(value)))
			else:
				result[value] = ucr.get(value)
		self.content_negotiation(result)

	def post(self):
		return self.get()


class Meta(Resource):
	"""Get Metainformation about the environment"""

	META_JSON_PATH = '/var/www/univention/meta.json'

	META_UCR_VARS = [
		'domainname',
		'hostname',
		'ldap/master',
		'license/base',
		'server/role',
		'ssl/validity/host',
		'ssl/validity/root',
		'ssl/validity/warning',
		'umc/web/favorites/default',
		'umc/web/piwik',
		'update/available',
		'update/reboot/required',
		'uuid/license',
		'uuid/system',
		'version/erratalevel',
		'version/patchlevel',
		'version/releasename',
		'version/version',
	]

	@allow_unauthorized
	def get(self):
		def _get_ucs_version():
			try:
				return '{version/version}-{version/patchlevel} errata{version/erratalevel}'.format(**ucr)
			except KeyError:
				pass

		def _has_system_uuid():
			fake_uuid = '00000000-0000-0000-0000-000000000000'
			return ucr.get('uuid/system', fake_uuid) != fake_uuid

		def _has_free_license():
			return ucr.get('license/base') in ('UCS Core Edition', 'Free for personal use edition')

		try:
			with open(self.META_JSON_PATH) as fd:
				meta_data = json.load(fd)
		except (EnvironmentError, ValueError) as exc:
			CORE.error('meta.json is not available: %s' % (exc,))
			meta_data = {}

		if not self.current_user.authenticated:
			self.content_negotiation(meta_data)
			return

		ucr.load()
		meta_data.update(dict(
			ucsVersion=_get_ucs_version(),
			ucs_version=_get_ucs_version(),
			has_system_uuid=_has_system_uuid(),
			has_free_license=_has_free_license(),
			hasFreeLicense=_has_free_license(),
			has_license_base=bool(ucr.get('license/base')),
			appliance_name=ucr.get('umc/web/appliance/name'),
		))
		meta_data.update([(i, ucr.get(i)) for i in self.META_UCR_VARS])
		self.content_negotiation(meta_data)


class Info(Resource):
	"""Get UCS and UMC version number and SSL validity

		.. deprecated:: 5.0
			if needed fetch UCR variables directly

		TODO: move into meta?
	"""

	CHANGELOG_VERSION = re.compile(r'^[^(]*\(([^)]*)\).*')

	def get_umc_version(self):
		try:
			with gzip.open('/usr/share/doc/univention-management-console-server/changelog.Debian.gz') as fd:
				line = fd.readline().decode('utf-8', 'replace')
		except IOError:
			return
		try:
			return self.CHANGELOG_VERSION.match(line).groups()[0]
		except AttributeError:
			return

	def get_ucs_version(self):
		return '{0}-{1} errata{2} ({3})'.format(ucr.get('version/version', ''), ucr.get('version/patchlevel', ''), ucr.get('version/erratalevel', '0'), ucr.get('version/releasename', ''))

	def get(self):
		ucr.load()

		result = {
			'umc_version': self.get_umc_version(),
			'ucs_version': self.get_ucs_version(),
			'server': '{0}.{1}'.format(ucr.get('hostname', ''), ucr.get('domainname', '')),
			'ssl_validity_host': int(ucr.get('ssl/validity/host', '0')) * 24 * 60 * 60 * 1000,
			'ssl_validity_root': int(ucr.get('ssl/validity/root', '0')) * 24 * 60 * 60 * 1000,
		}
		self.content_negotiation(result)


class Hosts(Resource):
	"""List all directory nodes in the domain"""

	def get(self):
		self.content_negotiation(self.get_hosts())

	def get_hosts(self):
		lo = self.lo
		if not lo:  # unjoined / no LDAP connection
			return []
		try:
			domaincontrollers = lo.search(filter="(objectClass=univentionDomainController)", attr=['cn', 'associatedDomain'])
		except (ldap.LDAPError, udm_errors.base) as exc:
			reset_ldap_connection_cache(lo)
			CORE.warn('Could not search for domaincontrollers: %s' % (exc))
			return []

		return sorted(
			b'.'.join((computer['cn'][0], computer['associatedDomain'][0])).decode('utf-8', 'replace')
			for dn, computer in domaincontrollers
			if computer.get('associatedDomain')
		)


class Set(Resource):
	"""Generic set

	..deprecated:: 5.0
		use the specific set paths
	"""

	@tornado.gen.coroutine
	def post(self):
		is_univention_lib = self.request.headers.get('User-Agent', '').startswith('UCS/')
		for key in self.request.body_arguments:
			cls = {'password': SetPassword, 'user': SetUserPreferences, 'locale': SetLocale}.get(key)
			if is_univention_lib and cls:
				# for backwards compatibility with non redirecting clients we cannot redirect here :-(
				p = cls(self.application, self.request)
				p._ = self._
				p.finish = self.finish
				yield p.post()
				return
			if key == 'password':
				self.redirect('/univention/set/password', status=307)
			elif key == 'user':
				self.redirect('/univention/set/user/preferences', status=307)
			elif key == 'locale':
				self.redirect('/univention/set/locale', status=307)
		#raise NotFound()
		raise HTTPError(404)


class SetPassword(Resource):
	"""Change the password of the currently authenticated user"""

	@sanitize(password=DictSanitizer(dict(
		password=StringSanitizer(required=True),
		new_password=StringSanitizer(required=True),
	)))
	@tornado.gen.coroutine
	def post(self):
		from .server import pool
		username = self.current_user.user.username
		password = self.request.body_arguments['password']['password']
		new_password = self.request.body_arguments['password']['new_password']

		CORE.info('Changing password of user %r' % (username,))
		pam = PamAuth(str(self.locale.code))
		try:
			yield pool.submit(pam.change_password, username, password, new_password)
		except PasswordChangeFailed as exc:
			raise UMC_HTTPError(400, str(exc), {'new_password': '%s' % (exc,)})  # 422
		else:
			CORE.info('Successfully changed password')
			self.set_header('X-UMC-Message', json.dumps(self._('Password successfully changed.')))
			self.content_negotiation(None)

			# FIXME:
			self.auth_type = None
			self._password = new_password
			self.current_user.processes.update_module_passwords()


class UserPreferences(Resource):
	"""get user specific preferences like favorites"""

	def get(self):
		# fallback is an empty dict
		lo = self.current_user.user.get_user_ldap_connection()
		result = {'preferences': self._get_user_preferences(lo)}
		self.content_negotiation(result)

	def post(self):
		return self.get()

	def _get_user_preferences(self, lo):
		user_dn = self.current_user.user.user_dn
		if not user_dn or not lo:
			return {}
		try:
			preferences = lo.get(user_dn, ['univentionUMCProperty']).get('univentionUMCProperty', [])
		except (ldap.LDAPError, udm_errors.base) as exc:
			CORE.warn('Failed to retrieve user preferences: %s' % (exc,))
			return {}
		preferences = (val.decode('utf-8', 'replace') for val in preferences)
		return dict(val.split(u'=', 1) if u'=' in val else (val, u'') for val in preferences)


class SetUserPreferences(UserPreferences):
	"""set user specific preferences like favorites"""

	def get(self):
		return self.post()

	@sanitize(user=DictSanitizer(dict(
		preferences=DictSanitizer(dict(), required=True),
	)))
	def post(self):
		lo = self.current_user.user.get_user_ldap_connection()
		# eliminate double entries
		preferences = self._get_user_preferences(lo)
		preferences.update(dict(self.request.body_arguments['user']['preferences']))
		if preferences:
			self._set_user_preferences(lo, preferences)
		self.content_negotiation(None)

	def _set_user_preferences(self, lo, preferences):
		user_dn = self.current_user.user.user_dn
		if not user_dn or not lo:
			return

		user = lo.get(user_dn, ['univentionUMCProperty', 'objectClass'])
		old_preferences = user.get('univentionUMCProperty')
		object_classes = list(set(user.get('objectClass', [])) | set([b'univentionPerson']))

		# validity / sanitizing
		new_preferences = []
		for key, value in preferences.items():
			if not isinstance(key, six.string_types):
				CORE.warn('user preferences keys needs to be strings: %r' % (key,))
				continue

			# we can put strings directly into the dict
			if isinstance(value, six.string_types):
				new_preferences.append((key, value))
			else:
				new_preferences.append((key, json.dumps(value)))
		new_preferences = [b'%s=%s' % (key.encode('utf-8'), value.encode('utf-8')) for key, value in new_preferences]

		lo.modify(user_dn, [['univentionUMCProperty', old_preferences, new_preferences], ['objectClass', user.get('objectClass', []), object_classes]])
