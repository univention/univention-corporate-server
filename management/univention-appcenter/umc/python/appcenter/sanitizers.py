#!/usr/bin/python3
#
# Univention Management Console
#  App Center sanitizers
#
# SPDX-FileCopyrightText: 2011-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import univention.config_registry
import univention.management.console as umc
import univention.management.console.modules as umcm
from univention.appcenter.actions.credentials import (
    ConnectionFailedInvalidMachineCredentials, ConnectionFailedInvalidUserCredentials, ConnectionFailedSecretFile,
    ConnectionFailedServerDown,
)
from univention.appcenter.app_cache import Apps
from univention.appcenter.exceptions import Abort
from univention.management.console.base import LDAP_ServerDown
from univention.management.console.log import MODULE
from univention.management.console.modules.sanitizers import BooleanSanitizer, DictSanitizer, Sanitizer, StringSanitizer


_ = umc.Translation('univention-management-console-module-appcenter').translate


def error_handling(etype, exc, etraceback):
    if isinstance(exc, ConnectionFailedSecretFile):
        MODULE.error(str(exc))
        error_msg = [_('Cannot connect to the LDAP service.'), _('The server seems to be lacking a proper password file.'), _('Please check the join state of the machine.')]
        raise umcm.UMC_Error('\n'.join(error_msg), status=500)
    if isinstance(exc, ConnectionFailedInvalidUserCredentials):
        MODULE.error(str(exc))
        error_msg = [_('Cannot connect to the LDAP service.'), _('The credentials provided were not accepted.'), _('This may be solved by simply logging out and in again.'), _('Maybe your password changed during the session.')]
        raise umcm.UMC_Error('\n'.join(error_msg), status=500)
    if isinstance(exc, ConnectionFailedInvalidMachineCredentials):
        MODULE.error(str(exc))
        error_msg = [_('Cannot connect to the LDAP service.'), _('The credentials provided were not accepted.'), _('This may be solved by simply logging out and in again.'), _('Maybe the machine password changed during the session.')]
        raise umcm.UMC_Error('\n'.join(error_msg), status=500)
    if isinstance(exc, ConnectionFailedServerDown):
        MODULE.error(str(exc))
        raise LDAP_ServerDown()
    if isinstance(exc, Abort | SystemError):
        MODULE.error(str(exc))
        raise umcm.UMC_Error(str(exc), status=500)


class AppSanitizer(Sanitizer):

    def _sanitize(self, value, name, further_args):
        app = Apps.find_by_string(value)
        if not app:
            self.raise_validation_error(_("Could not find an application for %s") % (value, ))
        app_version = app.version
        if not app.is_installed() and not app.install_permissions_exist():
            apps = Apps().get_all_apps_with_id(app.id)
            apps = [_app for _app in apps if not _app.install_permissions]
            if apps:
                for _app in apps:
                    if _app.version == app_version:
                        app = _app
                        break
                else:
                    app = sorted(apps)[-1]
        return app


class NoDoubleNameSanitizer(StringSanitizer):

    def _sanitize(self, value, name, further_arguments):
        from .constants import COMPONENT_BASE
        ucr = univention.config_registry.ConfigRegistry()
        ucr.load()
        if '%s/%s' % (COMPONENT_BASE, value) in ucr:
            self.raise_validation_error(_("There already is a component with this name"))
        return value


basic_components_sanitizer = DictSanitizer({
    'server': StringSanitizer(required=True, minimum=1),
},
    allow_other_keys=False,
)


advanced_components_sanitizer = DictSanitizer({
    'server': StringSanitizer(),
    'enabled': BooleanSanitizer(required=True),
    'name': StringSanitizer(required=True, regex_pattern=r'^[A-Za-z0-9\-\_\.]+$'),
    'description': StringSanitizer(),
    'version': StringSanitizer(regex_pattern='^((([0-9]+\\.[0-9]+|current),)*([0-9]+\\.[0-9]+|current))?$'),
})


add_components_sanitizer = advanced_components_sanitizer + DictSanitizer({
    'name': NoDoubleNameSanitizer(required=True, regex_pattern=r'^[A-Za-z0-9\-\_\.]+$'),
})
