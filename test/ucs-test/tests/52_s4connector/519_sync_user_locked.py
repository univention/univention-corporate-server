#!/usr/share/ucs-test/runner pytest-3 -s -l -v
## desc: "Test the UCS <-> Samba user locked out sync"
## exposure: dangerous
## packages:
## - univention-s4-connector

import ldap
import pytest

from univention.admin import uexceptions, uldap
from univention.config_registry import ConfigRegistry
from univention.lib.umc import HTTPError
from univention.testing.active_directory import (
    AccountLockedOutException, ActiveDirectorySettings, DomainPasswordSettings, DomainPasswordsettingsData,
    LogonFailureException, NotLockedOutException, Shares, User, UserData,
)
from univention.testing.ucr import UCSTestConfigRegistry
from univention.testing.udm import UCSTestUDM
from univention.testing.umc import Client
from univention.testing.utils import restart_slapd

from s4connector import S4Connection, connector_running_on_this_host, wait_for_sync as s4_wait_for_sync


def get_user_dn(username: str, config_registry: ConfigRegistry):
    new_position = 'cn=users,%s' % config_registry.get('connector/s4/ldap/base')
    samba_user_dn = 'cn=%s,%s' % (ldap.dn.escape_dn_chars(username), new_position)

    udm_user_dn = ldap.dn.dn2str(
        [
            [('uid', username, ldap.AVA_STRING)],
            [('CN', 'users', ldap.AVA_STRING)],
            *ldap.dn.str2dn(config_registry.get('ldap/base')),
        ],
    )

    return {
        'samba_user_dn': samba_user_dn,
        'udm_user_dn': udm_user_dn,
    }


def lock_user_via_smb(username: str, active_directory_settings: ActiveDirectorySettings):
    shares = Shares(active_directory_settings)
    account_lockout_threshold = DomainPasswordSettings(active_directory_settings).get().account_lockout_threshold
    account_locked = False
    for i in range(account_lockout_threshold + 1):
        try:
            shares.list(
                username=username,
                password='wrong_password',
            )

        except LogonFailureException:
            pass

        except AccountLockedOutException:
            account_locked = True
            break

    if not account_locked:
        raise NotLockedOutException()


def lock_user_via_pam(username: str, ucr: UCSTestConfigRegistry):
    client = Client(language='en-US')
    resp = client.authenticate(username, 'univention')
    assert resp.status == 200

    for _ in range(ucr.get_int('auth/faillog/limit')):
        with pytest.raises(HTTPError) as e:
            client.authenticate(username, 'fake_password')

    with pytest.raises(HTTPError) as e:
        client.authenticate(username, 'univention')

    assert e.value.code == 401


def lock_user_via_ldap(binddn: str, ucr: UCSTestConfigRegistry, udm: UCSTestUDM):
    def ldap_login(binddn, bindpw, ucr):
        uldap.access(
            host=ucr['ldap/server/name'],
            port=ucr.get('ldap/server/port', 7389),
            base=ucr['ldap/base'],
            binddn=binddn,
            bindpw=bindpw,
            start_tls=2,
            follow_referral=True,
        )

    ldap_base = ucr.get('ldap/base')
    ppolicy_dn = f'cn=default,cn=ppolicy,cn=univention,{ldap_base}'
    ppolicy = udm._lo.get(ppolicy_dn)
    pwd_max_failure = int(ppolicy.get('pwdMaxFailure')[0].decode('ascii'))

    ldap_login(ucr=ucr, binddn=binddn, bindpw='univention')

    for _ in range(pwd_max_failure):
        try:
            ldap_login(ucr=ucr, binddn=binddn, bindpw='wrong_password')
        except uexceptions.authFail:
            pass

    with pytest.raises(uexceptions.authFail):
        ldap_login(ucr=ucr, binddn=binddn, bindpw='univention')


@pytest.fixture
def password_policies(active_directory_settings: ActiveDirectorySettings, ucr: UCSTestConfigRegistry, udm: UCSTestUDM):
    # Configures Samba to lock an user account after 3
    # failed login attemps
    ad_domain_passwordsettings = DomainPasswordSettings(active_directory_settings)
    orig_ad_domain_passwordsettings = ad_domain_passwordsettings.get()
    new_ad_domain_passwordsettings = DomainPasswordsettingsData(
        account_lockout_duration=5,
        account_lockout_threshold=3,
        reset_account_lockout_after=3,
    )
    ad_domain_passwordsettings.set(new_ad_domain_passwordsettings)

    # Configures PAM and enable LDAP ppolicy
    ucr.handler_set(
        [
            'auth/faillog=yes',
            'auth/faillog/limit=3',
            'auth/faillog/lock_global=yes',
            'auth/faillog/unlock_time=300',
            'ldap/ppolicy/enabled=yes',
        ],
    )

    restart_slapd()

    # Configure LDAP
    ldap_base = ucr.get('ldap/base')
    ppolicy_dn = f'cn=default,cn=ppolicy,cn=univention,{ldap_base}'
    old_ppolicy = udm._lo.get(ppolicy_dn)
    udm._lo.modify(
        ppolicy_dn,
        [
            ('pwdMaxFailure', old_ppolicy.get('pwdMaxFailure'), b'3'),
            ('pwdFailureCountInterval', old_ppolicy.get('pwdFailureCountInterval'), b'180'),
        ],
    )

    yield True

    # Reset lockout policy
    ad_domain_passwordsettings.set(orig_ad_domain_passwordsettings)


def test_sync_locked_samba_to_ucs(
    udm: UCSTestUDM,
    ucr: UCSTestConfigRegistry,
    s4_connector: S4Connection,
    samba_user: UserData,
    password_policies: bool,
    active_directory_settings: ActiveDirectorySettings,
):
    """
    Test if the UCS user attribute 'sambaBadPasswordTime' would be
    synced with Samba user attribute 'sambaBadPasswordTime', when the user is
    lockout in Samba, because of too many password fails.
    """
    assert password_policies

    lock_user_via_smb(username=samba_user.name, active_directory_settings=active_directory_settings)
    s4_wait_for_sync()

    user_dn = get_user_dn(username=samba_user.name, config_registry=ucr)
    s4_res = s4_connector.get(dn=user_dn['samba_user_dn'], attr=['lockoutTime'])
    lockout_time = s4_res.get('lockoutTime')

    udm_res = udm._lo.search(
        base=user_dn['udm_user_dn'],
        scope='base',
        attr=['sambaAcctFlags', 'sambaBadPasswordTime'],
    )
    samba_acct_flags = udm_res[0][1].get('sambaAcctFlags', [b''])[0]
    samba_bad_password_time = udm_res[0][1].get('sambaBadPasswordTime')

    assert b'L' in samba_acct_flags
    assert b'D' not in samba_acct_flags
    # Compare only the first five digits, because
    # of conversion differences.
    assert lockout_time[0].decode('ascii')[:5] == samba_bad_password_time[0].decode('ascii')[:5]


@pytest.mark.skipif(not connector_running_on_this_host(), reason='Univention S4 Connector not configured.')
def test_sync_unlocked_samba_to_ucs(
    udm: UCSTestUDM,
    ucr: UCSTestConfigRegistry,
    samba_user: UserData,
    password_policies: bool,
    active_directory_settings: ActiveDirectorySettings,
):
    """
    Test if the Samba user attribute 'lockoutTime' would
    be synced  with the UCS user attribute 'sambaBadPasswordTime'
    when the user will be unlocked in Samba.
    """
    assert password_policies

    lock_user_via_smb(username=samba_user.name, active_directory_settings=active_directory_settings)
    s4_wait_for_sync()

    user_dn = get_user_dn(username=samba_user.name, config_registry=ucr)
    user = User(active_directory_settings)
    user.unlock(username=samba_user.name)

    s4_wait_for_sync()

    udm_res = udm._lo.get(
        dn=user_dn['udm_user_dn'],
        attr=['sambaAcctFlags', 'sambaBadPasswordTime'],
    )
    samba_acct_flags = udm_res.get('sambaAcctFlags', [b''])[0]
    samba_bad_password_time = udm_res.get('sambaBadPasswordTime')[0]

    assert b'L' not in samba_acct_flags
    assert samba_bad_password_time == b'0'


@pytest.mark.skipif(not connector_running_on_this_host(), reason='Univention S4 Connector not configured.')
@pytest.mark.skip('The tests failes, the user is disabled and not locked!')
def test_sync_locked_ucs_pam_to_samba(
    udm: UCSTestUDM,
    ucr: UCSTestConfigRegistry,
    s4_connector: S4Connection,
    ucs_user: dict[str, str],
    password_policies: bool,
):
    assert password_policies

    lock_user_via_pam(username=ucs_user.get('username'), ucr=ucr)
    s4_wait_for_sync()

    user_dn = get_user_dn(username=ucs_user.get('username'), config_registry=ucr)
    ad_res = s4_connector.get(dn=user_dn['samba_user_dn'], attr=['lockoutTime'])
    lockout_time = ad_res.get('lockoutTime')[0]

    udm_res = udm._lo.get(
        dn=user_dn['udm_user_dn'],
        attr=['sambaAcctFlags', 'sambaBadPasswordTime'],
    )
    samba_bad_password_time = udm_res.get('sambaBadPasswordTime')[0]
    samba_acct_flags = udm_res.get('sambaAcctFlags')[0]

    assert b'L' in samba_acct_flags
    assert lockout_time != b'0'
    assert lockout_time == samba_bad_password_time


@pytest.mark.skipif(not connector_running_on_this_host(), reason='Univention S4 Connector not configured.')
def test_sync_locked_ucs_ldap_to_samba(
    ucs_user: dict,
    ucr: UCSTestConfigRegistry,
    udm: UCSTestUDM,
    s4_connector: S4Connection,
    password_policies: bool,
):
    assert password_policies

    lock_user_via_ldap(binddn=ucs_user.get('dn'), ucr=ucr, udm=udm)
    s4_wait_for_sync()

    user_dn = get_user_dn(username=ucs_user['username'], config_registry=ucr)
    ad_res = s4_connector.get(dn=user_dn['samba_user_dn'], attr=['lockoutTime'])
    lockout_time = ad_res.get('lockoutTime')[0]

    udm_res = udm._lo.get(
        dn=user_dn['udm_user_dn'],
        attr=['sambaAcctFlags', 'sambaBadPasswordTime'],
    )
    samba_bad_password_time = udm_res.get('sambaBadPasswordTime')[0]
    samba_acct_flags = udm_res.get('sambaAcctFlags')[0]

    assert b'L' in samba_acct_flags
    assert lockout_time != b'0'
    assert lockout_time == samba_bad_password_time


@pytest.mark.skipif(not connector_running_on_this_host(), reason='Univention S4 Connector not configured.')
def test_sync_unlocked_ucs_to_samba(
    udm: UCSTestUDM,
    ucr: UCSTestConfigRegistry,
    s4_connector: S4Connection,
    samba_user: UserData,
    password_policies: bool,
    active_directory_settings: ActiveDirectorySettings,
):
    """
    Test if the Samba user attribute 'lockoutTime' would
    be synced with the UCS user attribute 'sambaBadPasswordTime'
    when the user will be unlocked in UCS.
    """
    assert password_policies

    lock_user_via_smb(username=samba_user.name, active_directory_settings=active_directory_settings)
    s4_wait_for_sync()

    user_dn = get_user_dn(username=samba_user.name, config_registry=ucr)
    udm_res = udm._lo.get(
        dn=user_dn['udm_user_dn'],
        attr=['sambaAcctFlags', 'sambaBadPasswordTime'],
    )
    old_samba_acct_flags = udm_res.get('sambaAcctFlags', [b''])[0]
    old_samba_bad_password_time = udm_res.get('sambaBadPasswordTime')

    new_samba_acct_flags = b'[U          ]'
    new_samba_bad_password_time = b'0'

    udm._lo.modify(
        user_dn['udm_user_dn'],
        [
            ('sambaAcctFlags', old_samba_acct_flags, new_samba_acct_flags),
            ('sambaBadPasswordTime', old_samba_bad_password_time, new_samba_bad_password_time),
        ],
    )

    s4_wait_for_sync()

    ad_res = s4_connector.get(dn=user_dn['samba_user_dn'], attr=['lockoutTime'])
    lockout_time = ad_res.get('lockoutTime')[0]

    assert lockout_time == new_samba_bad_password_time
