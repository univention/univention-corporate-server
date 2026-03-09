#!/usr/bin/python3
# SPDX-FileCopyrightText: 2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from ipaddress import IPv4Network

from univention.config_registry import interfaces, ucr_live as ucr
from univention.lib.i18n import Translation
from univention.management.console.modules.diagnostic import Instance, Warning  # noqa: A004


_ = Translation('univention-management-console-module-diagnostic').translate

title = _('Docker bridge network conflicts with host network')
description = _('No conflict between the Docker bridge network and host network interfaces detected.')

run_descr = ['Checks if the Docker bridge network (docker0) overlaps with any host network interface']


def run(_umc_instance: Instance) -> None:
    bip_net_var = 'docker/daemon/default/opts/bip'
    bip = ucr.get(bip_net_var, '172.17.42.1/16')
    docker0_net = IPv4Network(bip, strict=False)

    conflicts = []
    for name, iface in interfaces.Interfaces().ipv4_interfaces:
        if 'address' in iface and 'netmask' in iface:
            try:
                host_net = IPv4Network(f'{iface["address"]}/{iface["netmask"]}', strict=False)
            except ValueError:
                continue
            if host_net.overlaps(docker0_net):
                conflicts.append((name, host_net))

    if conflicts:
        details = '\n'.join(
            _('- Interface %s (%s) overlaps with Docker bridge %s') % (name, net, docker0_net)
            for name, net in conflicts
        )
        msg = '\n'.join([
            _('The Docker bridge network (%s, UCR variable %s) overlaps with the following host network interfaces:') % (docker0_net, bip_net_var),
            '',
            details,
            '',
            _('Please set %s to a non-overlapping network via {ucr} and restart the system.') % bip_net_var,
        ])
        raise Warning(msg, umc_modules=[{'module': 'ucr'}])


if __name__ == '__main__':
    from univention.management.console.modules.diagnostic import main

    main()
