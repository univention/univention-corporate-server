#!/usr/share/ucs-test/runner pytest-3 -s -v
## desc: Check diagnostic module for consistent references in DNS SRV records (Bug #32192)
## tags: [udm,udm-dns,bug-32192]
## roles: [domaincontroller_master]
## exposure: careful
## packages:
##   - univention-config
##   - univention-directory-manager-tools

import re
from collections.abc import Iterator

import pytest

import univention.testing.strings as uts
from univention.config_registry import ucr


WAIT_FOR = True  # set to False to get faster results during test development
DIAGNOSTIC_RE = re.compile(
    r"(?:^ran ([\d\w]*) successfully.$)|(?:#+ Start ([\d\w]*) #+)\n(.*)\n(?:#+ End (?:\2) #+)",
    flags=re.M | re.S,
)
DIAGNOSTIC_MODULE = "20_check_srv_records"


@pytest.fixture
def create_forward_zone(udm) -> Iterator[str]:
    """Create a new DNS forward zone"""
    forward_zone_name = "%s.%s" % (
        uts.random_name(),
        ucr.get("domainname"),
    )
    forward_zone_dn = udm.create_object(
        "dns/forward_zone",
        zone=forward_zone_name,
        nameserver="%(hostname)s.%(domainname)s" % ucr,
        wait_for=WAIT_FOR,
    )
    return forward_zone_dn


def create_srv_record(udm, zone, target):
    udm.create_object(
        "dns/srv_record",
        name="pytest tcp pytestsuffix",
        location=f"10 20 65000 {target}",
        zonettl=3600,
        superordinate=zone,
        wait_for=WAIT_FOR,
    )


@pytest.mark.parametrize(
    "target",
    [
        ucr.get("hostname"),
        uts.random_name(),
        "%s.%s" % (uts.random_name(), uts.random_dns_record()),
        "%s.%s" % (ucr.get("hostname"), ucr.get("domainname")),
    ],
    ids=["hostname", "random_hostname", "random_fqdn", "local_fqdn"],
)
def test_invalid_target(udm, test_diagnostic_module, create_forward_zone, target) -> None:
    """Check that invalid targets in SRV records are identified."""
    create_srv_record(udm, create_forward_zone, target)
    test_diagnostic_module(DIAGNOSTIC_MODULE, success_expected=False)


def test_invalid_cname(udm, test_diagnostic_module, create_forward_zone) -> None:
    """Check that invalid CNAME targets in SRV records are identified."""
    alias_name = uts.random_name()
    alias_fqdn = f'{alias_name}.{ucr.get("domainname")}.'
    udm.create_object(
        "dns/alias",
        name=alias_name,
        cname=f"{ucr.get('hostname')}.{ucr.get('domainname')}.",
        superordinate=f"zoneName={ucr.get('domainname')},cn=dns,{ucr.get('ldap/base')}",
        wait_for=WAIT_FOR,
    )
    create_srv_record(udm, create_forward_zone, alias_fqdn)
    test_diagnostic_module(DIAGNOSTIC_MODULE, success_expected=False)


def test_valid_records(test_diagnostic_module) -> None:
    """By default, each UCS environment has multiple valid SRV records. So just run the test."""
    test_diagnostic_module(DIAGNOSTIC_MODULE, success_expected=True)
