#
# Univention Management Console
# Listener module to set save all UMC service providers in UCR
#
# SPDX-FileCopyrightText: 2015-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from __future__ import annotations

import os
import subprocess

import univention.debug as ud
from univention.config_registry import handler_set, handler_unset

import listener


name = 'umc-service-providers'
description = 'Manage umc/saml/trusted/sp/* and ldap/server/sasl/oauthbearer/trusted-authorized-party/* variable'
filter = '(|(objectClass=univentionDomainController)(objectClass=univentionMemberServer))'
attributes = ['univentionService', 'cn', 'associatedDomain']

__changed_trusted_sp = False


def handler(dn: str, new: dict[str, list[bytes]], old: dict[str, list[bytes]]) -> None:
    global __changed_trusted_sp
    listener.setuid(0)
    try:
        try:
            fqdn = '%s.%s' % (new['cn'][0].decode('UTF-8'), new['associatedDomain'][0].decode('UTF-8'))
        except (KeyError, IndexError):
            return
        umc_service_active = b'Univention Management Console' in new.get('univentionService', [])
        umc_service_was_active = b'Univention Management Console' in old.get('univentionService', [])
        domain_added = 'associatedDomain' in new and 'associatedDomain' not in old and umc_service_active
        if umc_service_active and (domain_added or not umc_service_was_active):
            handler_set([
                'umc/saml/trusted/sp/%s=%s' % (fqdn, fqdn),
                'ldap/server/sasl/oauthbearer/trusted-authorized-party/%s=https://%s/univention/oidc/' % (fqdn, fqdn),
            ])
            __changed_trusted_sp = True
        elif umc_service_was_active and not umc_service_active:
            handler_unset([
                'umc/saml/trusted/sp/%s' % (fqdn,),
                'ldap/server/sasl/oauthbearer/trusted-authorized-party/%s' % (fqdn,),
            ])
            __changed_trusted_sp = True

    finally:
        listener.unsetuid()


def postrun() -> None:
    global __changed_trusted_sp

    if __changed_trusted_sp:
        __changed_trusted_sp = False
        slapd_running = not subprocess.call(['pidof', 'slapd'])
        initscript = '/etc/init.d/slapd'
        if os.path.exists(initscript) and slapd_running:
            listener.setuid(0)
            try:
                ud.debug(ud.LISTENER, ud.PROCESS, '%s: Reloading LDAP server.' % (name,))
                p = subprocess.Popen([initscript, 'graceful-restart'], close_fds=True)
                p.wait()
                if p.returncode != 0:
                    ud.debug(ud.LISTENER, ud.ERROR, '%s: LDAP server restart returned %s.' % (name, p.returncode))
            finally:
                listener.unsetuid()
