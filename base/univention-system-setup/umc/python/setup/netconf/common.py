# SPDX-FileCopyrightText: 2004-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""Univention Setup: network configuration abstract common classes"""

import os
from abc import ABCMeta
from ipaddress import IPv4Interface, IPv4Network, IPv6Interface, IPv6Network

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
        super().pre()
        self.call(["systemctl", "stop", self.service])

    def post(self) -> None:
        super().pre()
        self.call(["systemctl", "start", self.service])


class AddressMap(AddressChange, metaclass=ABCMeta):
    """Helper to provide a mapping from old addresses to new addresses."""

    def __init__(self, changeset: ChangeSet) -> None:
        super().__init__(changeset)
        self.old_primary, self.new_primary = (
            iface.get_default_ip_address()
            for iface in (
                self.changeset.old_interfaces,
                self.changeset.new_interfaces,
            )
        )
        self.net_changes = self._map_ip()
        self.ip_mapping = self._get_address_mapping()

    def _map_ip(self) -> dict[IPv4Interface | IPv6Interface, IPv4Interface | IPv6Interface | None]:
        ipv4_changes = self.ipv4_changes()
        ipv6_changes = self.ipv6_changes()
        net_changes: dict[IPv4Interface | IPv6Interface, IPv4Interface | IPv6Interface | None] = {}
        net_changes.update(ipv4_changes)  # type: ignore
        net_changes.update(ipv6_changes)  # type: ignore
        return net_changes

    def ipv4_changes(self) -> dict[IPv4Interface, IPv4Interface | None]:
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

    def ipv6_changes(self) -> dict[IPv6Interface, IPv6Interface | None]:
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

    def _get_address_mapping(self) -> dict[str, str | None]:
        mapping = {
            str(old_ip.ip): str(new_ip.ip) if new_ip else None
            for (old_ip, new_ip) in self.net_changes.items()
        }
        return mapping


class LdapChange(AddressChange, Ldap, metaclass=ABCMeta):
    """Helper to provide access to LDAP through UDM."""

    def __init__(self, changeset: ChangeSet) -> None:
        super().__init__(changeset)
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


def convert_udm_subnet_to_network(subnet: str) -> IPv4Network | IPv6Network:
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
    return IPv4Network("%s/%d" % (address, prefix_length), False)


def convert_udm_subnet_to_ipv6_network(subnet: str) -> IPv6Network:
    prefix = subnet.replace(":", "")
    count = len(prefix)
    assert 1 <= count <= 32
    prefix_length = 4 * count
    address = subnet
    if count <= 28:
        address += "::"
    return IPv6Network("%s/%d" % (address, prefix_length), False)
