#!/usr/share/ucs-test/runner pytest-3 -s -v
## desc: Check diagnostic module for checking for resolvable URLs in portals/entry objects (Bug #32192)
## tags: [udm,udm-dns,bug-32192]
## roles: [domaincontroller_master]
## exposure: careful
## packages:
##   - univention-config
##   - univention-directory-manager-tools

import re

import pytest

import univention.testing.strings as uts
from univention.config_registry import ucr_live as ucr


WAIT_FOR = True  # set to False to get faster results during test development
DIAGNOSTIC_RE = re.compile(
    r"(?:^ran ([\d\w]*) successfully.$)|(?:#+ Start ([\d\w]*) #+)\n(.*)\n(?:#+ End (?:\2) #+)",
    flags=re.M | re.S,
)
DIAGNOSTIC_MODULE = "24_portal_entries"


@pytest.mark.parametrize(
    "url,success_expected",
    [
        ["/univention/portal/", True],
        ["/univention/portal/?some=query&but=unused", True],
        ["http://10.20.30.40/univention/portal/", True],
        ["https://123.45.67.089/univention/portal/?some=query&but=unused", True],
        [f"http://{uts.random_name()}/univention/", False],
        [f"http://{uts.random_name()}.{ucr.get('domainname')}", False],
        [f"https://{uts.random_name()}.{ucr.get('domainname')}/univention-portal/?with=query", False],
        [f"https://{ucr.get('hostname')}", True],
        [f"http://{ucr.get('hostname')}.{ucr.get('domainname')}", True],
        [f"https://{ucr.get('hostname')}.{ucr.get('domainname')}/univention/portal/?with=query", True],
    ],
)
def test_invalid_portal_entries(
    udm,
    test_diagnostic_module,
    url,
    success_expected,
) -> None:
    """Check that portals/entry objects with invalid host part are identified."""
    udm.create_object(
        "portals/entry",
        position=f"cn=entry,cn=portals,cn=univention,{ucr.get('ldap/base')}",
        name=uts.random_name(),
        displayName=f"de_DE {uts.random_string(20)}",
        description=f"de_DE {uts.random_string(50)}",
        activated="TRUE",
        anonymous="TRUE",
        linkTarget="newwindow",
        link=[f"de_DE {url}", f"en_US {url}"],
        wait_for=WAIT_FOR,
    )
    test_diagnostic_module(DIAGNOSTIC_MODULE, success_expected=success_expected)


def test_ignore_list(ucr, udm, test_diagnostic_module) -> None:
    """Check that the ignore list for portals/entry objects is working."""
    obj_name = uts.random_name()
    udm.create_object(
        "portals/entry",
        position=f"cn=entry,cn=portals,cn=univention,{ucr.get('ldap/base')}",
        name=obj_name,
        displayName=f"de_DE {uts.random_string(20)}",
        description=f"de_DE {uts.random_string(50)}",
        activated="TRUE",
        anonymous="TRUE",
        linkTarget="newwindow",
        link=["de_DE https://does.not.exist/univention/portal/"],
        wait_for=WAIT_FOR,
    )
    ucr.handler_set([f"diagnostic/check/24_portal_entries/ignore=foo,{obj_name},bar"])
    test_diagnostic_module(DIAGNOSTIC_MODULE, success_expected=True)
