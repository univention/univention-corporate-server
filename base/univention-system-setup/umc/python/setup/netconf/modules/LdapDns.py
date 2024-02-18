#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# SPDX-FileCopyrightText: 2024 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from typing import List

from univention import ipcalc
from univention.management.console.modules.setup.netconf.common import AddressMap
from univention.management.console.modules.setup.netconf.conditions import Executable, Ldap


class PhaseLdapDns(AddressMap, Ldap, Executable):
    """Create reverse DNS zones and add pointer records for host."""

    priority = 46
    executable = "/usr/share/univention-directory-manager-tools/univention-dnsedit"

    def post(self) -> None:
        self._create_reverse_dns_ipv4()
        self._create_reverse_dns_ipv6()

    def _create_reverse_dns_ipv4(self) -> None:
        for ipv4 in set(self.changeset.new_ipv4s) - set(self.changeset.old_ipv4s):
            self.call([
                self.executable,
                "--binddn", self.binddn,
                "--bindpwd", self.bindpwd,
                "--ignore-exists",
                "--reverse", ipcalc.calculate_ipv4_reverse(ipv4),
                "add", "zone",
            ] + self._soa())
            self.call([
                self.executable,
                "--binddn", self.binddn,
                "--bindpwd", self.bindpwd,
                "--ignore-exists",
                "--reverse", ipcalc.calculate_ipv4_reverse(ipv4),
                "add", "ptr",
                ipcalc.calculate_ipv4_pointer(ipv4),
                "%(hostname)s.%(domainname)s." % self.changeset.ucr,
            ])

    def _create_reverse_dns_ipv6(self) -> None:
        for ipv6 in set(self.changeset.new_ipv6s) - set(self.changeset.old_ipv6s):
            self.call([
                self.executable,
                "--binddn", self.binddn,
                "--bindpwd", self.bindpwd,
                "--ignore-exists",
                "--reverse", ipcalc.calculate_ipv6_reverse(ipv6),
                "add", "zone",
            ] + self._soa())
            self.call([
                self.executable,
                "--binddn", self.binddn,
                "--bindpwd", self.bindpwd,
                "--ignore-exists",
                "--reverse", ipcalc.calculate_ipv6_reverse(ipv6),
                "add", "ptr",
                ipcalc.calculate_ipv6_pointer(ipv6),
                "%(hostname)s.%(domainname)s." % self.changeset.ucr,
            ])

    def _soa(self) -> List[str]:
        return [
            "root@%(domainname)s." % self.changeset.ucr,
            "1",
            "%d" % (8 * 60 * 60,),
            "%d" % (3 * 60 * 60,),
            "%d" % (7 * 24 * 60 * 60,),
            "%d" % (1 + 30 * 60 * 60,),
            "%(hostname)s.%(domainname)s." % self.changeset.ucr,
        ]
