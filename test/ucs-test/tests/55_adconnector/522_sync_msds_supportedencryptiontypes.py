#!/usr/share/ucs-test/runner pytest-3 -s -l -v
## desc: "Test msDS-SupportedEncryptionTypes handling during password sync"
## exposure: dangerous
## packages:
## - univention-ad-connector
## tags:
##  - skip_admember

import subprocess

import ldap
import pytest

import univention.config_registry
import univention.testing.strings as tstrings
from univention.testing.connector_common import NormalUser, create_udm_user, delete_con_user

import adconnector
from adconnector import connector_running_on_this_host, connector_setup, wait_for_sync


AD = adconnector.ADConnection()

from univention.testing.udm import UCSTestUDM  # noqa: E402


configRegistry = univention.config_registry.ConfigRegistry()
configRegistry.load()

MISSING_ATTR = "msDS-SupportedEncryptionTypes should be set to include RC4"


def _set_ad_password(username, password):
    host = configRegistry.get("connector/ad/ldap/host")
    admin = ldap.dn.explode_rdn(configRegistry.get("connector/ad/ldap/binddn"), notypes=True)[0]
    passw = open(configRegistry.get("connector/ad/ldap/bindpw")).read()
    cmd = ["samba-tool", "user", "setpassword", "--newpassword='%s'" % password, username, "--URL=ldap://%s" % host, "-U'%s'%%'%s'" % (admin, passw)]
    subprocess.check_call(" ".join(cmd), shell=True)


def _get_ad_attribute(ad_user_dn):
    ad_attrs = AD.get(ad_user_dn, attr=['msDS-SupportedEncryptionTypes'])
    return ad_attrs.get('msDS-SupportedEncryptionTypes')


def _assert_rc4_bit_set(ad_user_dn, msg=MISSING_ATTR):
    enc_types_val = _get_ad_attribute(ad_user_dn)
    assert enc_types_val is not None, f"{msg}: attribute is missing"
    enc_types = int(enc_types_val[0])
    assert enc_types & 4, f"{msg}: value {enc_types} does not include bit 4 (RC4)"


@pytest.mark.skipif(not connector_running_on_this_host(), reason="Univention AD Connector not configured.")
def test_password_sync_ucs_sets_arc4_in_msds_supportedencryptiontypes():
    """UCS->AD password sync must set msDS-SupportedEncryptionTypes with RC4 (bit 4)."""
    with connector_setup("sync"), UCSTestUDM() as udm:
        udm_user = NormalUser()
        (udm_user_dn, ad_user_dn) = create_udm_user(udm, AD, udm_user, wait_for_sync)
        _assert_rc4_bit_set(ad_user_dn, "After initial user creation")

        AD.set_attributes(ad_user_dn, **{'msDS-SupportedEncryptionTypes': [b'24']})
        wait_for_sync()

        new_password = f"U{tstrings.random_string(alpha=True)}123!"
        udm.modify_object('users/user', dn=udm_user_dn, set={'password': new_password})
        wait_for_sync()

        _assert_rc4_bit_set(ad_user_dn, "After password change from UCS")
        delete_con_user(AD, ad_user_dn, udm_user_dn, wait_for_sync)


@pytest.mark.skipif(not connector_running_on_this_host(), reason="Univention AD Connector not configured.")
def test_password_sync_ad_deletes_msds_supportedencryptiontypes():
    """AD->UCS password sync must delete msDS-SupportedEncryptionTypes from AD."""
    with connector_setup("sync"), UCSTestUDM() as udm:
        udm_user = NormalUser()
        (udm_user_dn, ad_user_dn) = create_udm_user(udm, AD, udm_user, wait_for_sync)
        _assert_rc4_bit_set(ad_user_dn, "Before AD password change")

        ad_attrs = AD.get(ad_user_dn, attr=['sAMAccountName'])
        sAMAccountName = ad_attrs.get('sAMAccountName', [b''])[0].decode('UTF-8')

        _set_ad_password(sAMAccountName, "Univention.99")
        wait_for_sync()

        assert _get_ad_attribute(ad_user_dn) is None, \
            "msDS-SupportedEncryptionTypes should be deleted after AD password sync"
        delete_con_user(AD, ad_user_dn, udm_user_dn, wait_for_sync)
