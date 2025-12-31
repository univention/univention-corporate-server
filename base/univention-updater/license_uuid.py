#!/usr/bin/python3
#
# Univention Updater
#  Dump key id from license to local UCR variable
#
# SPDX-FileCopyrightText: 2013-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only


import univention.config_registry

import listener


description = 'Dump key id from license to local UCR variable'
filter = '(&(objectClass=univentionLicense)(cn=admin))'


def handler(dn: str, new: dict[str, list[bytes]], old: dict[str, list[bytes]]) -> None:
    if new:
        listener.setuid(0)
        try:
            ucrVars = ['license/base=%s' % new['univentionLicenseBaseDN'][0].decode('UTF-8')]
            if new.get('univentionLicenseKeyID'):
                ucrVars.append('uuid/license=%s' % new['univentionLicenseKeyID'][0].decode('ASCII'))
            else:
                univention.config_registry.handler_unset(['uuid/license'])
            univention.config_registry.handler_set(ucrVars)
        finally:
            listener.unsetuid()
