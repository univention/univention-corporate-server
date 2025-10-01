#!/usr/share/ucs-test/runner pytest-3 -s -l -v
## desc: "Test the UCS <-> AD NT user locked out sync"
## exposure: dangerous
## packages:
## - univention-ad-connector

import random
from collections.abc import Generator

import ldap
import pytest

from univention.testing.active_directory import (
    AccountLockedOutException, ActiveDirectorySettings, DomainPasswordSettings, DomainPasswordsettingsData,
    LogonFailureException, NotLockedOutException, Shares, User, UserData,
)
from univention.testing.connector_common import to_unicode
from univention.testing.ucr import UCSTestConfigRegistry
from univention.testing.udm import UCSTestUDM

from adconnector import _Connector, connector_running_on_this_host, wait_for_sync as ad_wait_for_sync


def get_user_dn(username: str, ucr: UCSTestConfigRegistry):
    new_position = 'cn=users,%s' % ucr.get('connector/ad/ldap/base')
    ad_user_dn = 'cn=%s,%s' % (ldap.dn.escape_dn_chars(to_unicode(username)), new_position)

    udm_user_dn = ldap.dn.dn2str(
        [
            [('uid', to_unicode(username), ldap.AVA_STRING)],
            [('CN', 'users', ldap.AVA_STRING)],
            *ldap.dn.str2dn(ucr.get('ldap/base')),
        ],
    )

    return {
        'ad_user_dn': ad_user_dn,
        'udm_user_dn': udm_user_dn,
    }


@pytest.fixture
def ad_user_locked(
    active_directory_settings: ActiveDirectorySettings,
) -> Generator[UserData, None, None]:
    """
    Creates an user in AD, lock him with failed login attemps
    and deletes the user after the calling function is completed.
    """
    # Configures AD to lock an user account after 3
    # failed login attemps
    domain_passwordsettings = DomainPasswordSettings(active_directory_settings)
    orig_domain_passwordsettings = domain_passwordsettings.get()
    new_domain_passwordsettings = DomainPasswordsettingsData(
        account_lockout_duration=30,
        account_lockout_threshold=3,
        reset_account_lockout_after=30,
    )
    domain_passwordsettings.set(new_domain_passwordsettings)

    # Create user in AD
    user = User(active_directory_settings)
    ad_user = user.create(username=f'TestSyncLockedOut{random.randrange(1, 999)}', password='Univention.99')

    ad_wait_for_sync()

    # Lock user with failed login attemps
    shares = Shares(active_directory_settings)
    account_locked = False
    for i in range(new_domain_passwordsettings.account_lockout_threshold + 1):
        try:
            shares.list(
                username=ad_user.name,
                password='wrong_password',
            )

        except LogonFailureException:
            pass
        except AccountLockedOutException:
            account_locked = True
            break

    if not account_locked:
        raise NotLockedOutException()

    ad_wait_for_sync()

    yield ad_user

    user.delete(username=ad_user.name)

    # Reset lockout policy
    domain_passwordsettings.set(orig_domain_passwordsettings)


@pytest.mark.skipif(not connector_running_on_this_host(), reason='Univention AD Connector not configured.')
def test_sync_locked_ad_to_ucs(
    udm: UCSTestUDM,
    ucr: UCSTestConfigRegistry,
    ad_connector: _Connector,
    ad_user_locked: UserData,
):
    """
    Test if the UCS user attribute 'sambaBadPasswordTime' would be
    synced with AD user attribute 'lockoutTime', when the user is
    lockout in AD, because of too many password fails.
    """
    user_dn = get_user_dn(username=ad_user_locked.name, ucr=ucr)
    ad_res = ad_connector._ad.get(dn=user_dn['ad_user_dn'], attr=['lockoutTime'])
    lockout_time = ad_res.get('lockoutTime')

    attr = udm._lo.get(user_dn['udm_user_dn'], ['sambaAcctFlags', 'sambaBadPasswordTime'])
    samba_acct_flags = attr.get('sambaAcctFlags', [b''])[0]
    samba_bad_password_time = attr.get('sambaBadPasswordTime')

    assert b'L' in samba_acct_flags
    # Compare only the first five digits, because of conversion differences.
    assert lockout_time[0].decode('ascii')[:5] == samba_bad_password_time[0].decode('ascii')[:5]


@pytest.mark.skipif(not connector_running_on_this_host(), reason='Univention AD Connector not configured.')
def test_sync_unlocked_ad_to_ucs(
    udm: UCSTestUDM,
    ucr: UCSTestConfigRegistry,
    ad_user_locked: UserData,
    active_directory_settings: ActiveDirectorySettings,
):
    """
    Test if the AD user attribute 'lockoutTime' would
    be synced  with the UCS user attribute 'sambaBadPasswordTime'
    when the user will be unlocked in AD.
    """
    user_dn = get_user_dn(username=ad_user_locked.name, ucr=ucr)
    user = User(active_directory_settings)
    user.unlock(username=ad_user_locked.name)

    ad_wait_for_sync()

    udm_res = udm._lo.get(user_dn['udm_user_dn'], ['sambaAcctFlags', 'sambaBadPasswordTime'])
    samba_acct_flags = udm_res.get('sambaAcctFlags', [b''])[0]
    samba_bad_password_time = udm_res.get('sambaBadPasswordTime')[0]

    assert b'L' not in samba_acct_flags
    assert samba_bad_password_time == b'0'


@pytest.mark.skipif(not connector_running_on_this_host(), reason='Univention AD Connector not configured.')
def test_sync_unlocked_ucs_to_ad(
    udm: UCSTestUDM,
    ad_connector: _Connector,
    ucr: UCSTestConfigRegistry,
    ad_user_locked: UserData,
):
    """
    Test if the AD user attribute 'lockoutTime' would
    be synced with the UCS user attribute 'sambaBadPasswordTime'
    when the user will be unlocked in UCS.
    """
    user_dn = get_user_dn(username=ad_user_locked.name, ucr=ucr)
    udm_res = udm._lo.get(user_dn['udm_user_dn'], ['sambaAcctFlags', 'sambaBadPasswordTime'])
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

    ad_wait_for_sync()

    ad_res = ad_connector._ad.get(user_dn['ad_user_dn'], ['lockoutTime'])
    lockout_time = ad_res.get('lockoutTime', [None])[0]

    assert lockout_time == new_samba_bad_password_time
