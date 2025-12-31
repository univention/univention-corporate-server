#
# Univention DHCP
#  listener module
#
# SPDX-FileCopyrightText: 2004-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from __future__ import annotations

import univention.debug as ud

from listener import configRegistry as ucr, run


description = 'Restart the dhcp service if a dhcp subnet or a policy was changed'
filter = (
    '(|'
    '(objectClass=univentionDhcpSubnet)'
    '(objectClass=univentionDhcpService)'
    '(objectClass=univentionPolicyDhcpBoot)'
    '(objectClass=univentionPolicyDhcpDns)'
    '(objectClass=univentionPolicyDhcpDnsUpdate)'
    '(objectClass=univentionPolicyDhcpLeaseTime)'
    '(objectClass=univentionPolicyDhcpNetbios)'
    '(objectClass=univentionPolicyDhcpRouting)'
    '(objectClass=univentionPolicyDhcpScope)'
    '(objectClass=univentionPolicyDhcpStatements)'
    '(objectClass=univentionDhcpPool)'
    '(cn=dhcp)'
    '(objectClass=domain)'
    ')'
)


def handler(dn: str, new: dict[str, list[bytes]], old: dict[str, list[bytes]]) -> None:
    pass


def postrun() -> None:
    if ucr.is_true("dhcpd/autostart", False):
        if ucr.is_true('dhcpd/restart/listener', False):
            ud.debug(ud.LISTENER, ud.INFO, 'DHCP: Restarting server')
            try:
                run('/bin/systemctl', ['systemctl', 'try-reload-or-restart', '--', 'isc-dhcp-server.service'], uid=0)
            except Exception as ex:
                ud.debug(ud.ADMIN, ud.WARN, 'The restart of the DHCP server failed: %s' % (ex,))
        else:
            ud.debug(ud.ADMIN, ud.INFO, 'DHCP: the automatic restart of the dhcp server by the listener is disabled. Set dhcpd/restart/listener to true to enable this option.')
    else:
        ud.debug(ud.LISTENER, ud.INFO, 'DHCP: dcpd disabled in config_registry - not started.')
