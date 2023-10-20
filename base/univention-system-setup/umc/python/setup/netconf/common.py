# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2004-2023 Univention GmbH
#
# https://www.univention.de/
#
# All rights reserved.
#
# The source code of this program is made available
# under the terms of the GNU Affero General Public License version 3
# (GNU AGPL V3) as published by the Free Software Foundation.
#
# Binary versions of this program provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention and not subject to the GNU AGPL V3.
#
# In the case you use this program under the terms of the GNU AGPL V3,
# the program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <https://www.gnu.org/licenses/>.

"""Univention Setup: network configuration abstract common classes"""

import os
from abc import ABCMeta
from ipaddress import IPv4Interface, IPv4Network, IPv6Interface, IPv6Network
from typing import Dict, Optional, Union

from univention.admin import uldap
from univention.management.console.modules.setup.netconf import ChangeSet
from univention.management.console.modules.setup.netconf.conditions import AddressChange, Executable, Ldap


class RestartService(Executable, metaclass=ABCMeta):
    """Helper to restart a single service."""

    service = ""
    PREFIX = "/etc/init.d"

    @property
    def executable(self) -> str:
        return os.path.join(self.PREFIX, self.service)

    def pre(self) -> None:
        super(RestartService, self).pre()
        self.call(["systemctl", "stop", self.service])

    def post(self) -> None:
        super(RestartService, self).pre()
        self.call(["systemctl", "start", self.service])


class AddressMap(AddressChange, metaclass=ABCMeta):
    """Helper to provide a mapping from old addresses to new addresses."""

    def __init__(self, changeset: ChangeSet) -> None:
        super(AddressMap, self).__init__(changeset)
        self.old_primary, self.new_primary = (
            iface.get_default_ip_address()
            for iface in (
                self.changeset.old_interfaces,
                self.changeset.new_interfaces,
            )
        )
        self.net_changes = self._map_ip()
        self.ip_mapping = self._get_address_mapping()

    def _map_ip(self) -> Dict[Union[IPv4Interface, IPv6Interface], Union[None, IPv4Interface, IPv6Interface]]:
        ipv4_changes = self.ipv4_changes()
        ipv6_changes = self.ipv6_changes()
        net_changes: Dict[Union[IPv4Interface, IPv6Interface], Union[None, IPv4Interface, IPv6Interface]] = {}
        net_changes.update(ipv4_changes)  # type: ignore
        net_changes.update(ipv6_changes)  # type: ignore
        return net_changes

    def ipv4_changes(self) -> Dict[IPv4Interface, Optional[IPv4Interface]]:
        ipv4s = {
            name: iface.ipv4_address()
            for name, iface in self.changeset.new_interfaces.ipv4_interfaces
        }
        default = self.changeset.new_interfaces.get_default_ipv4_address()
        mapping = {}
        for name, iface in self.changeset.old_interfaces.ipv4_interfaces:
            old_addr = iface.ipv4_address()
            new_addr = ipv4s.get(name, default)
            if new_addr is None or old_addr.ip != new_addr.ip:
                mapping[old_addr] = new_addr
        return mapping

    def ipv6_changes(self) -> Dict[IPv6Interface, Optional[IPv6Interface]]:
        ipv6s = {
            (iface.name, name): iface.ipv6_address(name)
            for (iface, name) in self.changeset.new_interfaces.ipv6_interfaces
        }
        default = self.changeset.new_interfaces.get_default_ipv6_address()
        mapping = {}
        for iface, name in self.changeset.old_interfaces.ipv6_interfaces:
            old_addr = iface.ipv6_address(name)
            new_addr = ipv6s.get((iface.name, name), default)
            if new_addr is None or old_addr.ip != new_addr.ip:
                mapping[old_addr] = new_addr
        return mapping

    def _get_address_mapping(self) -> Dict[str, Optional[str]]:
        mapping = {
            str(old_ip.ip): str(new_ip.ip) if new_ip else None
            for (old_ip, new_ip) in self.net_changes.items()
        }
        return mapping


class LdapChange(AddressChange, Ldap, metaclass=ABCMeta):
    """Helper to provide access to LDAP through UDM."""

    def __init__(self, changeset: ChangeSet) -> None:
        super(LdapChange, self).__init__(changeset)
        self.ldap = None
        self.position = None

    def open_ldap(self) -> None:
        ldap_host = self.changeset.ucr["ldap/master"]
        ldap_base = self.changeset.ucr["ldap/base"]
        self.ldap = uldap.access(
            host=ldap_host,
            base=ldap_base,
            binddn=self.binddn,
            bindpw=self.bindpwd,
        )
        self.position = uldap.position(ldap_base)


def convert_udm_subnet_to_network(subnet: str) -> Union[IPv4Network, IPv6Network]:
    if ":" in subnet:
        return convert_udm_subnet_to_ipv6_network(subnet)
    else:
        return convert_udm_subnet_to_ipv4_network(subnet)


def convert_udm_subnet_to_ipv4_network(subnet: str) -> IPv4Network:
    octets = subnet.split('.')
    count = len(octets)
    assert 1 <= count <= 4
    prefix_length = 8 * count
    octets += ["0"] * (4 - count)
    address = '.'.join(octets)
    return IPv4Network(u"%s/%d" % (address, prefix_length), False)


def convert_udm_subnet_to_ipv6_network(subnet: str) -> IPv6Network:
    prefix = subnet.replace(":", "")
    count = len(prefix)
    assert 1 <= count <= 32
    prefix_length = 4 * count
    address = subnet
    if count <= 28:
        address += "::"
    return IPv6Network(u"%s/%d" % (address, prefix_length), False)
