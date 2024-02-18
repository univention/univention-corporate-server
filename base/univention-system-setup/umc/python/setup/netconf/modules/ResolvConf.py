#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# SPDX-FileCopyrightText: 2024 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from univention.config_registry.frontend import handler_commit
from univention.management.console.modules.setup.netconf import SkipPhase
from univention.management.console.modules.setup.netconf.conditions import Dhcp


class PhaseResolvConv(Dhcp):
    """Commit /etc/resolv.conf if no more DHCP is used."""

    priority = 75

    def check(self) -> None:
        super(PhaseResolvConv, self).check()
        if self.new_dhcps:
            raise SkipPhase("Still using DHCP")

    def post(self) -> None:
        super(PhaseResolvConv, self).post()
        self.logger.info("Committing /etc/resolv.conf...")
        if not self.changeset.no_act:
            handler_commit(["/etc/resolv.conf"])
