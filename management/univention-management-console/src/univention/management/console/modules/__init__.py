#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  Base class for UMC 2.0 modules
#
# Copyright 2006-2014 Univention GmbH
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

"""
Python API for UMC modules
==========================

The python API for UMC modules primary consists of one base class that
must be implemented. As an addition the python API provides some helper
functions and classes:

* exception classes
* translation support
* logging functions
* UCR access

The XML file defining the UMC module specifies functions for the
commands provided by the module. These functions must be implemented as
methods of a class named *Instance* that inherits :class:`.Base`.

The following python code example matches the definition in the previous section::

 from univention.management.console import Translation
 from univention.management.console.config import ucr
 from univention.management.console.modules import Base, UMC_OptionTypeError, UMC_OptionMissing, UMC_CommandError
 from univention.management.console.log import MODULE

 _ = Translation( 'univention-management-console-modules-udm' ).translate

 class Instance(Base):
   def query(self, request):
     ...

   def containers(self, request):
     module_name = request.options.get('objectType')
     if not module_name or 'all' == module_name:
       module_name = request.flavor
     if not module_name:
      raise UMC_OptionMissing('No valid module name found')

     module = UDM_Module(module_name)
     self.finished(request.id, module.containers + self.settings.containers(request.flavor))

Each command methods has one parameter that contains the UMCP request of
type
:class:`~univention.management.console.protocol.message.Request`. Such
an object has the following properties:

*id*
	is the unique identifier of the request

*options*
	contains the arguments for the command. For most commands it is a
	dictionary.

*flavor*
	is the name of the flavor that was used to invoke the command. This
	might be *None*

The *containers* method in the example above shows how to retrieve the
command parameters and what to do to send the result back to the
client. Important is that returning a value in a command function does
not send anything back to the client. Therefor the function *finished*
must be invoked. The first parameter is the identifier of the request
that will be answered and the second parameter the data structure
containing the result. As the result is converted to JSON it must just
contain data types that can be converted. The *finished* function has
two further optional parameters. *message* may contain a human readable
text explaining the result and *success* is a boolean parameter defining
the success of the operation. By default *success* is true. By setting
*success* to *False* the UCM module sends an error status back to the
client. Another way to send an error message back to the client is by
raising one of the following exceptions:

*UMC_OptionTypeError*
	The type of a given option does not match

*UMC_OptionMissing*
	One required option is missing

*UMC_CommandError*
	A general error occurred

The base class for modules provides some properties and methods that
could be useful when writing UMC modules:

Properties
 * *username*: The username of the owner of this session
 * *password*: The password of the user

Methods
 * *init*: Is invoked after the module process has been initialised. At that moment, the settings, like locale and username and password are available.
 * *permitted*: Can be used to determine if a specific UMCP command can be invoked by the current user. This method has two parameters: The ''command'' name and the ''options''.

"""

from notifier import signals
import traceback
import ldap

from univention.lib.i18n import Translation

import univention.admin.uldap as udm_uldap
import univention.admin.uexceptions as udm_errors

from ..protocol.message import Response, MIMETYPE_JSON
from ..protocol.definitions import BAD_REQUEST, MODULE_ERR, MODULE_ERR_COMMAND_FAILED, SUCCESS, SUCCESS_MESSAGE, SUCCESS_PARTIAL, SUCCESS_SHUTDOWN
from ..log import MODULE, CORE
from ..config import ucr

_ = Translation('univention.management.console').translate


class UMC_Error(Exception):
	status = BAD_REQUEST

	def __init__(self, message=None, status=None, result=None):
		super(UMC_Error, self).__init__(message)
		self.msg = message
		self.result = result
		if isinstance(status, int):
			self.status = status


class UMC_OptionTypeError(UMC_Error):
	pass  # deprecated, please use .sanitizers instead!


class UMC_OptionMissing(UMC_Error):
	pass  # deprecated, please use .sanitizers instead!


class UMC_CommandError(UMC_Error):
	pass  # deprecated, please use .sanitizers instead!


class UMC_OptionSanitizeError(UMC_OptionTypeError):

	def __init__(self, message, body=None):
		status = 409  # HTTP Conflict
		super(UMC_OptionSanitizeError, self).__init__(message, status, body)


class LDAP_ServerDown(UMC_Error):

	def __init__(self):
		ucr.load()
		self._is_master = ucr.get('server/role') == 'domaincontroller_master'
		self._updates_available = ucr.is_true('update/available')
		self._fqdn = '%s.%s' % (ucr.get('hostname'), ucr.get('domainname'))
		message = '\n'.join(self._error_msg())
		super(LDAP_ServerDown, self).__init__(message, status=503)

	def _error_msg(self):
		yield _('Cannot connect to the LDAP service.')
		yield _('The following steps can help to solve this problem:')
		if self._is_master:
			yield ' * ' + _('Check if enough hard disk space and free RAM is available on this server or free some resources')
		else:
			yield ' * ' + _('Make sure the domaincontroller master is running and reachable from %s') % (self._fqdn,)
			yield ' * ' + _('Check if enough hard disk space and free RAM is available on this server and on the domaincontroller master or free some resources')
		yield ' * ' + _('Restart the LDAP service on the domaincontroller master either via "invoke-rc.d slapd restart" on command line or with the UMC module "System services"')
		if self._updates_available:
			yield ' * ' + _('Install the latest software updates')
		yield _('If the problem persists additional hints about the cause can be found in the following log file(s):')
		yield ' * /var/log/univention/management-console-module-udm.log'


def error_handling(function, method=None):
	method = method or function.__name__

	def _decorated(self, request, *args, **kwargs):
		message = ''
		result = None
		try:
			try:
				return function(self, request, *args, **kwargs)
			except ldap.SERVER_DOWN:
				raise LDAP_ServerDown()
		except UMC_Error as exc:
			status = exc.status
			result = exc.result
			if isinstance(exc, UMC_OptionTypeError):
				message = _('An option passed to %s has the wrong type: %s') % (method, exc)
			elif isinstance(exc, UMC_OptionMissing):
				message = _('One or more options to %s are missing: %s') % (method, exc)
			elif isinstance(exc, UMC_CommandError):
				message = _('The command has failed: %s') % (exc,)
			else:
				message = str(exc)
		except:
			status = MODULE_ERR_COMMAND_FAILED
			message = _("Execution of command '%(command)s' has failed:\n\n%(text)s")
			message = message % {
				'command': ('%s %s' % (request.arguments[0], request.flavor or '')).strip(),
				'text': unicode(traceback.format_exc())
			}
		MODULE.process(str(message))
		self.finished(request.id, result, message, status=status)
	return _decorated


class Base(signals.Provider, Translation):

	'''The base class for UMC modules of version 2 or higher'''

	def __init__(self, domain=None):
		signals.Provider.__init__(self)
		self.signal_new('success')
		self._username = None
		self._user_dn = None
		self._password = None
		self.__acls = None
		self.__requests = {}
		Translation.__init__(self, domain)

	@property
	def username(self):
		return self._username

	@username.setter
	def username(self, username):
		self._username = username

	@property
	def user_dn(self):
		return self._user_dn

	@user_dn.setter
	def user_dn(self, user_dn):
		self._user_dn = user_dn
		MODULE.info('Setting user LDAP DN %r' % (self._user_dn,))

	@property
	def password(self):
		return self._password

	@password.setter
	def password(self, password):
		self._password = password

	@property
	def acls(self):
		return self.__acls

	@acls.setter
	def acls(self, acls):
		self.__acls = acls

	def init(self):
		'''this function is invoked after the initial UMCP SET command
		that passes the base configuration to the module process'''
		pass

	def destroy(self):
		'''this function is invoked before the module process is
		exiting.'''
		pass

	def execute(self, method, request):
		self.__requests[request.id] = (request, method)

		try:
			function = getattr(self, method).im_func
		except AttributeError:
			message = _('Method %r (%r) in %r does not exists.\n\n%s') % (method, request.arguments, self.__class__.__module__, traceback.format_exc())
			self.finished(request.id, None, message=message, status=500)
			return

		function = error_handling(function, method)
		MODULE.info('Executing %s' % (request.arguments,))
		function(self, request)

	def get_user_ldap_connection(self):
		if not self._user_dn:
			return  # local user (probably root)
		try:
			# open an LDAP connection with the user password and credentials
			return udm_uldap.access(
				host=ucr.get('ldap/server/name'),
				base=ucr.get('ldap/base'),
				port=int(ucr.get('ldap/server/port', '7389')),
				binddn=self._user_dn,
				bindpw=self._password,
				follow_referral=True
			)
		except (ldap.LDAPError, udm_errors.base) as exc:
			CORE.warn('Failed to open LDAP connection for user %s: %s' % (self._user_dn, exc))

	def required_options(self, request, *options):
		"""Raises an UMC_OptionMissing exception if any of the given
		options is not found in request.options

		Deprecated. Please use univention.management.console.modules.sanitizers
		"""
		missing = filter(lambda o: o not in request.options, options)
		if missing:
			raise UMC_OptionMissing(', '.join(missing))

	def permitted(self, command, options, flavor=None):
		if not self.__acls:
			return False
		return self.__acls.is_command_allowed(command, options=options, flavor=flavor)

	def finished(self, id, response, message=None, success=True, status=None, mimetype=None):
		"""Should be invoked by module to finish the processing of a
		request. 'id' is the request command identifier, 'dialog' should
		contain the result as UMC dialog and 'success' defines if the
		request could be fulfilled or not. If there is a definition of a
		'_post' processing function it is called immediately."""

		if id not in self.__requests:
			return
		request, method = self.__requests[id]

		if not isinstance(response, Response):
			res = Response(request)

			if mimetype and mimetype != MIMETYPE_JSON:
				res.mimetype = mimetype
				res.body = response
			else:
				res.result = response
				res.message = message
		else:
			res = response

		if not res.status:
			if status is not None:
				res.status = status
			elif success:
				res.status = SUCCESS
			else:
				res.status = MODULE_ERR

		self.result(res)

	def result(self, response):
		if response.id in self.__requests:
			self.signal_emit('success', response)
			del self.__requests[response.id]
