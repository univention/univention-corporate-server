#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  session handling
#
# Copyright 2006-2015 Univention GmbH
#
# http://www.univention.de/
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
# <http://www.gnu.org/licenses/>.

"""Implements several helper classes to handle the state of a session
and the communication with the module processes"""

import base64
import ldap
import os
import sys
import time
import json
import traceback
import gzip
import re

import ldap.filter

import notifier
import notifier.signals as signals
import notifier.popen as popen
from notifier import threads

import univention.admin.uldap as udm_uldap
import univention.admin.uexceptions as udm_errors

from univention.lib.i18n import I18N_Error

from .message import Response, Request, MIMETYPE_JSON, InvalidOptionsError
from .client import Client, NoSocketError
from .version import VERSION
from .definitions import (SUCCESS, BAD_REQUEST_INVALID_OPTS, BAD_REQUEST_INVALID_ARGS,
	status_description, BAD_REQUEST_UNAVAILABLE_LOCALE, BAD_REQUEST_FORBIDDEN,
	BAD_REQUEST_NOT_FOUND, SERVER_ERR_MODULE_FAILED)

from ..resources import moduleManager, categoryManager
from ..auth import AuthHandler
from ..pam import PamAuth, PasswordChangeFailed
from ..acl import LDAP_ACLs
from ..log import CORE
from ..config import MODULE_INACTIVITY_TIMER, MODULE_DEBUG_LEVEL, MODULE_COMMAND, ucr
from ..locales import I18N, I18N_Manager
from ..base import Base, UMC_Error
from ..modules.sanitizers import StringSanitizer, DictSanitizer
from ..modules.decorators import sanitize

TEMPUPLOADDIR = '/var/tmp/univention-management-console-frontend'


class State(signals.Provider):

	"""Holds information about the state of an active session

	:param str client: IP address + port
	:param fd socket: file descriptor or socket obbject
	"""

	def __init__(self, client, socket):
		signals.Provider.__init__(self)
		self.__auth = AuthHandler()
		self.__auth.signal_connect('authenticated', self._authenticated)
		self.client = client
		self.socket = socket
		self.processor = None
		self.authenticated = False
		self.__credentials = (None, None)
		self.buffer = ''
		self.requests = {}
		self.authResponse = None
		self.signal_new('authenticated')
		self.resend_queue = []
		self.running = False
		self.username = None

	def __del__(self):
		CORE.info('The session is shutting down')
		if self.processor:
			self.processor.__del__()
		del self.processor

	def _authenticated(self, result):
		self.__credentials = result.credentials
		self.signal_emit('authenticated', result, self)

	def authenticate(self, username, password, new_password=None, locale=None):
		"""Initiates an authentication process"""
		self.username = username
		self.__auth.authenticate(username, password, new_password, locale)

	def credentials(self):
		"""Returns the credentials"""
		return self.__credentials


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
		Client.__init__(self, unix=socket, ssl=False, auth=False)
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
		if msg.command == 'SET' and 'commands/permitted' in msg.arguments:
			return
		if msg.command == 'EXIT' and 'internal' in msg.arguments:
			return

		self.signal_emit('result', msg)

	def pid(self):
		"""Returns process ID of module process"""
		return self.__pid


class Processor(Base):

	"""Implements a proxy and command handler. It handles all internal
	UMCP commands and passes the commands for a module to the
	subprocess.

	:param str username: name of the user who authenticated for this session
	:param str password: password of the user
	"""

	def __init__(self, username, password):
		Base.__init__(self, 'univention-management-console')

		self.username = username
		self.password = password
		self.__udm_users_module_initialised = False
		self.__command_list = None
		self.i18n = I18N_Manager()
		self.i18n['umc-core'] = I18N()

		# stores the module processes [ modulename ] = <>
		self.__processes = {}

		self.__killtimer = {}

		self._init_ldap_connection()
		self._search_user_dn()

		# read the ACLs
		self._reload_acls_and_permitted_commands()

		self.signal_new('response')

	def _search_user_dn(self):
		if self.lo is not None:
			# get the LDAP DN of the authorized user
			ldap_dn = self.lo.searchDn('(uid=%s)' % ldap.filter.escape_filter_chars(self._username))
			if ldap_dn:
				self._user_dn = ldap_dn[0]
				CORE.info('The LDAP DN for user %s is %s' % (self._username, self._user_dn))

		if not self._user_dn and self._username not in ('root', '__systemsetup__'):
			CORE.error('The LDAP DN for user %s could not be found (lo=%r)' % (self._username, self.lo))

	def _reload_acls_and_permitted_commands(self):
		self.acls = LDAP_ACLs(self.lo, self._username, ucr['ldap/base'])
		self.__command_list = moduleManager.permitted_commands(ucr['hostname'], self.acls)

	def _reload_i18n(self):
		self.i18n.set_locale(str(self.i18n.locale))

	def _init_ldap_connection(self):
		try:
			# get LDAP connection with machine account
			self.lo, self.po = udm_uldap.getMachineConnection(ldap_master=False)
		except (ldap.LDAPError, udm_errors.base, IOError) as exc:
			# problems connection to LDAP server or the server is not joined (machine.secret is missing)
			CORE.warn('An error occurred connecting to the LDAP server: %s' % (exc,))
			self.lo = None

	def shutdown(self):
		"""Instructs the module process to shutdown"""
		CORE.info('The session is shutting down. Sending UMC modules an EXIT request (%d processes)' % len(self.__processes))
		for module_name, process in self.__processes.items():
			CORE.info('Ask module %s to shutdown gracefully' % (module_name,))
			req = Request('EXIT', arguments=[module_name, 'internal'])
			process.request(req)

	def __del__(self):
		CORE.process('Processor: dying')
		for process in self.__processes.values():
			#process.__del__()  # calling this will cause python notifier to fail hard! Bug #37457
			del process
		if self.lo:
			self.lo.lo.lo.unbind()  # close the connection to LDAP

	def get_module_name(self, command):
		"""Returns the name of the module that provides the given command

		:param str command: the command name
		"""
		return moduleManager.module_providing(self.__command_list, command)

	def request(self, msg):
		"""Handles an incoming UMCP request and passes the requests to
		specific handler functions.

		:param Request msg: UMCP request
		"""
		if msg.command in ('EXIT', 'GET', 'SET', 'VERSION', 'COMMAND', 'UPLOAD'):
			method = 'handle_request_%s' % (msg.command.lower(),)
		else:
			method = 'handle_request_unknown'

		self.execute(method, msg)

	def _purge_child(self, module_name):
		if module_name in self.__processes:
			CORE.process('module %s is still running - purging module out of memory' % module_name)
			pid = self.__processes[module_name].pid()
			os.kill(pid, 9)
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

	def handle_request_version(self, msg):
		"""Handles a VERSION request by returning the version of the UMC
		server's protocol version.

		:param Request msg: UMCP request
		"""
		res = Response(msg)
		res.status = SUCCESS  # Ok
		res.body['version'] = VERSION
		self.result(res)

	CHANGELOG_VERSION = re.compile('^[^(]*\(([^)]*)\).*')

	def handle_request_get(self, msg):
		"""Handles a GET request. The following possible variants are supported:

		modules/list
			Returns a list of all available UMC modules within the current session

		categories/list
			Returns a list of all known categories

		user/preferences
			Returns the user preferences as a dict.

		:param Request msg: UMCP request
		"""

		res = Response(msg)
		res.status = SUCCESS

		if 'ucr' in msg.arguments:
			ucr.load()
			res.result = {}
			if not isinstance(msg.options, (list, tuple)):
				raise InvalidOptionsError
			for value in msg.options:
				try:
					if not value:
						# make sure that 'value' is non-empty
						CORE.warn('Empty UCR variable requested. Ignoring value...')
						continue
					if value.endswith('*'):
						value = value[: -1]
						for var in filter(lambda x: x.startswith(value), ucr.keys()):
							res.result[var] = ucr.get(var)
					else:
						res.result[value] = ucr.get(value)
				except (TypeError, IndexError, AttributeError):
					CORE.warn('Invalid UCR variable requested: %s' % (value,))
					res.status = BAD_REQUEST_INVALID_OPTS
					res.message = self.i18n._('Invalid UCR variable requested: %s') % (value,)
		elif 'info' in msg.arguments:
			ucr.load()
			res.result = {}
			try:
				fd = gzip.open('/usr/share/doc/univention-management-console-server/changelog.Debian.gz')
				line = fd.readline()
				fd.close()
				match = self.CHANGELOG_VERSION.match(line)
				if not match:
					raise IOError
				res.result['umc_version'] = match.groups()[0]
				res.result['ucs_version'] = '{0}-{1} errata{2} ({3})'.format(ucr.get('version/version', ''), ucr.get('version/patchlevel', ''), ucr.get('version/erratalevel', '0'), ucr.get('version/releasename', ''))
				res.result['server'] = '{0}.{1}'.format(ucr.get('hostname', ''), ucr.get('domainname', ''))
				res.result['ssl_validity_host'] = int(ucr.get('ssl/validity/host', '0')) * 24 * 60 * 60 * 1000
				res.result['ssl_validity_root'] = int(ucr.get('ssl/validity/root', '0')) * 24 * 60 * 60 * 1000
			except IOError:
				res.status = BAD_REQUEST_FORBIDDEN
				pass
		elif 'modules/list' in msg.arguments:
			categoryManager.load()
			moduleManager.load()
			if isinstance(msg.options, dict) and msg.options.get('reload'):
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
							'description': self.i18n._(flavor.description, translationId),
							'icon': flavor.icon,
							'categories': (flavor.categories or module.categories) + favcat,
							'priority': flavor.priority,
							'keywords': list(set(flavor.keywords + [self.i18n._(keyword, translationId) for keyword in flavor.keywords]))
						})
				else:
					favcat = []
					if id in favorites:
						favcat.append('_favorites_')
					modules.append({
						'id': id,
						'name': self.i18n._(module.name, id),
						'description': self.i18n._(module.description, id),
						'icon': module.icon,
						'categories': module.categories + favcat,
						'priority': module.priority,
						'keywords': list(set(module.keywords + [self.i18n._(keyword, id) for keyword in module.keywords]))
					})
			res.body['modules'] = modules
			CORE.info('Modules: %s' % (modules,))

		elif 'categories/list' in msg.arguments:
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
			res.body['categories'] = categories
			CORE.info('Categories: %s' % (res.body['categories'],))
		elif 'user/preferences' in msg.arguments:
			# fallback is an empty dict
			res.body['preferences'] = self._get_user_preferences(self.get_user_ldap_connection())
		elif 'hosts/list' in msg.arguments:
			self._init_ldap_connection()
			if self.lo:
				try:
					domaincontrollers = self.lo.search(filter="(objectClass=univentionDomainController)")
				except (ldap.LDAPError, udm_errors.base) as exc:
					CORE.warn('Could not search for domaincontrollers: %s' % (exc))
					domaincontrollers = []
				res.result = ['%s.%s' % (computer['cn'][0], computer['associatedDomain'][0]) for dn, computer in domaincontrollers if computer.get('associatedDomain')]
				res.result.sort()
			else:
				# unjoined / no LDAP connection
				res.result = []
		else:
			res.status = BAD_REQUEST_INVALID_ARGS

		self.result(res)

	def handle_request_set(self, msg):
		"""Handles a SET request. No argument may be given. The
		variables that should be set are passed via the request
		options. Currently the only variable that may be set is the
		locale. If any unknown variable is given the the request is
		invalidated.

		:param Request msg: UMCP request
		"""
		res = Response(msg)
		if len(msg.arguments):
			res.status = BAD_REQUEST_INVALID_ARGS
			res.message = status_description(res.status)

			self.result(res)
			return

		res.status = SUCCESS
		if not isinstance(msg.options, dict):
			raise InvalidOptionsError
		for key, value in msg.options.items():
			if key == 'password':
				self._change_user_password(msg)
				return
			if key == 'locale':
				try:
					self.set_language(value)
					CORE.info('Setting locale: %r' % (value,))
					self.i18n.set_locale(value)
				except (I18N_Error, AttributeError, TypeError):
					res.status = BAD_REQUEST_UNAVAILABLE_LOCALE
					res.message = status_description(res.status)
					CORE.warn('Setting locale to specified locale failed (%r)' % (value,))
					CORE.warn('Falling back to C')
					self.set_language('C')
					self.i18n.set_locale('C')
					break
			elif key == 'user' and isinstance(value, dict) and 'preferences' in value:
				try:
					# make sure we got a dict
					prefs = value['preferences']
					if not isinstance(prefs, dict):
						raise ValueError('user preferences are not a dict: %r' % (prefs,))

					lo = self.get_user_ldap_connection()
					# eliminate double entries
					preferences = self._get_user_preferences(lo)
					preferences.update(dict(prefs))
					if preferences:
						self._set_user_preferences(lo, preferences)

				except (ValueError, ldap.LDAPError, udm_errors.base) as exc:
					CORE.warn('Could not set given option: %r' % (exc,))
					res.status = BAD_REQUEST_INVALID_OPTS
					res.message = status_description(res.status)
					break
			else:
				res.status = BAD_REQUEST_INVALID_OPTS
				res.message = status_description(res.status)
				break
		self.result(res)

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

	def _get_user_favorites(self):
		favorites = set()
		if not self._user_dn:  # no LDAP user
			favorites = set(ucr.get('umc/web/favorites/default', '').split(','))
		else:
			favorites = self._get_user_preferences(self.get_user_ldap_connection()).setdefault('favorites', ucr.get('umc/web/favorites/default', '')).strip()
			favorites = set(favorites.split(','))

		# appcenter module has changed to appcenter:appcenter -> make sure
		# that it will be in the favorites also after an update from
		# UCS 3.2 to UCS 4.0 (cf. Bug #36416)
		if 'appcenter' in favorites:
			favorites.add('appcenter:appcenter')
		return favorites

	@sanitize(password=DictSanitizer(dict(
		password=StringSanitizer(required=True),
		new_password=StringSanitizer(required=True),
	)))
	def _change_user_password(self, request):
		CORE.info('Got password changing request')

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
		res = Response(request)
		if isinstance(result, PasswordChangeFailed):
			res.status = 400#409
			res.message = '%s' % (result,)
			res.result = {'new_password': '%s' % (result,)}
		elif isinstance(result, BaseException):
			tb = ''.join(traceback.format_exception(*thread.exc_info))
			CORE.error('Changing password failed: %s' % (tb,))
			res.status = 500
			res.message = '%s%s' % (result, tb)
		else:
			CORE.info('Successfully changed password')
			res.status = 200
			res.message = self.i18n._('Password successfully changed.')

			self._password = new_password

			try:
				self._update_module_passwords()
			except:
				res.status = 500
				error_msg = self.i18n._('Nevertheless an error occured while updating the password for running modules. Please relogin to UMC to solve this problem.')
				res.message = ('%s %s%s' % (res.message, error_msg, traceback.format_exc()))

		self.result(res)

	def _update_module_passwords(self):
		exc_info = None
		for module_name, proc in self.__processes.items():
			CORE.info('Changing password on running module %s' % (module_name,))
			req = Request('SET', arguments=[module_name], options={'password': self._password})
			try:
				proc.request(req)
			except:
				exc_info = sys.exc_info()
		if exc_info:
			raise exc_info[0], exc_info[1], exc_info[2]

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
		# request.options = ( { 'filename' : store.filename, 'name' : store.name, 'tmpfile' : tmpfile } )

		if not isinstance(msg.options, (list, tuple)):
			raise InvalidOptionsError

		for file_obj in msg.options:
			# check if required options exists and file_obj is a dict
			try:
				tmpfilename, filename, name = file_obj['tmpfile'], file_obj['filename'], file_obj['name']
			except:
				raise InvalidOptionsError('required options "tmpfile", "filename" or "name" is missing')

			# limit files to tmpdir
			if not os.path.realpath(tmpfilename).startswith(TEMPUPLOADDIR):
				raise InvalidOptionsError('invalid file: invalid path')

			# check if file exists
			if not os.path.isfile(tmpfilename):
				raise InvalidOptionsError('invalid file: file does not exists')

			# don't accept files bigger than umc/server/upload/max
			st = os.stat(tmpfilename)
			max_size = int(ucr.get('umc/server/upload/max', 64)) * 1024
			if st.st_size > max_size:
				raise InvalidOptionsError('filesize is too large, maximum allowed filesize is %d' % (max_size,))

		if msg.arguments and msg.arguments[0] not in ('', '/'):
			# The request has arguments, so it will be treaten as COMMAND
			self.handle_request_command(msg)
			return

		# The request is an generic UPLOAD command (/upload)
		result = []
		for file_obj in msg.options:
			# read tmpfile and convert to base64
			tmpfilename, filename, name = file_obj['tmpfile'], file_obj['filename'], file_obj['name']
			with open(tmpfilename) as buf:
				b64buf = base64.b64encode(buf.read())
			result.append({'filename': filename, 'name': name, 'content': b64buf})

		response = Response(msg)
		response.result = result
		response.status = SUCCESS

		self.result(response)

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
		if len(msg.arguments) > 0:
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
			res = Response(msg)
			res.status = BAD_REQUEST_FORBIDDEN
			res.message = status_description(res.status)
			self.result(res)
			return

		if msg.arguments:
			if msg.mimetype == MIMETYPE_JSON:
				is_allowed = self.acls.is_command_allowed(msg.arguments[0], options=msg.options, flavor=msg.flavor)
			else:
				is_allowed = self.acls.is_command_allowed(msg.arguments[0])
			if not is_allowed:
				response = Response(msg)
				response.status = BAD_REQUEST_FORBIDDEN
				response.message = status_description(response.status)
				self.result(response)
				return
			if module_name not in self.__processes:
				CORE.info('Starting new module process and passing new request to module %s: %s' % (module_name, str(msg._id)))
				try:
					mod_proc = ModuleProcess(module_name, debug=MODULE_DEBUG_LEVEL, locale=self.i18n.locale)
				except OSError as exc:
					if exc.errno == 12:  # cannot allocate Memory
						raise UMC_Error(self.i18n._('Could not open the module. There is not enough memory available on the server. Please try again later.'), status=503)
					raise
				mod_proc.signal_connect('result', self.result)

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
			res.message = status_description(res.status)
			self.result(res)
			# cleanup module
			mod.signal_disconnect('closed', notifier.Callback(self._socket_died))
			mod.signal_disconnect('result', notifier.Callback(self.result))
			mod.signal_disconnect('finished', notifier.Callback(self._mod_died))
			if mod.name in self.__processes:
				self.__processes[mod.name].__del__()
				del self.__processes[mod.name]

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
				'credentials': {'username': self._username, 'password': self._password, 'user_dn': self._user_dn},
			}
			if str(self.i18n.locale):
				options['locale'] = str(self.i18n.locale)

			# WARNING! This debug message contains credentials!!!
			# CORE.info( 'Initialize module process: %s' % options )

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
			self.__processes[module_name].invalidate_all_requests()
			if self.__processes[module_name]._inactivity_timer is not None:
				CORE.warn('Remove inactivity timer')
				notifier.timer_remove(self.__processes[module_name]._inactivity_timer)
			del self.__processes[module_name]

	def handle_request_unknown(self, msg):
		"""Handles an unknown or invalid request that is answered with a
		status code BAD_REQUEST_NOT_FOUND.

		:param Request msg: UMCP request
		"""
		res = Response(msg)
		res.status = BAD_REQUEST_NOT_FOUND
		res.message = status_description(res.status)

		self.result(res)

if __name__ == '__main__':
	processor = Processor('Administrator', 'univention')
	processor.handle_request_get(None)
