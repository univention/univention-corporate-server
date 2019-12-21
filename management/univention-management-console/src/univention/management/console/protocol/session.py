#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  session handling
#
# Copyright 2006-2019 Univention GmbH
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
import ldap
import os
import time
import json
import traceback
import gzip
import re
import errno

import ldap.filter

import notifier
import notifier.popen as popen
from notifier import threads

import univention.admin.uexceptions as udm_errors

from .message import Response, Request, MIMETYPE_JSON
from .client import Client, NoSocketError
from .version import VERSION
from .definitions import status_description, SERVER_ERR_MODULE_FAILED, SERVER_ERR_MODULE_DIED

from ..resources import moduleManager, categoryManager
from ..auth import AuthHandler
from ..pam import PamAuth, PasswordChangeFailed
from ..acl import LDAP_ACLs, ACLs
from ..log import CORE
from ..config import MODULE_INACTIVITY_TIMER, MODULE_DEBUG_LEVEL, MODULE_COMMAND, ucr
from ..locales import I18N, I18N_Manager
from ..base import Base
from ..error import UMC_Error, Unauthorized, BadRequest, NotFound, Forbidden, ServiceUnavailable
from ..ldap import get_machine_connection, reset_cache
from ..modules.sanitizers import StringSanitizer, DictSanitizer
from ..modules.decorators import sanitize, sanitize_args, simple_response, allow_get_request

TEMPUPLOADDIR = '/var/tmp/univention-management-console-frontend'


class ModuleProcess(Client):

	"""handles the communication with a UMC module process

	:param str module: name of the module to start
	:param str debug: debug level as a string
	:param str locale: locale to use for the module process
	"""

	def __init__(self, module, debug='0', locale=None):
		socket = '/var/run/univention-management-console/%u-%lu.socket' % (os.getpid(), long(time.time() * 1000))
		# determine locale settings
		modxmllist = moduleManager[module]
		args = [MODULE_COMMAND, '-m', module, '-s', socket, '-d', str(debug)]
		for modxml in modxmllist:
			if modxml.notifier:
				args.extend(['-n', modxml.notifier])
				break
		if locale:
			args.extend(('-l', '%s' % locale))
			self.__locale = locale
		else:
			self.__locale = None
		Client.__init__(self, unix=socket, ssl=False)
		self.signal_connect('response', self._response)
		CORE.process('running: %s' % args)
		self.__process = popen.RunIt(args, stdout=False)
		self.__process.signal_connect('killed', self._died)
		self.__pid = self.__process.start()
		self._connect_retries = 1
		self.signal_new('result')
		self.signal_new('finished')
		self.name = module
		self.running = False
		self._queued_requests = []
		self._inactivity_timer = None
		self._inactivity_counter = 0

	def __del__(self):
		CORE.process('ModuleProcess: dying')
		if self.__process:
			self.disconnect()
			self.__process.signal_disconnect('killed', self._died)
			self.__process.stop()
			self.__process = None
			CORE.process('ModuleProcess: child stopped')

	def _died(self, pid, status):
		CORE.process('ModuleProcess: child died')
		self.signal_emit('finished', pid, status)

	def _response(self, msg):
		# these responses must not be send to the external client as
		# this commands were generated within the server
		if msg.command == 'EXIT' and 'internal' in msg.arguments:
			return

		self.signal_emit('result', msg)

	def pid(self):
		"""Returns process ID of module process"""
		return self.__pid


class ProcessorBase(Base):

	"""Implements a proxy and command handler. It handles all internal
	UMCP commands and passes the commands for a module to the
	subprocess.

	:param str username: name of the user who authenticated for this session
	:param str password: password of the user
	"""

	@property
	def lo(self):
		return get_machine_connection(write=False)[0]

	def __init__(self):
		Base.__init__(self, 'univention-management-console')
		self.__processes = {}
		self.__killtimer = {}
		self.__command_list = None
		self.i18n = I18N_Manager()
		self.i18n['umc-core'] = I18N()

	def set_locale(self, locale):
		# don't call the super method because it sets the process locale LC_*!
		self.set_language(locale)
		self.i18n.set_locale(locale)

	def set_credentials(self, username, password, auth_type):
		self.username = username
		self._password = password
		self.auth_type = auth_type
		self._search_user_dn()
		self._reload_acls_and_permitted_commands()
		self.update_module_passwords()

	def _reload_acls_and_permitted_commands(self):
		self._reload_acls()
		self.__command_list = moduleManager.permitted_commands(ucr['hostname'], self.acls)

	def _reload_acls(self):
		try:
			self.acls = LDAP_ACLs(self.lo, self._username, ucr['ldap/base'])
		except (ldap.LDAPError, udm_errors.ldapError):
			reset_cache()
			raise

	def _reload_i18n(self):
		self.i18n.set_locale(str(self.i18n.locale))

	def _search_user_dn(self):
		if self.lo and self._username:
			# get the LDAP DN of the authorized user
			try:
				ldap_dn = self.lo.searchDn(ldap.filter.filter_format('(&(uid=%s)(objectClass=person))', (self._username,)))
			except (ldap.LDAPError, udm_errors.base):
				reset_cache()
				ldap_dn = None
				CORE.error('Could not get uid for %r: %s' % (self._username, traceback.format_exc()))
			if ldap_dn:
				self._user_dn = ldap_dn[0]
				CORE.info('The LDAP DN for user %s is %s' % (self._username, self._user_dn))

		if not self._user_dn and self._username not in ('root', '__systemsetup__', None):
			CORE.error('The LDAP DN for user %s could not be found (lo=%r)' % (self._username, self.lo))

	def error_handling(self, etype, exc, etraceback):
		super(ProcessorBase, self).error_handling(etype, exc, etraceback)
		if isinstance(exc, UMC_Error) and exc.msg is None:
			exc.args = (status_description(exc.status),)

	def request(self, msg):
		"""Handles an incoming UMCP request and passes the requests to
		specific handler functions.

		:param Request msg: UMCP request
		"""
		if msg.command in ('AUTH', 'EXIT', 'GET', 'SET', 'VERSION', 'COMMAND', 'UPLOAD'):
			method = 'handle_request_%s' % (msg.command.lower(),)
		else:
			method = 'handle_request_unknown'

		self.execute(method, msg)

	@allow_get_request
	def handle_request_unknown(self, msg):
		"""Handles an unknown or invalid request"""
		raise NotFound()

	@allow_get_request
	def handle_request_unauthorized(self, msg):
		raise Unauthorized(self._('For using this request a login is required.'))

	@allow_get_request
	def handle_request_auth(self, request):
		result = request.authentication_result
		del request.authentication_result
		response = Response(request)
		response.status = result.status
		if result.message:
			response.message = result.message
		response.result = result.result
		self.finished(request.id, response)

	handle_request_get_ucr = handle_request_unauthorized
	handle_request_get_info = handle_request_unauthorized
	handle_request_get_user_preferences = handle_request_unauthorized
	handle_request_get_hosts = handle_request_unauthorized
	handle_request_set_password = handle_request_unauthorized
	handle_request_set_locale = handle_request_unauthorized
	handle_request_set_user = handle_request_unauthorized
	handle_request_version = handle_request_unauthorized

	@allow_get_request
	def handle_request_get(self, msg):
		"""Handles a GET request"""

		for arg in msg.arguments:
			method = {
				'ucr': self.handle_request_get_ucr,
				'meta': self.handle_request_get_meta,
				'info': self.handle_request_get_info,
				'modules/list': self.handle_request_get_modules,
				'modules': self.handle_request_get_modules,
				'categories/list': self.handle_request_get_categories,
				'categories': self.handle_request_get_categories,
				'user/preferences': self.handle_request_get_user_preferences,
				'hosts/list': self.handle_request_get_hosts,
				'hosts': self.handle_request_get_hosts,
			}.get(arg)
			if method:
				self.finished(msg.id, method(msg))
				return
		raise NotFound()

	META_JSON_PATH = '/usr/share/univention-management-console/meta.json'

	def handle_request_get_meta(self, request):
		try:
			with open(self.META_JSON_PATH) as fd:
				return json.load(fd)
		except (EnvironmentError, ValueError) as exc:
			CORE.error('meta.json is not available: %s' % (exc,))
			return {}

	def handle_request_set(self, msg):
		for key, value in msg.options.items():
			method = {
				'password': self.handle_request_set_password,
				'locale': self.handle_request_set_locale,
				'user': self.handle_request_set_user,
			}.get(key)
			if method:
				return method(msg)
		raise NotFound()

	def handle_request_get_modules(self, request):
		categoryManager.load()
		moduleManager.load()
		if isinstance(request.options, dict) and request.options.get('reload'):
			CORE.info('Reloading ACLs for existing session')
			self._reload_acls_and_permitted_commands()
			self._reload_i18n()

		favorites = self._get_user_favorites()
		modules = []
		for id, module in self.__command_list.items():
			# check for translation
			if module.flavors:
				for flavor in module.flavors:
					favcat = []
					if '%s:%s' % (id, flavor.id) in favorites:
						favcat.append('_favorites_')

					translationId = flavor.translationId
					if not translationId:
						translationId = id
					modules.append({
						'id': id,
						'flavor': flavor.id,
						'name': self.i18n._(flavor.name, translationId),
						'url': self.i18n._(module.url, translationId),
						'description': self.i18n._(flavor.description, translationId),
						'icon': flavor.icon,
						'categories': (flavor.categories or (module.categories if not flavor.hidden else [])) + favcat,
						'priority': flavor.priority,
						'keywords': list(set(flavor.keywords + [self.i18n._(keyword, translationId) for keyword in flavor.keywords])),
						'version': flavor.version,
					})
			else:
				favcat = []
				if id in favorites:
					favcat.append('_favorites_')
				translationId = module.translationId
				if not translationId:
					translationId = id
				modules.append({
					'id': id,
					'name': self.i18n._(module.name, translationId),
					'url': self.i18n._(module.url, translationId),
					'description': self.i18n._(module.description, translationId),
					'icon': module.icon,
					'categories': module.categories + favcat,
					'priority': module.priority,
					'keywords': list(set(module.keywords + [self.i18n._(keyword, translationId) for keyword in module.keywords])),
					'version': module.version,
				})
		CORE.info('Modules: %s' % (modules,))
		res = Response(request)
		res.body['modules'] = modules
		return res

	def _get_user_favorites(self):
		if not self._user_dn:  # user not authenticated or no LDAP user
			return set(ucr.get('umc/web/favorites/default', '').split(','))
		favorites = self._get_user_preferences(self.get_user_ldap_connection()).setdefault('favorites', ucr.get('umc/web/favorites/default', '')).strip()
		return set(favorites.split(','))

	def handle_request_get_categories(self, request):
		categoryManager.load()
		ucr.load()
		_ucr_dict = dict(ucr.items())
		categories = []
		for catID, category in categoryManager.items():
			categories.append({
				'id': catID,
				'icon': category.icon,
				'color': category.color,
				'name': self.i18n._(category.name, category.domain).format(**_ucr_dict),
				'priority': category.priority
			})
		CORE.info('Categories: %s' % (categories,))
		res = Response(request)
		res.body['categories'] = categories
		return res

	@sanitize(locale=StringSanitizer(required=True))
	@simple_response
	def handle_request_set_locale(self, locale):
		self.update_language([locale])

	def update_module_passwords(self):
		CORE.process('Updating user password in %d running module processes (auth-type: %s).' % (len(self.__processes), self.auth_type))
		for module_name, proc in self.__processes.items():
			CORE.info('Update the users password in the running %r module instance.' % (module_name,))
			req = Request('SET', arguments=[module_name], options={'password': self._password, 'auth_type': self.auth_type})
			try:
				proc.request(req)
			except:
				CORE.error(traceback.format_exc())

	@allow_get_request
	@sanitize(DictSanitizer(dict(
		tmpfile=StringSanitizer(required=True),
		filename=StringSanitizer(required=True),
		name=StringSanitizer(required=True),
	)))
	def handle_request_upload(self, msg):
		"""Handles an UPLOAD request. The command is used for the HTTP
		access to the UMC server. Incoming HTTP requests that send a
		list of files are passed on to the UMC server by storing the
		files in temporary files and passing the information about the
		files to the UMC server in the options of the request. The
		request options must be a list of dictionaries. Each dictionary
		must contain the following keys:

		* *filename* -- the original name of the file
		* *name* -- name of the form field
		* *tmpfile* -- filename of the temporary file

		:param Request msg: UMCP request
		"""

		direct_response = not msg.arguments or msg.arguments[0] in ('', '/')
		result = []
		for file_obj in msg.options:
			tmpfilename, filename, name = file_obj['tmpfile'], file_obj['filename'], file_obj['name']

			# limit files to tmpdir
			if not os.path.realpath(tmpfilename).startswith(TEMPUPLOADDIR):
				raise BadRequest('invalid file: invalid path')

			# check if file exists
			if not os.path.isfile(tmpfilename):
				raise BadRequest('invalid file: file does not exists')

			# don't accept files bigger than umc/server/upload/max
			st = os.stat(tmpfilename)
			max_size = int(ucr.get('umc/server/upload/max', 64)) * 1024
			if st.st_size > max_size:
				os.remove(tmpfilename)
				raise BadRequest('filesize is too large, maximum allowed filesize is %d' % (max_size,))

			if direct_response:
				with open(tmpfilename) as buf:
					b64buf = base64.b64encode(buf.read())
				result.append({'filename': filename, 'name': name, 'content': b64buf})

		if direct_response:
			self.finished(msg.id, result)
		else:
			self.handle_request_command(msg)

	@allow_get_request
	def handle_request_command(self, msg):
		"""Handles a COMMAND request. The request must contain a valid
		and known command that can be accessed by the current user. If
		access to the command is prohibited the request is answered as a
		forbidden command.

		If there is no running module process for the given command a
		new one is started and the request is added to a queue of
		requests that will be passed on when the process is ready.

		If a module process is already running the request is passed on
		and the inactivity timer is reset.

		:param Request msg: UMCP request
		"""

		# only one command?
		command = None
		if msg.arguments:
			command = msg.arguments[0]

		module_name = moduleManager.module_providing(self.__command_list, command)

		try:
			# check if the module exists in the module manager
			moduleManager[module_name]
		except KeyError:
			# the module has been removed from moduleManager (probably through a reload)
			CORE.warn('Module %r (command=%r, id=%r) does not exists anymore' % (module_name, command, msg.id))
			moduleManager.load()
			self._reload_acls_and_permitted_commands()
			module_name = None

		if not module_name:
			raise Forbidden()

		if msg.arguments:
			if msg.mimetype == MIMETYPE_JSON:
				is_allowed = moduleManager.is_command_allowed(self.acls, msg.arguments[0], options=msg.options, flavor=msg.flavor)
			else:
				is_allowed = moduleManager.is_command_allowed(self.acls, msg.arguments[0])
			if not is_allowed:
				raise Forbidden()
			if module_name not in self.__processes:
				CORE.info('Starting new module process and passing new request to module %s: %s' % (module_name, str(msg._id)))
				try:
					mod_proc = ModuleProcess(module_name, debug=MODULE_DEBUG_LEVEL, locale=self.i18n.locale)
				except EnvironmentError as exc:
					message = self._('Could not open the module. %s Please try again later.') % {
						errno.ENOMEM: self._('There is not enough memory available on the server.'),
						errno.EMFILE: self._('There are too many opened files on the server.'),
						errno.ENFILE: self._('There are too many opened files on the server.'),
						errno.ENOSPC: self._('There is not enough free space on the server.')
					}.get(exc.errno, self._('An unknown operating system error occurred (%s).' % (exc,)))
					raise ServiceUnavailable(message)
				mod_proc.signal_connect('result', self.result)

				cb = notifier.Callback(self._mod_error, module_name)
				mod_proc.signal_connect('error', cb)

				cb = notifier.Callback(self._socket_died, module_name)
				mod_proc.signal_connect('closed', cb)

				cb = notifier.Callback(self._mod_died, module_name)
				mod_proc.signal_connect('finished', cb)

				self.__processes[module_name] = mod_proc

				cb = notifier.Callback(self._mod_connect, mod_proc, msg)
				notifier.timer_add(50, cb)
			else:
				proc = self.__processes[module_name]
				if proc.running:
					CORE.info('Passing new request to running module %s' % module_name)
					proc.request(msg)
					self.reset_inactivity_timer(proc)
				else:
					CORE.info('Queuing incoming request for module %s that is not yet ready to receive' % module_name)
					proc._queued_requests.append(msg)

	def _mod_connect(self, mod, msg):
		"""Callback for a timer event: Trying to connect to newly started module process"""
		def _send_error():
			# inform client
			res = Response(msg)
			res.status = SERVER_ERR_MODULE_FAILED  # error connecting to module process
			res.message = '%s: %s' % (status_description(res.status), mod.name)
			self.result(res)
			# cleanup module
			mod.signal_disconnect('closed', notifier.Callback(self._socket_died))
			mod.signal_disconnect('result', notifier.Callback(self.result))
			mod.signal_disconnect('finished', notifier.Callback(self._mod_died))
			proc = self.__processes.pop(mod.name, None)
			if proc:
				proc.__del__()

		try:
			mod.connect()
		except NoSocketError:
			if mod._connect_retries > 200:
				CORE.info('Connection to module %s process failed' % mod.name)
				_send_error()
				return False
			if not mod._connect_retries % 50:
				CORE.info('No connection to module process yet')
			mod._connect_retries += 1
			return True
		except Exception as exc:
			CORE.error('Unknown error while trying to connect to module process: %s\n%s' % (exc, traceback.format_exc()))
			_send_error()
			return False
		else:
			CORE.info('Connected to new module process')
			mod.running = True

			# send acls, commands, credentials, locale
			options = {
				'acls': self.acls.json(),
				'commands': self.__command_list[mod.name].json(),
				'credentials': {
					'auth_type': self.auth_type,
					'username': self._username,
					'password': self._password,
					'user_dn': self._user_dn
				},
			}
			if str(self.i18n.locale):
				options['locale'] = str(self.i18n.locale)

			# WARNING! This debug message contains credentials!!!
			# CORE.info('Initialize module process: %s' % (options,))

			req = Request('SET', options=options)
			mod.request(req)

			# send first command
			mod.request(msg)

			# send queued request that were received during start procedure
			for req in mod._queued_requests:
				mod.request(req)
			mod._queued_requests = []

			# watch the module's activity and kill it after X seconds inactivity
			self.reset_inactivity_timer(mod)

		return False

	def _mod_inactive(self, module):
		CORE.info('The module %s is inactive for too long. Sending EXIT request to module' % module.name)
		if module.openRequests:
			CORE.info('There are unfinished requests. Waiting for %s' % ', '.join(module.openRequests))
			return True

		# mark as internal so the response will not be forwarded to the client
		req = Request('EXIT', arguments=[module.name, 'internal'])
		self.handle_request_exit(req)

		return False

	def _socket_died(self, module_name):
		CORE.warn('Socket died (module=%s)' % module_name)
		if module_name in self.__processes:
			self._mod_died(self.__processes[module_name].pid(), -1, module_name)

	def _mod_error(self, exc, module_name):
		CORE.error('Module %r ran into error: %s' % (module_name, exc))
		if module_name in self.__processes:
			self.__processes[module_name].invalidate_all_requests(status=exc.args[0], message=exc.args[1])
			self._mod_died(self.__processes[module_name].pid(), -1, module_name)
		self._purge_child(module_name)

	def _mod_died(self, pid, status, module_name):
		if status:
			if os.WIFSIGNALED(status):
				signal = os.WTERMSIG(status)
				exitcode = -1
			elif os.WIFEXITED(status):
				signal = -1
				exitcode = os.WEXITSTATUS(status)
			else:
				signal = -1
				exitcode = -1
			CORE.warn('Module process %s died (pid: %d, exit status: %d, signal: %d, status: %r)' % (module_name, pid, exitcode, signal, status))
		else:
			CORE.info('Module process %s died on purpose' % module_name)

		# if killtimer has been set then remove it
		CORE.info('Checking for kill timer (%s)' % ', '.join(self.__killtimer.keys()))
		if module_name in self.__killtimer:
			CORE.info('Stopping kill timer)')
			notifier.timer_remove(self.__killtimer[module_name])
			del self.__killtimer[module_name]
		if module_name in self.__processes:
			CORE.warn('Cleaning up requests')
			self.__processes[module_name].invalidate_all_requests(status=SERVER_ERR_MODULE_DIED)
			if self.__processes[module_name]._inactivity_timer is not None:
				CORE.warn('Remove inactivity timer')
				notifier.timer_remove(self.__processes[module_name]._inactivity_timer)
			del self.__processes[module_name]

	def reset_inactivity_timer(self, module):
		"""Resets the inactivity timer. This timer watches the
		inactivity of the module process. If the module did not receive
		a request for MODULE_INACTIVITY_TIMER seconds the module process
		is shut down to save resources. The timer ticks each seconds to
		handle glitches of the system clock.

		:param Module module: a module
		"""
		if module._inactivity_timer is None:
			module._inactivity_timer = notifier.timer_add(1000, notifier.Callback(self._inactivitiy_tick, module))

		module._inactivity_counter = MODULE_INACTIVITY_TIMER

	def _inactivitiy_tick(self, module):
		if module._inactivity_counter > 0:
			module._inactivity_counter -= 1000
			return True
		if self._mod_inactive(module):  # open requests -> waiting
			module._inactivity_counter = MODULE_INACTIVITY_TIMER
			return True

		module._inactivity_timer = None
		module._inactivity_counter = 0

		return False

	def handle_request_exit(self, msg):
		"""Handles an EXIT request. If the request does not have an
		argument that contains a valid name of a running UMC module
		instance the request is returned as a bad request.

		If the request is valid it is passed on to the module
		process. Additionally a timer of 3000 milliseconds is
		started. After that amount of time the module process MUST have
		been exited itself. If not the UMC server will kill the module
		process.

		:param Request msg: UMCP request
		"""
		if len(msg.arguments) < 1:
			return self.handle_request_unknown(msg)

		module_name = msg.arguments[0]
		if module_name:
			if module_name in self.__processes:
				self.__processes[module_name].request(msg)
				CORE.info('Ask module %s to shutdown gracefully' % module_name)
				# added timer to kill away module after 3000ms
				cb = notifier.Callback(self._purge_child, module_name)
				self.__killtimer[module_name] = notifier.timer_add(3000, cb)
			else:
				CORE.info('Got EXIT request for a non-existing module %s' % module_name)

	def _purge_child(self, module_name):
		if module_name in self.__processes:
			CORE.process('module %s is still running - purging module out of memory' % module_name)
			pid = self.__processes[module_name].pid()
			try:
				os.kill(pid, 9)
			except OSError as exc:
				CORE.warn('Failed to kill module %s: %s' % (module_name, exc))
		return False

	def shutdown(self):
		"""Instructs the module process to shutdown"""
		CORE.info('The session is shutting down. Sending UMC modules an EXIT request (%d processes)' % len(self.__processes))
		for module_name, process in self.__processes.items():
			CORE.info('Ask module %s to shutdown gracefully' % (module_name,))
			req = Request('EXIT', arguments=[module_name, 'internal'])
			process.request(req)

	def __del__(self):
		CORE.process('Processor: dying')
		for process in self.__processes.keys():
			self.__processes.pop(process).__del__()


class Processor(ProcessorBase):

	@sanitize(StringSanitizer(required=True))
	def handle_request_get_ucr(self, request):
		ucr.load()
		result = {}
		for value in request.options:
			if value.endswith('*'):
				value = value[:-1]
				result.update(dict((x, ucr.get(x)) for x in ucr.keys() if x.startswith(value)))
			else:
				result[value] = ucr.get(value)
		return result

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

	def handle_request_get_meta(self, request):
		def _get_ucs_version():
			try:
				return '{version/version}-{version/patchlevel} errata{version/erratalevel} ({version/releasename})'.format(**ucr)
			except KeyError:
				pass

		def _has_system_uuid():
			fake_uuid = '00000000-0000-0000-0000-000000000000'
			return ucr.get('uuid/system', fake_uuid) != fake_uuid

		def _has_free_license():
			return ucr.get('license/base') in ('UCS Core Edition', 'Free for personal use edition')

		meta_data = super(Processor, self).handle_request_get_meta(request)

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
		return meta_data

	CHANGELOG_VERSION = re.compile('^[^(]*\(([^)]*)\).*')

	def handle_request_get_info(self, request):
		ucr.load()
		result = {}
		try:
			with gzip.open('/usr/share/doc/univention-management-console-server/changelog.Debian.gz') as fd:
				line = fd.readline()
			match = self.CHANGELOG_VERSION.match(line)
			if not match:
				raise IOError
			result['umc_version'] = match.groups()[0]
			result['ucs_version'] = '{0}-{1} errata{2} ({3})'.format(ucr.get('version/version', ''), ucr.get('version/patchlevel', ''), ucr.get('version/erratalevel', '0'), ucr.get('version/releasename', ''))
			result['server'] = '{0}.{1}'.format(ucr.get('hostname', ''), ucr.get('domainname', ''))
			result['ssl_validity_host'] = int(ucr.get('ssl/validity/host', '0')) * 24 * 60 * 60 * 1000
			result['ssl_validity_root'] = int(ucr.get('ssl/validity/root', '0')) * 24 * 60 * 60 * 1000
		except IOError:
			raise Forbidden()
		return result

	def handle_request_get_hosts(self, request):
		result = []
		if self.lo:
			try:
				domaincontrollers = self.lo.search(filter="(objectClass=univentionDomainController)", attr=['cn', 'associatedDomain'])
			except (ldap.LDAPError, udm_errors.base) as exc:
				reset_cache()
				CORE.warn('Could not search for domaincontrollers: %s' % (exc))
				domaincontrollers = []
			result = sorted(['%s.%s' % (computer['cn'][0], computer['associatedDomain'][0]) for dn, computer in domaincontrollers if computer.get('associatedDomain')])
		return result

	@sanitize(password=DictSanitizer(dict(
		password=StringSanitizer(required=True),
		new_password=StringSanitizer(required=True),
	)))
	def handle_request_set_password(self, request):
		username = self._username
		password = request.options['password']['password']
		new_password = request.options['password']['new_password']

		CORE.info('Changing password of user %r' % (username,))
		pam = PamAuth(str(self.i18n.locale))
		change_password = notifier.Callback(pam.change_password, username, password, new_password)
		password_changed = notifier.Callback(self._password_changed, request, new_password)
		thread = threads.Simple('change_password', change_password, password_changed)
		thread.run()

	def _password_changed(self, thread, result, request, new_password):
		# it is important that this thread callback must not raise an exception. Otherwise the UMC-Server crashes.
		if isinstance(result, PasswordChangeFailed):
			self.finished(request.id, {'new_password': '%s' % (result,)}, message=str(result), status=400)  # 422
		elif isinstance(result, BaseException):
			self.thread_finished_callback(thread, result, request)
		else:
			CORE.info('Successfully changed password')
			self.finished(request.id, None, message=self._('Password successfully changed.'))
			self.auth_type = None
			self._password = new_password
			self.update_module_passwords()

	def handle_request_get_user_preferences(self, request):
		# fallback is an empty dict
		res = Response(request)
		res.body['preferences'] = self._get_user_preferences(self.get_user_ldap_connection())
		return res

	@sanitize(user=DictSanitizer(dict(
		preferences=DictSanitizer(dict(), required=True),
	)))
	@simple_response
	def handle_request_set_user(self, user):
		lo = self.get_user_ldap_connection()
		# eliminate double entries
		preferences = self._get_user_preferences(lo)
		preferences.update(dict(user['preferences']))
		if preferences:
			self._set_user_preferences(lo, preferences)

	def _get_user_preferences(self, lo):
		if not self._user_dn or not lo:
			return {}
		try:
			preferences = lo.get(self._user_dn, ['univentionUMCProperty']).get('univentionUMCProperty', [])
		except (ldap.LDAPError, udm_errors.base) as exc:
			CORE.warn('Failed to retrieve user preferences: %s' % (exc,))
			return {}
		return dict(val.split('=', 1) if '=' in val else (val, '') for val in preferences)

	def _set_user_preferences(self, lo, preferences):
		if not self._user_dn or not lo:
			return

		user = lo.get(self._user_dn, ['univentionUMCProperty', 'objectClass'])
		old_preferences = user.get('univentionUMCProperty')
		object_classes = list(set(user.get('objectClass', [])) | set(['univentionPerson']))

		# validity / sanitizing
		new_preferences = []
		for key, value in preferences.iteritems():
			if not isinstance(key, basestring):
				CORE.warn('user preferences keys needs to be strings: %r' % (key,))
				continue

			# we can put strings directly into the dict
			if isinstance(value, basestring):
				new_preferences.append((key, value))
			else:
				new_preferences.append((key, json.dumps(value)))
		new_preferences = ['%s=%s' % (key, value) for key, value in new_preferences]

		lo.modify(self._user_dn, [['univentionUMCProperty', old_preferences, new_preferences], ['objectClass', user.get('objectClass', []), object_classes]])

	def handle_request_version(self, msg):
		"""Handles a VERSION request by returning the version of the UMC
		server's protocol version.

		:param Request msg: UMCP request
		"""
		res = Response(msg)
		res.body['version'] = VERSION
		self.finished(msg.id, res)


class SessionHandler(ProcessorBase):

	def __init__(self):
		super(SessionHandler, self).__init__()
		self.__auth = AuthHandler()
		self.__auth.signal_connect('authenticated', self._authentication_finished)

		self.processor = None
		self.authenticated = False
		self.__credentials = None
		self.__locale = None
		self._reload_acls_and_permitted_commands()

	def has_active_module_processes(self):
		if self.processor:
			return self.processor._ProcessorBase__processes

	def _reload_acls(self):
		"""All unauthenticated requests are passed here. We need to set empty ACL's"""
		self.acls = ACLs()

	def error_handling(self, etype, exc, etraceback):
		super(SessionHandler, self).error_handling(etype, exc, etraceback)
		# make sure that the UMC login dialog is shown if e.g. restarting the UMC-Server during active sessions
		if isinstance(exc, UMC_Error) and exc.status == 403:
			exc.status = 401

	def shutdown(self):
		if self.processor is not None:
			self.processor.shutdown()

	def __del__(self):
		CORE.info('The session is shutting down')
		if self.processor:
			self.processor.__del__()
		self.processor = None

	def _authentication_finished(self, result, request):
		# caution! this is not executed in the main loop and any exception will therefore crash the server!
		self.execute('_authentication_finished2', request, result)

	@allow_get_request
	def _authentication_finished2(self, request, result):
		self.authenticated = bool(result)
		request.authentication_result = result
		if self.authenticated:
			if self.processor is None or self.processor.auth_type is not None or result.credentials['auth_type'] is None:
				# only set the credentials in 1. a new session 2. if password changed or 3. if logged in via plain authentication
				# to prevent a downgrade of the regular login to a SAML login
				self.__credentials = result.credentials
			if self.processor:
				# set the (new) password (also on re-authentication in the same session)
				self.processor.set_credentials(**self.__credentials)
			else:
				self.initalize_processor(request)
			self.processor.request(request)
		else:
			self.request(request)

	@allow_get_request
	def handle(self, request):
		"""Ensures that commands are only passed to the processor if a
			successful authentication has been completed."""
		CORE.info('Incoming request of type %s' % (request.command,))
		if not self.authenticated and request.command != 'AUTH':
			self.request(request)
		elif request.command == 'AUTH':
			self._handle_auth(request)
		elif request.command == 'GET' and 'newsession' in request.arguments:
			CORE.info('Renewing session')
			if self.processor:
				self.__locale = str(self.processor.locale)
			self.processor = None
			self.finished(request.id, None)
		else:
			self.initalize_processor(request)
			self.processor.request(request)

	def _handle_auth(self, request):
		request.body = sanitize_args(DictSanitizer(dict(
			username=StringSanitizer(required=True),
			password=StringSanitizer(required=True),
			auth_type=StringSanitizer(allow_none=True),
			new_password=StringSanitizer(required=False, allow_none=True),
		)), 'request', {'request': request.body})
		from univention.management.console.protocol.server import Server
		Server.reload()
		request.body['locale'] = str(self.i18n.locale)
		self.__auth.authenticate(request)

	def initalize_processor(self, request):
		if not self.processor:
			self.processor = Processor()
			self.processor.signal_connect('success', self._response)
			if self.__locale:
				self.processor.update_language([self.__locale])
			self.processor.set_credentials(**self.__credentials)

	def _response(self, response):
		self.signal_emit('success', response)

	@allow_get_request
	def parse_error(self, request, parse_error):
		status, message = parse_error.args
		raise UMC_Error(message, status=status)
