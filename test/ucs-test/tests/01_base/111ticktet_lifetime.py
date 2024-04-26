#!/usr/share/ucs-test/runner pytest-3 -s -l -v
## desc: Test ticket lifetime are changed successfully
## exposure: careful
## roles:
##  - domaincontroller_master
## tags: []
## packages:
##  - univention-config
## bugs: [52987]

import pytest

from univention.testing.utils import package_installed


KRB5_PATH = "/etc/krb5.conf"
SMB_PATH = "/etc/samba/smb.conf"
VALUE = "50"
KEY = "kerberos/defaults/ticket-lifetime"


def test_kerberos_lifetime(ucr) -> None:
    ucr.handler_set([f"{KEY}={VALUE}"])
    assert f"ticket_lifetime = {VALUE}h" in open(KRB5_PATH).read()


@pytest.mark.skipif(not package_installed('univention-samba4'), reason='Missing software: univention-samba4')
def test_samba_lifetime(ucr) -> None:
    ucr.handler_set([f"{KEY}={VALUE}"])
    assert f"kdc:user ticket lifetime = {VALUE}" in open(SMB_PATH).read()
