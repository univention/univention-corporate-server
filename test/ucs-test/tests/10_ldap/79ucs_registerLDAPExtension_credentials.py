#!/usr/share/ucs-test/runner pytest-3 -s
## desc: Test ucs_registerLDAPExtension with and without credentials
## tags:
##  - ldapextensions
## bugs: [56698]
## exposure: dangerous


import os
import sys
import time
from types import SimpleNamespace

import pytest

from univention.lib.ldap_extension import UniventionLDAPExtension, ucs_registerLDAPExtension
from univention.testing.ucr import UCSTestConfigRegistry
from univention.testing.utils import UCSTestDomainAdminCredentials


# mocks
def mock_is_local_active(self):
    return (0, None)


def mock_wait_for_activation(self):
    return True


UniventionLDAPExtension.is_local_active = mock_is_local_active
UniventionLDAPExtension.wait_for_activation = mock_is_local_active


def get_acl_extension(lo, ucr):
    res = lo.get(f"cn=66univention-appcenter_app,cn=ldapacl,cn=univention,{ucr['ldap/base']}")
    return SimpleNamespace(
        packagename=res["univentionOwnedByPackage"][0].decode("utf-8"),
        packageversion=res["univentionOwnedByPackageVersion"][0].decode("utf-8"),
        ucsversionstart=res["univentionUCSVersionStart"][0].decode("utf-8"),
        ucsversionend=res["univentionUCSVersionEnd"][0].decode("utf-8"),
        acl=os.path.join("/usr/share/univention-appcenter/", res["univentionLDAPACLFilename"][0].decode("utf-8")),
        active=res["univentionLDAPACLActive"][0].decode("utf-8"),
    )


def primary_or_backup():
    with UCSTestConfigRegistry() as ucr:
        return ucr.get('server/role') in ["domaincontroller_backup", "domaincontroller_master"]


@pytest.fixture()
def acl_extension(lo, ucr):
    return get_acl_extension(lo, ucr)


@pytest.fixture()
def verify_acl_extension(lo, ucr):
    """
    check that the objects univentionLDAPACLActive is FALSE after
    ucs_registerLDAPExtension and that the listener set TRUE
    after a couple of seconds
    """
    def _func():
        extension = get_acl_extension(lo, ucr)
        assert extension.active == "FALSE", "extension should be disabled after triggering ldap_touch_udm_object"
        for i in range(1, 30):
            time.sleep(3)
            extension = get_acl_extension(lo, ucr)
            if extension.active == "TRUE":
                return
        assert extension.active == "TRUE", "extension not activated by listener after waiting"

    return _func


@pytest.mark.skipif(not primary_or_backup(), reason="only domaincontroller_master/backup can retrigger ucs_registerLDAPExtension without credentials")
def test_without_credentials(acl_extension, verify_acl_extension):
    sys.argv = [
        sys.argv[0],
        "--packagename", acl_extension.packagename,
        "--packageversion", acl_extension.packageversion,
        "--ucsversionstart", acl_extension.ucsversionstart,
        "--ucsversionend", acl_extension.ucsversionend,
        "--acl", acl_extension.acl,
    ]
    ucs_registerLDAPExtension()
    verify_acl_extension()


def test_with_credentials(acl_extension, verify_acl_extension):
    account = UCSTestDomainAdminCredentials()
    sys.argv = [
        sys.argv[0],
        "--packagename", acl_extension.packagename,
        "--packageversion", acl_extension.packageversion,
        "--ucsversionstart", acl_extension.ucsversionstart,
        "--ucsversionend", acl_extension.ucsversionend,
        "--acl", acl_extension.acl,
        "--binddn", account.binddn,
        "--bindpwdfile", account.pwdfile,
    ]
    ucs_registerLDAPExtension()
    verify_acl_extension()
