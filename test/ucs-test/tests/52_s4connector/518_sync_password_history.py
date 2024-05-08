#!/usr/share/ucs-test/runner pytest-3 -s -l -v
## desc: "Test the UCS<->S4 NT password history sync"
## exposure: dangerous
## packages:
## - univention-s4-connector
## bugs:
##  - 52230

from __future__ import annotations

import binascii
import subprocess

import ldap
import pytest

import univention.admin.uldap
import univention.testing.connector_common as tcommon
import univention.testing.strings as tstrings
from univention.admin import modules
from univention.config_registry import ucr
from univention.testing.connector_common import NormalUser, create_udm_user, delete_con_user, to_unicode
from univention.testing.udm import UCSTestUDM, UCSTestUDM_ModifyUDMObjectFailed
from univention.testing.utils import get_ldap_connection

import s4connector
from s4connector import connector_running_on_this_host, connector_setup


pytestmark = pytest.mark.skipif(not connector_running_on_this_host(), reason="S4C not configured")


def create_s4_user(username: str, password: str, **kwargs) -> tuple[str, str]:
    cmd = ["samba-tool", "user", "create", "--use-username-as-cn", username, password]
    subprocess.run(cmd, capture_output=True, check=True)

    new_position = 'cn=users,%(connector/s4/ldap/base)s' % ucr
    con_user_dn = f'cn={ldap.dn.escape_dn_chars(tcommon.to_unicode(username))},{new_position}'

    udm_user_dn = ldap.dn.dn2str([
        [("uid", to_unicode(username), ldap.AVA_STRING)],
        [("CN", "users", ldap.AVA_STRING)]] + ldap.dn.str2dn(ucr['ldap/base']))
    s4connector.wait_for_sync()
    return (con_user_dn, udm_user_dn)


def modify_passwordpolicy_s4(key: str, value: str) -> None:
    cmd = ["samba-tool", "domain", "passwordsettings", "set", f"--{key}={value}"]
    subprocess.run(cmd, capture_output=True, check=False)


def modify_password_s4(username: str, password: str) -> None:
    cmd = ["samba-tool", "user", "setpassword", f"--newpassword={password}", username]
    subprocess.run(cmd, capture_output=True, check=True)
    s4connector.wait_for_sync()


def udm_modify(udm, **kwargs) -> None:
    udm._cleanup.setdefault('users/user', []).append(kwargs['dn'])
    udm.modify_object(modulename='users/user', **kwargs)
    s4connector.wait_for_sync()


def test_initial_S4_pwd_is_synced() -> None:
    with connector_setup("sync") as s4, UCSTestUDM() as udm:
        (s4_user_dn, udm_user_dn) = create_s4_user(tstrings.random_username(), "Univention.2-")

        s4_results = s4.get(s4_user_dn, attr=['unicodePwd'])
        nt_hash = binascii.b2a_hex(s4_results['unicodePwd'][0])
        ucs_result = udm._lo.search(base=udm_user_dn, attr=['sambaNTPassword', 'pwhistory'])[0][1]
        print("- Check udm and S4 nt_hash.")
        assert ucs_result["sambaNTPassword"][0] == nt_hash.upper(), "UDM sambaNTPassword and S4 nt_hash should be equal"
        print("Ok")
        print("- Check udm and S4 pwd history.")
        pwhist = ucs_result["pwhistory"][0].decode('ASCII').strip().split(" ")
        assert nt_hash.decode('ASCII').upper() == pwhist[-1][len("{NT}$"):].upper(), "Error verifying last S4 and UDM password entry"
        print("Ok")

        print("- Try to set original S4 password in UDM. (Should Raise, the password is in the history)")
        with pytest.raises(UCSTestUDM_ModifyUDMObjectFailed):
            udm_modify(udm, dn=udm_user_dn, password="Univention.2-")
        print("Ok")

        print("- Set a different password in in UDM.")
        udm_modify(udm, dn=udm_user_dn, password="Univention.3-")
        print("Ok")

        delete_con_user(s4, s4_user_dn, udm_user_dn, s4connector.wait_for_sync)


def test_UCS_pwd_in_s4_history_synced() -> None:
    with connector_setup("sync") as s4, UCSTestUDM() as udm:
        udm_user = NormalUser()
        (udm_user_dn, s4_user_dn) = create_udm_user(udm, s4, udm_user, s4connector.wait_for_sync)

        print("- Set a different password in in S4.")
        modify_password_s4(ldap.dn.explode_rdn(s4_user_dn, notypes=True)[0], "Univention.5-")
        print("Ok")

        print("- Try to set the same password in UDM. (Should Raise, the password is in the history)")
        with pytest.raises(UCSTestUDM_ModifyUDMObjectFailed):
            udm_modify(udm, dn=udm_user_dn, password="Univention.5-")
        print("Ok")

        s4_results = s4.get(s4_user_dn, attr=['unicodePwd', 'ntPwdHistory'])
        nt_hash = binascii.b2a_hex(s4_results['unicodePwd'][0])
        ucs_result = udm._lo.search(base=udm_user_dn, attr=['sambaNTPassword', 'pwhistory'])[0][1]
        print("- Check udm and S4 nt_hash.")
        assert ucs_result["sambaNTPassword"][0] == nt_hash.upper(), "UDM sambaNTPassword and S4 nt_hash should be equal"
        print("Ok")
        print("- Check udm and S4 pwd history.")
        pwhist = ucs_result["pwhistory"][0].decode('ASCII').strip().split(" ")
        assert nt_hash.decode('ASCII').upper() == pwhist[-1][len("{NT}$"):].upper(), "Error verifying last S4 and UDM password entry"
        print("Ok")

        delete_con_user(s4, s4_user_dn, udm_user_dn, s4connector.wait_for_sync)


@pytest.mark.skipif(not connector_running_on_this_host(), reason="Univention S4 Connector not configured.")
def test_empty_pwd_policy() -> None:
    with connector_setup("sync") as s4, UCSTestUDM() as udm:
        udm_user = NormalUser()
        (udm_user_dn, s4_user_dn) = create_udm_user(udm, s4, udm_user, s4connector.wait_for_sync)

        base_dn = ucr['ldap/base']
        lo = get_ldap_connection(admin_uldap=True)
        position = univention.admin.uldap.position(lo.base)
        modules.update()
        udm_dc = modules.get("container/dc")
        modules.init(lo, position, udm_dc)
        modify_passwordpolicy_s4("history-length", "3")
        univentionPolicyReference = lo.get(base_dn, attr=['univentionPolicyReference'])['univentionPolicyReference'][0].decode('UTF-8')
        try:
            if univentionPolicyReference:
                udm._cleanup.setdefault("container/dc", []).append(base_dn)
                udm.modify_object("container/dc", dn=base_dn, policy_dereference=univentionPolicyReference)

            print("- Set a different password in in S4.")
            udm_modify(udm, dn=udm_user_dn, password="Univention.2-")
            print("Ok")

            s4_results = s4.get(s4_user_dn, attr=['unicodePwd', 'ntPwdHistory'])
            nt_hash = binascii.b2a_hex(s4_results['unicodePwd'][0])
            ucs_result = udm._lo.search(base=udm_user_dn, attr=['sambaNTPassword'])[0][1]
            print("- Check udm and S4 nt_hash.")
            assert ucs_result["sambaNTPassword"][0] == nt_hash.upper(), "UDM sambaNTPassword and S4 nt_hash should be equal"
            print("Ok")
        finally:
            if univentionPolicyReference:
                udm.modify_object("container/dc", dn=base_dn, policy_reference=univentionPolicyReference)
                udm._cleanup["container/dc"] = [x for x in udm._cleanup.setdefault("container/dc", []) if x != base_dn]
                modify_passwordpolicy_s4("history-length", "0")

        delete_con_user(s4, s4_user_dn, udm_user_dn, s4connector.wait_for_sync)
