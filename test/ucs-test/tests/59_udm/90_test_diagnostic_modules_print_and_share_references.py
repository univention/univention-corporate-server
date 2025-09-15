#!/usr/share/ucs-test/runner pytest-3 -s -v
## desc: Check diagnostic module for consistent references in share/* objects (Bug #32192)
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
DIAGNOSTIC_MODULE = "20_check_share_references"


@pytest.mark.parametrize(
    "fileserver,success_expected",
    [
        [f"{uts.random_name()}.{ucr.get('domainname')}", False],
        [f"{ucr.get('hostname')}.{ucr.get('domainname')}", True],
    ],
    ids=["invalid", "valid"],
)
def test_invalid_shares_share_detection(
    udm,
    test_diagnostic_module,
    fileserver,
    success_expected,
) -> None:
    """Check that shares/share objects with invalid "host" are identified."""
    udm.create_object(
        "shares/share",
        name=uts.random_name(),
        host=fileserver,
        path=f"/var/tmp/pytest-{uts.random_name()}.shares",
        wait_for=WAIT_FOR,
    )
    test_diagnostic_module(DIAGNOSTIC_MODULE, success_expected=success_expected)


@pytest.mark.parametrize(
    "spool_host,success_expected",
    [
        [f"{uts.random_name()}.{ucr.get('domainname')}", False],
        [f"{ucr.get('hostname')}.{ucr.get('domainname')}", True],
    ],
    ids=["invalid", "valid"],
)
def test_invalid_shares_printer_detection(
    udm,
    test_diagnostic_module,
    spool_host,
    success_expected,
) -> None:
    """Check that shares/printer objects with invalid "spoolHost" are identified."""
    udm.create_object(
        "shares/printer",
        name=uts.random_name(),
        spoolHost=spool_host,
        uri="cups-pdf:/",
        producer="cn=Alps,cn=cups,cn=univention,dc=ucs,dc=test",
        model="foomatic-db-compressed-ppds:0/ppd/foomatic-ppd/Alps-MD-1000-md2k.ppd",
        wait_for=WAIT_FOR,
    )
    test_diagnostic_module(DIAGNOSTIC_MODULE, success_expected=success_expected)


@pytest.mark.parametrize(
    "spool_host,success_expected",
    [
        [f"{uts.random_name()}.{ucr.get('domainname')}", False],
        [f"{ucr.get('hostname')}.{ucr.get('domainname')}", True],
    ],
    ids=["invalid", "valid"],
)
def test_invalid_shares_printergroup_detection(
    udm,
    test_diagnostic_module,
    spool_host,
    success_expected,
) -> None:
    """Check that shares/printer objects with invalid "spoolHost" are identified."""
    printer_name = uts.random_name()
    udm.create_object(
        "shares/printer",
        name=printer_name,
        spoolHost=spool_host,
        uri="cups-pdf:/",
        producer="cn=Alps,cn=cups,cn=univention,dc=ucs,dc=test",
        model="foomatic-db-compressed-ppds:0/ppd/foomatic-ppd/Alps-MD-1000-md2k.ppd",
        wait_for=WAIT_FOR,
    )
    udm.create_object(
        "shares/printergroup",
        name=uts.random_name(),
        spoolHost=spool_host,
        groupMember=printer_name,
        wait_for=WAIT_FOR,
    )
    test_diagnostic_module(DIAGNOSTIC_MODULE, success_expected=success_expected)
