#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  App Center sanitizers
#
# Copyright 2011-2019 Univention GmbH
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

import univention.config_registry
import univention.management.console as umc
import univention.management.console.modules as umcm
from univention.management.console.log import MODULE
from univention.management.console.base import LDAP_ServerDown
from univention.management.console.modules.sanitizers import Sanitizer, StringSanitizer, DictSanitizer, BooleanSanitizer
from univention.management.console.modules.appcenter.app_center import AppcenterServerContactFailed
from univention.appcenter.actions.credentials import ConnectionFailedServerDown, ConnectionFailedInvalidMachineCredentials, ConnectionFailedInvalidUserCredentials, ConnectionFailedSecretFile
from univention.appcenter.exceptions import Abort
from univention.appcenter.app_cache import Apps


_ = umc.Translation('univention-management-console-module-appcenter').translate


def error_handling(etype, exc, etraceback):
	if isinstance(exc, (ConnectionFailedSecretFile,)):
		MODULE.error(str(exc))
		error_msg = [_('Cannot connect to the LDAP service.'), _('The server seems to be lacking a proper password file.'), _('Please check the join state of the machine.')]
		raise umcm.UMC_Error('\n'.join(error_msg), status=500)
	if isinstance(exc, (ConnectionFailedInvalidUserCredentials,)):
		MODULE.error(str(exc))
		error_msg = [_('Cannot connect to the LDAP service.'), _('The credentials provided were not accepted.'), _('This may be solved by simply logging out and in again.'), _('Maybe your password changed during the session.')]
		raise umcm.UMC_Error('\n'.join(error_msg), status=500)
	if isinstance(exc, (ConnectionFailedInvalidMachineCredentials,)):
		MODULE.error(str(exc))
		error_msg = [_('Cannot connect to the LDAP service.'), _('The credentials provided were not accepted.'), _('This may be solved by simply logging out and in again.'), _('Maybe the machine password changed during the session.')]
		raise umcm.UMC_Error('\n'.join(error_msg), status=500)
	if isinstance(exc, (ConnectionFailedServerDown,)):
		MODULE.error(str(exc))
		raise LDAP_ServerDown()
	if isinstance(exc, (Abort, SystemError, AppcenterServerContactFailed)):
		MODULE.error(str(exc))
		raise umcm.UMC_Error(str(exc), status=500)


class AppSanitizer(Sanitizer):

	def _sanitize(self, value, name, further_args):
		app = Apps().find(value)
		if not app.is_installed() and not app.install_permissions_exist():
			apps = Apps().get_all_apps_with_id(app.id)
			apps = [_app for _app in apps if not _app.install_permissions]
			if apps:
				app = sorted(apps)[-1]
		return app


# TODO: remove this, unused!
class AnySanitizer(Sanitizer):

	def _sanitize(self, value, name, further_args):
		any_given = any([value] + further_args.values())
		if not any_given:
			self.raise_formatted_validation_error(_('Any of %r must be given') % ([name] + further_args.keys()), name, value)
		return any_given


class NoDoubleNameSanitizer(StringSanitizer):

	def _sanitize(self, value, name, further_arguments):
		from constants import COMPONENT_BASE
		ucr = univention.config_registry.ConfigRegistry()
		ucr.load()
		if '%s/%s' % (COMPONENT_BASE, value) in ucr:
			self.raise_validation_error(_("There already is a component with this name"))
		return value


basic_components_sanitizer = DictSanitizer({
	'server': StringSanitizer(required=True, minimum=1),
	'prefix': StringSanitizer(required=True),
	'unmaintained': BooleanSanitizer(required=True),
},
	allow_other_keys=False,
)


advanced_components_sanitizer = DictSanitizer({
	'server': StringSanitizer(),
	'prefix': StringSanitizer(),
	'unmaintained': BooleanSanitizer(),
	'enabled': BooleanSanitizer(required=True),
	'name': StringSanitizer(required=True, regex_pattern='^[A-Za-z0-9\-\_\.]+$'),
	'description': StringSanitizer(),
	'username': StringSanitizer(),
	'password': StringSanitizer(),
	'version': StringSanitizer(regex_pattern='^((([0-9]+\\.[0-9]+|current),)*([0-9]+\\.[0-9]+|current))?$')
}
)


add_components_sanitizer = advanced_components_sanitizer + DictSanitizer({
	'name': NoDoubleNameSanitizer(required=True, regex_pattern='^[A-Za-z0-9\-\_\.]+$'),
}
)
