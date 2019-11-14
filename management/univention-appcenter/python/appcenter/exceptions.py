#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention App Center
#  Exception classes
#
# Copyright 2015-2019 Univention GmbH
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
#


import re

from univention.appcenter.utils import unique, _


class Abort(Exception):
	'''The Abort class is the base class for a "controlled" abortion of an
	action (meaning: univention-app <action>). This means that this
	situation was foreseen by the developers and is less critical. The
	"code" variable is sent to the App Center server for Univention to get
	a clue what went wrong.
	You should only use one class in different
	places in the code if you are confident that sending this error from
	two places does not lead to irritation. (This explicitly holds for
	Abort itself, you better subclass it)
	If you give a "default_error_msg" variable, you may also use %(var)s
	for formatting in this string. In this case, the __init__ method will
	require the class to be initiated with "var" (either positional or
	non-positional). The last argument (or an argument named "message") can
	overwrite any "default_error_msg".
	'''
	code = 401
	default_error_msg = ''

	def __init__(self, *args, **kwargs):
		keys = re.findall(r'%\(([^)]+)\)', self.default_error_msg)
		keys = unique(keys)
		i = 0
		_args = []
		for key in keys:
			if key in kwargs:
				value = kwargs[key]
			else:
				try:
					value = args[i]
				except IndexError:
					raise TypeError('Need %s for %s' % (key, self.__class__.__name__))
				i += 1
			setattr(self, key, value)
			_args.append(value)
		if len(args) > i:
			self.message = args[i]
		elif 'message' in kwargs:
			self.message = kwargs.get('message')
		else:
			self.message = ''
		self.args = tuple(_args)

	def get_exc_details(self):
		return None

	def __str__(self):
		if self.message:
			return self.message
		else:
			return self.default_error_msg % self.__dict__


class AbortWithDetails(Abort):
	def __init__(self, *args, **kwargs):
		self._exc_details = kwargs
		super(AbortWithDetails, self).__init__(*args, **kwargs)

	def get_exc_details(self):
		if self._exc_details:
			return self._exc_details


class NetworkError(Abort):
	code = 402


class CredentialsNoUsernameError(Abort):
	code = 403


class CredentialsNoPasswordError(Abort):
	code = 404


class ConnectionFailed(Abort):
	code = 405
	default_error_msg = 'No connection possible'


class ConnectionFailedSecretFile(ConnectionFailed):
	code = 406
	default_error_msg = '/etc/machine.secret not readable'


class ConnectionFailedInvalidAdminCredentials(ConnectionFailed):
	code = 407
	default_error_msg = 'LDAP server does not accept admin password!'


class ConnectionFailedInvalidMachineCredentials(ConnectionFailed):
	code = 408
	default_error_msg = 'LDAP server does not accept machine password!'


class ConnectionFailedInvalidUserCredentials(ConnectionFailed):
	code = 409
	default_error_msg = 'Too many failed attempts!'


class ConnectionFailedServerDown(ConnectionFailed):
	code = 410
	default_error_msg = 'LDAP server is not running!'


class UpdateSignatureVerificationFailed(Abort):
	code = 411
	default_error_msg = 'Signature verification for %(filename)s failed'


class UpdateUnpackArchiveFailed(Abort):
	code = 412
	default_error_msg = 'Failed to unpack "%(filename)s"'


class ConfigureFailed(Abort):
	code = 413
	default_error_msg = 'Failed to configure: %(app)s: %(exc)s'


class ShellNoCommandError(Abort):
	code = 414
	default_error_msg = 'Cannot run command: No command specified'


class ShellAppNotRunning(Abort):
	code = 415
	default_error_msg = 'Cannot run command: %(app)s is not running in a container'


class InstallSetupFailed(AbortWithDetails):
	code = 416
	default_error_msg = 'Setup script failed!'


# TODO: AbortWithDetails
class DockerCouldNotStartContainer(Abort):
	code = 417
	default_error_msg = 'Unable to start the container!'

	def get_exc_details(self):
		return str(self)


class DatabaseConnectorError(Abort):
	code = 418

	def get_exc_details(self):
		return str(self)


class InstallNonDockerVersionError(Abort):
	code = 419
	default_error_msg = 'Cannot use %(app)s as docker is to be ignored, yet, only non-docker versions could be found'


# TODO: AbortWithDetails
class InstallFailed(Abort):
	code = 420
	default_error_msg = 'Failed to install the App'


class InstallMasterPackagesNoninteractiveError(Abort):
	code = 421


class InstallMasterPackagesPasswordError(Abort):
	code = 422


class RemoveBackupFailed(Abort):
	code = 423
	default_error_msg = 'Could not backup container!'


class RemovePluginUnsupported(Abort):
	code = 424
	default_error_msg = 'Uninstallation of a plugin is not supported!'


class RegisterSchemaFailed(AbortWithDetails):
	code = 425
	default_error_msg = 'Registration of schema extension failed (Code: %(code)s)'

	def get_exc_details(self):
		return str(self)


class RegisterSchemaFileFailed(Abort):
	code = 426
	default_error_msg = 'Registering schema file %(filename)s failed'

	def get_exc_details(self):
		return str(self)


# Not used. Here for reference (and to prevent re-using the code)
class DockerVerificationFailed(Abort):
	code = 427

	def get_exc_details(self):
		return str(self)


class LocalAppCenterError(Abort):
	# this is a bit lazy...
	code = 428


class UpgradeStartContainerFailed(Abort):
	code = 429
	default_error_msg = 'Could not start the app container. It needs to be running to be upgraded!'


class UpgradeBackupFailed(Abort):
	code = 430
	default_error_msg = 'Could not backup container!'


class UpgradeAppFailed(Abort):
	code = 431
	default_error_msg = 'App upgrade script failed'


class UpgradePackagesFailed(Abort):
	code = 432
	default_error_msg = 'Package upgrade script failed'


class UpgradeReleaseFailed(Abort):
	code = 433
	default_error_msg = 'Release upgrade script failed'


class ConnectionFailedConnectError(ConnectionFailed):
	code = 434

	def __init__(self, exc):
		self.details = exc.args[0]

	def __str__(self):
		msg = _('LDAP connection refused. There may be an issue with the certificate of the LDAP server. Please also check the proxy and firewall settings, if any.')
		details = None
		try:
			details = self.details.get('info', 'No further details')
		except (IndexError, KeyError):
			pass
		if details:
			msg += ' (' + details + ')'
		return msg


class DockerImagePullFailed(Abort):
	code = 435
	default_error_msg = 'Downloading Docker image %(image)s failed: %(out)s'


# TODO: AbortWithDetails
class RemoveFailed(Abort):
	code = 436
	default_error_msg = 'Failed to uninstall the App'


class ParallelOperationInProgress(Abort):
	code = 437
	default_error_msg = 'Another package operation is in progress'


class InstallWithoutPermissionError(Abort):
	code = 438
	default_error_msg = 'The App requires install permissions which are missing. Please contact the App Provider.'


class ReinitializeError(Abort):
	code = 439
	default_error_msg = 'Reinitializing the App failed.'


class AppCenterError(Exception):
	'''A "real" exception that developers cannot handle very well.
	The difference between AppCenterError and Abort is that Abort is a
	somewhat defined behavior, i.e. App installation has to fail if the
	setup script fails. AppCenterError happens where it was not supposed
	to.
	The difference between AppCenterError and Exception is that
	AppCenterError gives a nicer feedback for the Administrator than a
	scary traceback. You can even put custom information into the proposed
	feedback mail (raise AppCenterError(str(custom))).
	As with Abort, AppCenterError should be subclassed and get a different
	code.'''
	code = 500
	title = _('An error occurred!')
	info = _('We are sorry for the inconvenience. Please help us to improve the App Center and the Apps by sending us the information below.')


class AppCenterErrorContainerStart(AppCenterError):
	code = 501
	title = _('The docker container could not be started!')
