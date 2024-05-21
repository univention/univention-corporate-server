#!/usr/share/ucs-test/runner pytest-3
## desc: Test the UMC network functionality
## bugs: [34622]
## roles:
##  - domaincontroller_master
##  - domaincontroller_backup
## exposure: dangerous

from __future__ import annotations

from typing import Any

import pytest

from univention.config_registry.interfaces import Interfaces
from univention.lib.umc import BadRequest
from univention.testing.strings import random_username

from umc import UDMModule


class UMCNetworkFunctionality(UDMModule):

    def __init__(self) -> None:
        """Test Class constructor"""
        super().__init__()
        self.ldap_base = self.ucr['ldap/base']

        net = Interfaces(self.ucr).get_default_ipv4_address().network
        self.network_addr = net.network_address.exploded
        self.network_name = f'umc_test_network_{random_username(6)}'
        self.network_subnet, _, _ = self.network_addr.rpartition(".")
        self.ip_range: tuple[str, str] = (f"{self.network_subnet}.50", f"{self.network_subnet}.70")
        self.computer_name = f'umc_test_computer_{random_username(6)}'

        self.network_dn = ''

    def create_network(
        self,
        netmask: str = "24",
        dns_forward: str = "",
        dns_reverse: str = "",
        dhcp_entry: str = "",
    ) -> None:
        """
        Makes a 'udm/add' request to create a network with a
        number of given options
        """
        options = [{"object": {"dnsEntryZoneReverse": dns_reverse,
                               "netmask": netmask,
                               "dhcpEntryZone": dhcp_entry,
                               "name": self.network_name,
                               "dnsEntryZoneForward": dns_forward,
                               "ipRange": [list(self.ip_range)],
                               "network": self.network_addr,
                               "$policies$": {}},
                    "options": {"container": "cn=networks," + self.ldap_base,
                                "objectType": "networks/network"}}]

        request_result = self.request("udm/add", options, "networks/network")
        assert request_result[0].get("success")
        self.network_dn = request_result[0].get('$dn$')

    def query_dhcp_services(self) -> list[dict[str, Any]]:
        """Makes a 'udm/query' request to get the DHCP services available"""
        options = {"superordinate": "None",
                   "objectType": "dhcp/dhcp",
                   "objectProperty": "None",
                   "objectPropertyValue": "",
                   "hidden": True}
        return self.request('udm/query', options, "dhcp/dhcp")

    def get_network_config(self, increase_counter: bool = True) -> dict[str, Any]:
        """
        Makes a 'udm/network' request to get the network configuration
        with the next free IP address
        """
        options = {"networkDN": self.network_dn,
                   "increaseCounter": increase_counter}
        return self.request("udm/network", options)

    def get_network_choices(self, syntax) -> list[dict[str, Any]]:
        """Returns result of 'udm/syntax/choices' for a given 'syntax' request."""
        options = {"syntax": syntax}
        return self.request("udm/syntax/choices", options, "computers/computer")

    def check_dns_dhcp_in_choices(self, syntax: str, name: str) -> bool:
        """
        Makes a 'udm/syntax/chioces' request with given 'syntax'
        options to get the dns or dhcp available and returns True when
        dns/dhcp with a given 'name' is found among them.
        """
        return any(name in choice['label'] for choice in self.get_network_choices(syntax))

    def modify_network_ip_range(self) -> None:
        """Makes a 'udm/put' request to modify network ipRange"""
        options = [{"object": {"dnsEntryZoneReverse": "",
                               "dhcpEntryZone": "",
                               "dnsEntryZoneForward": "",
                               "ipRange": [list(self.ip_range)],
                               "$dn$": self.network_dn},
                    "options": None}]
        self.modify_object(options, "networks/network")

    def query_networks(self) -> list[dict[str, Any]]:
        """Makes a 'udm/query' request for networks and returns result"""
        options = {"container": "all",
                   "objectType": "networks/network",
                   "objectProperty": "None",
                   "objectPropertyValue": "",
                   "hidden": True}
        return self.request('udm/query', options, 'networks/network')

    def run_dns_dhcp_choices_checks(self) -> None:
        """
        Checks if the correct options are reported for 'DNS_ForwardZone'
        and 'dhcpService' configurations
        """
        domain_name = self.ucr.get('domainname')
        print(f"\nChecking if DNS forward zone {domain_name} is reported in choices for {self.computer_name} computer")
        assert self.check_dns_dhcp_in_choices("DNS_ForwardZone", domain_name)

        print(f"\nChecking if a DHCP service is reported in choices for {self.computer_name} computer")
        dhcp_services = self.query_dhcp_services()
        if dhcp_services:
            dhcp_service_name = dhcp_services[0]['name']
            assert self.check_dns_dhcp_in_choices("dhcpService", dhcp_service_name)
        else:
            print("\nCheck skipped, since no DHCP services in the domain were found...")

    def run_address_reservation_checks(self) -> None:
        """
        Checks if ip addresses ending with .0, .1 and .254 are not
        returned as an option for computer network configuration
        """
        assert self.client is not None
        self.ip_range = (f'{self.network_subnet}.1', f'{self.network_subnet}.254')
        print(f"\nChecking that '*.0' and '*.1' addresses are not retrieved as an option for network configuration after changing {self.network_name} network ip range to {self.ip_range}")
        self.modify_network_ip_range()
        network_config = self.get_network_config()
        assert network_config.get('ip') not in {f'{self.network_subnet}.0', f'{self.network_subnet}.1'}

        self.ip_range = (f'{self.network_subnet}.254', f'{self.network_subnet}.254')
        print(f"\nChecking that '*.254' address is not retrieved as an option for network configuration after changing {self.network_name} network ip range to {self.ip_range}")
        self.modify_network_ip_range()
        options = {"networkDN": self.network_dn,
                   "increaseCounter": True}
        with pytest.raises(BadRequest, match=r".*(?:Fehler bei der automatischen IP Adresszuweisung|Failed to automatically assign an IP address).*"):
            self.client.umc_command('udm/network', options)

    def run_checks_with_computers(self) -> None:
        """
        Creates a computer in a test network and after tries to create
        one more computer in the same network where no more free ip
        addresses are left
        """
        print(f"\nCreating a test computer {self.computer_name} in the test network {self.network_name}")
        assert any(self.network_name in network['id'] for network in self.get_network_choices("network"))

        network_config = self.get_network_config()
        creation_result = self.create_computer(self.computer_name, [network_config['ip']], network_config['dnsEntryZoneForward'], network_config['dnsEntryZoneReverse'])
        assert creation_result[0].get("success")

        print(f"\nAttempting to create another test computer {self.computer_name}_2 in the test network {self.network_name} where no more free ip addresses are left")
        creation_result = self.create_computer(f'{self.computer_name}_2', [network_config['ip']], network_config['dnsEntryZoneForward'], network_config['dnsEntryZoneReverse'])
        assert not creation_result[0].get("success")
        assert not self.check_obj_exists(f'{self.computer_name}_2', "computers/computer")

    def run_modification_checks(self) -> None:
        """
        Creates a network for the test, modifies it and
        checks if the modification was done correctly
        """
        print(f"\nCreating a network for the test with a name {self.network_name} and ip range {self.ip_range}")
        assert self.check_obj_exists(self.network_name, "networks/network")

        self.ip_range = (f'{self.network_subnet}.70', f'{self.network_subnet}.70')
        print(f"\nModifing and checking test network {self.network_name} ip range to {self.ip_range}")
        self.modify_network_ip_range()
        network = self.get_object([self.network_dn], "networks/network")
        assert list(self.ip_range) in network[0]["ipRange"]

    def main(self) -> None:
        """A method to test the UMC network functionality"""
        try:
            self.create_network()
            self.run_modification_checks()
            self.run_checks_with_computers()
            self.run_address_reservation_checks()
            self.run_dns_dhcp_choices_checks()
        finally:
            print("\nRemoving created test objects (if any):")
            if self.check_obj_exists(f'{self.computer_name}_2', "computers/computer"):
                self.delete_obj(f'{self.computer_name}_2', "computers", "computers/computer")
            if self.check_obj_exists(self.computer_name, "computers/computer"):
                self.delete_obj(self.computer_name, "computers", "computers/computer")
            if self.check_obj_exists(self.network_name, "networks/network"):
                self.delete_obj(self.network_name, "networks", "networks/network")


@pytest.fixture(scope="module")
def umc() -> UMCNetworkFunctionality:
    self = UMCNetworkFunctionality()
    self.create_connection_authenticate()
    return self


@pytest.mark.parametrize("netmask,ip_range,network", [
    ("foo", ("foo", "bar"), "foo"),
    ("12345", ("10.20.25.256", "10.20.25.257"), "12345"),
    ("256", ("10.20.256.2", "10.20.25.2"), "10.20.25."),
])
def test_syntax(netmask: str, ip_range: tuple[str, str], network: str, umc: UMCNetworkFunctionality) -> None:
    """
    Makes a 'udm/validate' request with non-valid values and
    checks if they were reported as 'valid'==false
    """
    options = {"objectType": "networks/network",
               "properties": {"netmask": netmask,
                              "ipRange": [list(ip_range)],
                              "network": network}}

    for prop in umc.request('udm/validate', options, "networks/network"):
        # Workaround for answers that have lists inside:
        try:
            assert True not in prop.get('valid')
        except TypeError:
            assert not prop.get('valid')


def test_basic_checks(umc: UMCNetworkFunctionality) -> None:
    """
    Makes a network query request and checks it for all
    default fields presence
    """
    for network in umc.query_networks():
        assert '$dn$' in network
        assert 'name' in network
        assert '$childs$' in network
        assert 'labelObjectType' in network
        assert 'objectType' in network
        assert 'path' in network


def test_umc(umc: UMCNetworkFunctionality) -> None:
    umc.main()
