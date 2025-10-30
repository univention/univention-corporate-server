#!/usr/share/ucs-test/runner pytest-3 -s -l -vvv
## desc: "Test uoid2guid mapping db"
## exposure: dangerous
## packages:
## - univention-ad-connector
## tags:
##  - skip_admember

import contextlib
import sqlite3
import subprocess

import ldap
import pytest

from univention.connector import decode_guid
from univention.testing.strings import random_username

from adconnector import _Connector, connector_setup2


UOID2GUID_SCRIPT = '/usr/share/univention-ad-connector/uoid2guid.py'


# TODO: after merge of fbotner/ad-con-pullcord-changes import adconnector_stopped from utils
def stop_adconnector() -> None:
    subprocess.check_call(['systemctl', 'stop', 'univention-ad-connector'])


def start_adconnector() -> None:
    subprocess.check_call(['systemctl', 'start', 'univention-ad-connector'])


def restart_adconnector() -> None:
    subprocess.check_call(['systemctl', 'restart', 'univention-ad-connector'])


@contextlib.contextmanager
def adconnector_stopped():
    try:
        stop_adconnector()
        yield
    finally:
        start_adconnector()


def test_uoid2guid_check_db():
    prefix = random_username()
    ad = _Connector()
    with adconnector_stopped():
        # check unique constraint for value
        ad.cache_internal.insert('uoid2guid', f'{prefix}-test1', f'{prefix}-test1')
        with pytest.raises(sqlite3.IntegrityError):
            ad.cache_internal.insert('uoid2guid', f'{prefix}-test2', f'{prefix}-test1')
        # check unique constraint for key
        with pytest.raises(sqlite3.IntegrityError):
            ad.cache_internal.insert('uoid2guid', f'{prefix}-test1', f'{prefix}-test3')


@pytest.mark.parametrize(
    'command',
    [
        [UOID2GUID_SCRIPT, 'list'],
        [UOID2GUID_SCRIPT, 'list', '-v'],
        [UOID2GUID_SCRIPT, 'import'],
        [UOID2GUID_SCRIPT, 'purge'],
        [UOID2GUID_SCRIPT, 'purge', '--everything'],

    ],
    ids=['list', 'list-verbose', 'import', 'purge', 'purge-everything'])
def test_uoid2guid_script(command):
    subprocess.check_call(command)


@pytest.mark.parametrize('mode', ['sync', 'write'], ids=['sync mode', 'write mode'])
def test_uoid2guid_after_create_in_udm(udm, lo, mode):
    with connector_setup2(mode) as ad:
        user_dn, username = udm.create_user()
        uoid = lo.getAttr(user_dn, attr='univentionObjectIdentifier')[0].decode('UTF-8')
        ad.wait_for_sync()
        guid = ad._ad.search(f'samAccountName={ldap.filter.escape_filter_chars(username)}')[0][1]['objectGUID'][0]
        guid = decode_guid(guid)
        assert guid
        assert guid == ad.get_uoid2guid_mapping(uoid)


@pytest.mark.parametrize('mode', ['sync', 'read'], ids=['sync mode', 'read mode'])
def test_uoid2guid_after_create_in_ad(lo, mode):
    with connector_setup2(mode) as ad:
        username = random_username()
        user_dn = ad.create_object('users/user', {'username': username.encode('UTF-8')})
        guid = ad._ad.get(user_dn)['objectGUID'][0]
        guid = decode_guid(guid)
        uoid = lo.search(f'uid={ldap.filter.escape_filter_chars(username)}')[0][1]['univentionObjectIdentifier'][0].decode('UTF-8')
        assert uoid
        assert guid == ad.get_uoid2guid_mapping(uoid)


@pytest.mark.parametrize('mode', ['sync'], ids=['sync mode'])
def test_old_mapping_removed_after_restore_in_ad_without_deleted_object_in_ucs(udm, mode, lo):
    with connector_setup2(mode) as ad:
        user_dn, username = udm.create_user()
        old_uoid = lo.getAttr(user_dn, attr='univentionObjectIdentifier')[0].decode('UTF-8')
        ad.wait_for_sync()
        user_dn_ad = ad.get_dn(username)
        guid = ad._ad.get(user_dn_ad)['objectGUID'][0]
        guid = decode_guid(guid)
        udm.remove_object('users/user', dn=user_dn)
        ad.wait_for_sync()
        ad.restore_object(user_dn_ad)
        ad.wait_for_sync()
        uoid = lo.getAttr(user_dn, attr='univentionObjectIdentifier')[0].decode('UTF-8')
        assert not ad.get_uoid2guid_mapping(old_uoid)
        assert guid == ad.get_uoid2guid_mapping(uoid)
