# SPDX-FileCopyrightText: 2004-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""config registry module for the network interfaces."""

import re
from subprocess import call


RE_IFACE = re.compile(r'^interfaces/([^/]+)/((?:ipv6/([^/]+)/)?.*)$')
SKIP = {'interfaces/restart/auto'}
PRIMARY = 'interfaces/primary'
GATEWAYS = {'gateway', 'ipv6/gateway'}


def _common(ucr, changes, command):
    """Run command on changed interfaces."""
    if not ucr.is_true('interfaces/restart/auto', True):
        return
    interfaces = set()
    if GATEWAYS & set(changes):
        # Restart all interfaces on gateway change
        interfaces.add('-a')
    else:
        # Restart both old and new primary interfaces
        if PRIMARY in changes:
            interfaces |= {_ for _ in changes[PRIMARY] if _}
        # Collect changed interfaces
        for key in changes.keys():
            if key in SKIP:
                continue
            match = RE_IFACE.match(key)
            if not match:
                continue
            iface, _subkey, _ipv6_name = match.groups()
            interfaces.add(iface.replace('_', ':'))
    # Shutdown changed interfaces
    for iface in interfaces:
        call((command, iface))


def preinst(ucr, changes):
    """Pre run handler to shutdown changed interfaces."""
    _common(ucr, changes, 'ifdown')


def postinst(ucr, changes):
    """Post run handler to start changed interfaces."""
    _common(ucr, changes, 'ifup')
