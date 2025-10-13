#!/usr/share/ucs-test/runner pytest-3 -s -l -v
## desc: "Test the recyclebin restore sync"
## exposure: dangerous
## packages:
## - univention-s4-connector


import pytest
from ldap.dn import dn2str, str2dn
from ldap.filter import escape_filter_chars

from univention.admin.uldap import access
from univention.testing.fixtures_recyclebin import _deleted_object_dn, _restore_in_ucs
from univention.testing.strings import random_name
from univention.testing.udm import UCSTestUDM
from univention.testing.utils import verify_ldap_object

from s4connector import S4Connection, connector_running_on_this_host, wait_for_sync


pytest_plugins = ('univention.testing.fixtures_recyclebin')


def _create_and_delete_user_in_ucs(udm: UCSTestUDM, connector: S4Connection, position: str, lo: access) -> dict:
    user = _create_user_in_ucs(udm, connector, position, lo)
    _delete_user_in_ucs(udm, connector, user['ucs_dn'], user['connector_dn'])
    return user


def _create_user_in_ucs(udm: UCSTestUDM, connector: S4Connection, position: str, lo: access) -> dict:
    user_ucs_dn, username = udm.create_user(position=position, wait_for=False)
    wait_for_sync()
    verify_ldap_object(user_ucs_dn, should_exist=True)
    original_ucs_attrs = lo.get(user_ucs_dn, attr=['+', '*'])
    user_connector_dn, original_connector_attrs = connector.search(f'sAMAccountName={escape_filter_chars(username)}')[0]
    return {
        'original_ucs_attrs': original_ucs_attrs,
        'original_connector_attrs': original_connector_attrs,
        'ucs_dn': user_ucs_dn,
        'connector_dn': user_connector_dn,
    }


def _delete_user_in_ucs(udm: UCSTestUDM, connector: S4Connection, ucs_dn: str, connector_dn: str) -> dict:
    udm.remove_object('users/user', dn=ucs_dn, wait_for=False)
    wait_for_sync()
    verify_ldap_object(ucs_dn, should_exist=False)
    connector.verify_object(connector_dn, None)


def _verify_ucs_attributes(dn: str, attributes: dict):
    diverse_attributes = [
        'createTimestamp',
        'entryCSN',
        'modifyTimestamp',
        'sambaPwdLastSet',
    ]
    for da in diverse_attributes:
        if attributes.get(da):
            attributes.pop(da)
    verify_ldap_object(dn, should_exist=True, expected_attr=attributes, retry_count=0)


@pytest.fixture
def connector():
    return S4Connection()


@pytest.fixture
def domain_sid(udm: UCSTestUDM) -> str:
    res = udm.list_objects('settings/sambadomain')
    return res[0][1].get('SID')[0]


@pytest.mark.skipif(not connector_running_on_this_host(), reason='Connector not configured.')
@pytest.mark.parametrize(
    'recyclebin_policy',
    [
        f'recyclebin_{random_name()}',
        f"recyclebin_{random_name()}_ $&%!|/:.()[]§`'^*-{{}}~",
        f'recyclebin_{random_name()}_€Ω®@½äöüßâêôûŵẑĉŷĵĝŝ',
        # f'recyclebin_{random_name()}_+"<>\\=?#',
    ],
    indirect=True,
)
def test_restore_ucs(udm: UCSTestUDM, recyclebin_policy: tuple, lo: access, connector: S4Connection):
    recyclebin_container, _ = recyclebin_policy
    user = _create_and_delete_user_in_ucs(
        udm=udm,
        lo=lo,
        connector=connector,
        position=recyclebin_container,
    )

    _restore_in_ucs(
        univention_object_identifier=user.get('original_ucs_attrs')['univentionObjectIdentifier'][0].decode('UTF-8'),
        udm=udm,
    )
    wait_for_sync()

    _verify_ucs_attributes(dn=user['ucs_dn'], attributes=user['original_ucs_attrs'])

    assert user['original_connector_attrs']
    connector.verify_object_con(user['connector_dn'], user['original_connector_attrs'])


@pytest.mark.skipif(not connector_running_on_this_host(), reason='Connector not configured.')
@pytest.mark.parametrize(
    'recyclebin_policy',
    [
        f'recyclebin_{random_name()}',
        f"recyclebin_{random_name()}_ $&%!|/:.()[]§`'^*-{{}}~",
        f'recyclebin_{random_name()}_€Ω®@½äöüßâêôûŵẑĉŷĵĝŝ',
        # f'recyclebin_{random_name()}_+"<>\\=?#',
    ],
    indirect=True,
)
def test_restore_connector(udm: UCSTestUDM, recyclebin_policy: tuple, lo: access, connector: S4Connection):
    """
    Test restore sync, when user is restored in AD.

    Full version, succeeds only when recyclebin in AD is activated!
    See: https://learn.microsoft.com/de-de/troubleshoot/windows-server/active-directory/retore-deleted-accounts-and-groups-in-ad
         https://diecknet.de/de/2025/04/28/active-directory-recycle-bin/
         https://woshub.com/restore-deleted-active-directory-objects-users/
         https://theitbros.com/restore-deleted-active-directory-user/
    """
    recyclebin_container, _ = recyclebin_policy
    user = _create_and_delete_user_in_ucs(
        udm=udm,
        lo=lo,
        connector=connector,
        position=recyclebin_container,
    )

    connector.restore_object(dn=user['connector_dn'])
    wait_for_sync()

    # these attributes are overwritten by the restore in S4
    # because they are not restored in samba, samba does not fully support recycle bin
    for attr in ['givenName', 'gecos', 'displayName', 'loginShell', 'cn']:
        if attr in user['original_ucs_attrs']:
            del user['original_ucs_attrs'][attr]
    for attr in ['givenName', 'loginShell', 'displayName']:
        if attr in user['original_connector_attrs']:
            del user['original_connector_attrs'][attr]

    _verify_ucs_attributes(dn=user['ucs_dn'], attributes=user['original_ucs_attrs'])
    connector.verify_object_con(user['connector_dn'], user['original_connector_attrs'])


@pytest.mark.skipif(not connector_running_on_this_host(), reason='Connector not configured.')
def test_link_after_restore_ucs(udm: UCSTestUDM, recyclebin_policy_session: tuple, lo: access, connector: S4Connection):
    recyclebin_container, _ = recyclebin_policy_session
    user = _create_and_delete_user_in_ucs(
        udm=udm,
        lo=lo,
        connector=connector,
        position=recyclebin_container,
    )

    restored_dn = _restore_in_ucs(
        univention_object_identifier=user['original_ucs_attrs']['univentionObjectIdentifier'][0].decode('UTF-8'),
        udm=udm,
    )

    new_firstname = 'test_link_after_restore_ucs'
    udm._cleanup.setdefault('users/user', []).append(restored_dn)
    udm.modify_object(modulename='users/user', dn=restored_dn, firstname=new_firstname, wait_for=False)
    wait_for_sync()

    connector.verify_object_con(user['connector_dn'], {'givenName': [new_firstname.encode()]})


def test_restore_connector_minimal_deleted_object_in_ucs_removed(udm: UCSTestUDM, recyclebin_policy_session: tuple, lo: access, connector: S4Connection):
    """
    Test restore in AD but remove the deleted object in UCS
    Connector should just ADD a "new" object in UCS, same Name but different ID's
    """
    recyclebin_container, _ = recyclebin_policy_session
    user = _create_and_delete_user_in_ucs(
        udm=udm,
        lo=lo,
        connector=connector,
        position=recyclebin_container,
    )

    # remove deleted object in UCS
    deleted_dn = _deleted_object_dn(
        univention_object_identifier=user.get('original_ucs_attrs')['univentionObjectIdentifier'][0].decode('UTF-8'),
    )
    udm._cleanup.setdefault('recyclebin/removedobject', []).append(deleted_dn)
    udm.remove_object('recyclebin/removedobject', dn=deleted_dn)
    verify_ldap_object(deleted_dn, should_exist=False, retry_count=2)

    # Restore in AD
    connector.restore_object(dn=user['connector_dn'])
    wait_for_sync()

    _verify_ucs_attributes(
        dn=user['ucs_dn'],
        attributes={
            'uid': user['original_ucs_attrs']['uid'],
        },
    )

    connector.verify_object_con(
        user.get('connector_dn'),
        {
            'distinguishedName': user['original_connector_attrs']['distinguishedName'],
            'name': user['original_connector_attrs']['name'],
            'sAMAccountName': user['original_connector_attrs']['sAMAccountName'],
            'objectGUID': user['original_connector_attrs']['objectGUID'],
            'objectSid': user['original_connector_attrs']['objectSid'],
        },
    )


@pytest.mark.skipif(not connector_running_on_this_host(), reason='Connector not configured.')
def test_restore_connector_minimal(udm: UCSTestUDM, recyclebin_policy_session: tuple, lo: access, connector: S4Connection):
    """
    Test restore sync, when user is restored in AD.

    Minimal version, must succeed even when recyclebin in AD is deactivated!
    See: https://learn.microsoft.com/de-de/troubleshoot/windows-server/active-directory/retore-deleted-accounts-and-groups-in-ad
         https://diecknet.de/de/2025/04/28/active-directory-recycle-bin/
         https://woshub.com/restore-deleted-active-directory-objects-users/
         https://theitbros.com/restore-deleted-active-directory-user/
    """
    recyclebin_container, _ = recyclebin_policy_session
    user = _create_and_delete_user_in_ucs(
        udm=udm,
        lo=lo,
        connector=connector,
        position=recyclebin_container,
    )

    # Restore in AD
    connector.restore_object(dn=user['connector_dn'])
    wait_for_sync()

    _verify_ucs_attributes(
        dn=user['ucs_dn'],
        attributes={
            'univentionObjectIdentifier': user['original_ucs_attrs']['univentionObjectIdentifier'],
            'entryUUID': user['original_ucs_attrs']['entryUUID'],
            'sambaSID': user['original_ucs_attrs']['sambaSID'],
            'uid': user['original_ucs_attrs']['uid'],
            'entryDN': user['original_ucs_attrs']['entryDN'],
        },
    )

    connector.verify_object_con(
        user.get('connector_dn'),
        {
            'distinguishedName': user['original_connector_attrs']['distinguishedName'],
            'name': user['original_connector_attrs']['name'],
            'sAMAccountName': user['original_connector_attrs']['sAMAccountName'],
            'objectGUID': user['original_connector_attrs']['objectGUID'],
            'objectSid': user['original_connector_attrs']['objectSid'],
        },
    )


def test_restore_to_another_position_in_ad(udm: UCSTestUDM, recyclebin_policy_session: tuple, lo: access, connector: S4Connection):
    recyclebin_container, _ = recyclebin_policy_session
    ou_name = random_name()
    ou_dn = udm.create_object('container/ou', name=ou_name)
    user = _create_and_delete_user_in_ucs(
        udm=udm,
        lo=lo,
        connector=connector,
        position=recyclebin_container,
    )
    ou_dn_ad = connector.search(f'ou={escape_filter_chars(ou_name)}')[0][0]

    # Restore in AD to another position
    connector.restore_object(dn=user['connector_dn'], position=ou_dn_ad)
    wait_for_sync()

    ad_rdn, *_ = str2dn(user['connector_dn'])
    new_ad_dn = dn2str([ad_rdn, *str2dn(ou_dn_ad)])
    ucs_rdn, *_ = str2dn(user['ucs_dn'])
    new_ucs_dn = dn2str([ucs_rdn, *str2dn(ou_dn)])

    _verify_ucs_attributes(
        dn=new_ucs_dn,
        attributes={
            'univentionObjectIdentifier': user['original_ucs_attrs']['univentionObjectIdentifier'],
            'entryUUID': user['original_ucs_attrs']['entryUUID'],
            'sambaSID': user['original_ucs_attrs']['sambaSID'],
            'uid': user['original_ucs_attrs']['uid'],
            'entryDN': [new_ucs_dn],
        },
    )

    connector.verify_object_con(
        new_ad_dn,
        {
            'distinguishedName': [new_ad_dn.encode()],
            'name': user['original_connector_attrs']['name'],
            'sAMAccountName': user['original_connector_attrs']['sAMAccountName'],
            'objectGUID': user['original_connector_attrs']['objectGUID'],
            'objectSid': user['original_connector_attrs']['objectSid'],
        },
    )


def test_ouid2guid_state(udm: UCSTestUDM, recyclebin_policy_session: tuple, lo: access, connector: S4Connection):
    recyclebin_container, _ = recyclebin_policy_session
    user = _create_user_in_ucs(
        udm=udm,
        lo=lo,
        connector=connector,
        position=recyclebin_container,
    )
    uoid = user['original_ucs_attrs']['univentionObjectIdentifier'][0].decode('utf-8')
    guid = connector.decode_guid(user['original_connector_attrs']['objectGUID'][0])

    uoid2guid_uoid = connector.cache_internal.get_by_value('uoid2guid', guid)
    uoid2guid_guid = connector.cache_internal.get('uoid2guid', uoid)

    assert uoid == uoid2guid_uoid
    assert guid == uoid2guid_guid

    _delete_user_in_ucs(udm, connector, user['ucs_dn'], user['connector_dn'])

    uoid2guid_uoid = connector.cache_internal.get_by_value('uoid2guid', guid)
    uoid2guid_guid = connector.cache_internal.get('uoid2guid', uoid)

    assert not uoid2guid_uoid
    assert not uoid2guid_guid

    uoid2guid_uoid = connector.cache_internal.get_by_value('uoid2guid', guid, deleted=True)
    uoid2guid_guid = connector.cache_internal.get('uoid2guid', uoid, deleted=True)

    assert uoid == uoid2guid_uoid
    assert guid == uoid2guid_guid

    _restore_in_ucs(
        univention_object_identifier=user.get('original_ucs_attrs')['univentionObjectIdentifier'][0].decode('UTF-8'),
        udm=udm,
    )
    wait_for_sync()

    uoid2guid_uoid = connector.cache_internal.get_by_value('uoid2guid', guid)
    uoid2guid_guid = connector.cache_internal.get('uoid2guid', uoid)

    assert uoid == uoid2guid_uoid
    assert guid == uoid2guid_guid
