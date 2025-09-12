#!/usr/share/ucs-test/runner pytest-3 -s -v
## desc: Check diagnostic module for consistent references in DNS zones (Bug #32192)
## tags: [udm,udm-dns,bug-32192]
## roles: [domaincontroller_master]
## exposure: careful
## packages:
##   - univention-config
##   - univention-directory-manager-tools

import re

import pytest

import univention.testing.strings as uts
from univention.config_registry import ucr


WAIT_FOR = True  # set to False to get faster results during test development
DIAGNOSTIC_RE = re.compile(
    r"(?:^ran ([\d\w]*) successfully.$)|(?:#+ Start ([\d\w]*) #+)\n(.*)\n(?:#+ End (?:\2) #+)",
    flags=re.M | re.S,
)
DIAGNOSTIC_MODULE = "20_check_nameservers"


def create_forward_zone(udm, nameservers: list[str]) -> None:
    """Create a new DNS forward zone with specified nameservers."""
    forward_zone_name = "%s.%s" % (uts.random_name(), ucr.get("domainname"))
    udm.create_object(
        "dns/forward_zone",
        zone=forward_zone_name,
        nameserver=nameservers,
        wait_for=WAIT_FOR,
    )


def create_reverse_zone(udm, nameservers: list[str]) -> None:
    """Create a new DNS reverse zone with specified nameservers"""
    udm.create_object(
        "dns/reverse_zone",
        subnet=uts.random_subnet(),
        nameserver=nameservers,
        wait_for=WAIT_FOR,
    )


@pytest.mark.parametrize(
    "nameservers",
    [
        # random hostname
        [uts.random_name()],
        # random hostname and valid FQDN in zone
        [uts.random_name(), f"{ucr.get('hostname')}.{ucr.get('domainname')}."],
        # random FQDN in zone
        [f"{uts.random_name()}.{ucr.get('domainname')}."],
        # random FQDN in zone + valid FQDN in zone
        [
            f"{uts.random_name()}.{ucr.get('domainname')}.",
            f"{ucr.get('hostname')}.{ucr.get('domainname')}.",
        ],
        # invalid FQDN
        ["this.host.does.not.exist.univention.de."],
    ],
)
def test_forward_zone_with_invalid_ns_record(
    udm,
    test_diagnostic_module,
    nameservers: list[str],
) -> None:
    """Check that DNS forward zone errors are identified."""
    create_forward_zone(udm, nameservers)
    test_diagnostic_module(DIAGNOSTIC_MODULE, success_expected=False)


@pytest.mark.parametrize(
    "create_zone",
    [
        create_forward_zone,
        create_reverse_zone,
    ],
    ids=["forward_zone", "reverse_zone"],
)
def test_zones_with_invalid_cname_in_ns_record(udm, test_diagnostic_module, create_zone) -> None:
    """Check that DNS forward/reverse zones with invalid CNAME as nameserver are correctly identified."""
    alias_name = uts.random_name()
    udm.create_object(
        "dns/alias",
        name=alias_name,
        cname=f"{ucr.get('hostname')}.{ucr.get('domainname')}.",
        superordinate=f"zoneName={ucr.get('domainname')},cn=dns,{ucr.get('ldap/base')}",
        wait_for=WAIT_FOR,
    )
    create_zone(udm, [f'{alias_name}.{ucr.get("domainname")}.'])
    test_diagnostic_module(DIAGNOSTIC_MODULE, success_expected=False)


@pytest.mark.parametrize(
    "nameservers",
    [
        # random hostname
        [uts.random_name()],
        # random hostname and valid FQDN in zone
        [uts.random_name(), f"{ucr.get('hostname')}.{ucr.get('domainname')}."],
        # random FQDN in zone
        [f"{uts.random_name()}.{ucr.get('domainname')}."],
        # random FQDN in zone + valid FQDN in zone
        [
            f"{uts.random_name()}.{ucr.get('domainname')}.",
            f"{ucr.get('hostname')}.{ucr.get('domainname')}.",
        ],
        # invalid FQDN
        ["this.host.does.not.exist.univention.de."],
    ],
)
def test_dns_reverse_zones_with_invalid_domain(udm, test_diagnostic_module, nameservers) -> None:
    create_reverse_zone(udm, nameservers)
    test_diagnostic_module(DIAGNOSTIC_MODULE, success_expected=False)


def test_dns_forward_zones_with_valid_ns_record(udm, test_diagnostic_module) -> None:
    create_forward_zone(udm, [f"{ucr.get('hostname')}.{ucr.get('domainname')}."])
    test_diagnostic_module(DIAGNOSTIC_MODULE, success_expected=True)
