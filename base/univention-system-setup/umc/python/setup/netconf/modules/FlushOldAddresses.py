#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# SPDX-FileCopyrightText: 2024 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from univention.management.console.modules.setup.netconf import Phase


class PhaseFlushOldAddresses(Phase):
    """Flush old interfaces to remove old addresses."""

    priority = 55

    def pre(self) -> None:
        super(PhaseFlushOldAddresses, self).pre()
        for _name, iface in self.changeset.old_interfaces.all_interfaces:
            self.call(["ip", "addr", "flush", iface.name])
