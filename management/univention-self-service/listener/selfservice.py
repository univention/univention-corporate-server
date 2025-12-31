#!/usr/bin/python3
#
# Univention LDAP
"""listener script to set umc/self-service/passwordreset/email/webserver_address."""
#
# SPDX-FileCopyrightText: 2017-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from __future__ import annotations

import univention.config_registry

import listener


description = 'Set umc/self-service/passwordreset/email/webserver_address.'
filter = '(univentionService=univention-self-service)'

UCRV = 'umc/self-service/passwordreset/email/webserver_address'


def handler(dn: str, new: dict[str, list[bytes]], old: dict[str, list[bytes]]) -> None:
    if new:
        ucr = univention.config_registry.ConfigRegistry()
        ucr.load()
        if not ucr.get(UCRV):
            fqdn = '%s.%s' % (new['cn'][0].decode('UTF-8'), new.get('associatedDomain')[0].decode('ASCII'))
            listener.setuid(0)
            try:
                univention.config_registry.handler_set(['%s=%s' % (UCRV, fqdn)])
            finally:
                listener.unsetuid()
