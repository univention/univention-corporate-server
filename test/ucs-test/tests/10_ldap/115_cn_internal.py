#!/usr/share/ucs-test/runner pytest-3 -s
## desc: Test cn=archive database
## exposure: dangerous

import subprocess
import time

import ldap
import pytest

from univention.admin.uexceptions import ldapError, noObject, permissionDenied
from univention.admin.uldap import access, getAdminConnection, getMachineConnection
from univention.testing.ucr import UCSTestConfigRegistry


BASE = 'cn=internal'
BASE_BLOCKLISTS = f'cn=blocklists,{BASE}'


def role():
    with UCSTestConfigRegistry() as ucr:
        return ucr.get('server/role')


def create_container(lo, cn, base):
    lo.search(base=base)
    dn = f'cn={cn},{base}'
    lo.add(dn, [('cn', cn.encode('UTF-8')), ('objectClass', b'organizationalRole')])
    lo.get(dn, required=True)
    lo.delete(dn)


@pytest.fixture()
def slapd_config():

    def _func(ucr_changes: list) -> None:
        with UCSTestConfigRegistry() as ucr:
            ucr.handler_set(ucr_changes)
            subprocess.check_call(['deb-systemd-invoke', 'restart', 'slapd'])
            time.sleep(3)

    yield _func

    subprocess.check_call(['deb-systemd-invoke', 'restart', 'slapd'])
    time.sleep(3)


@pytest.mark.skipif(role() not in ['domaincontroller_master'], reason="check additional acls only on syncprov/primary")
def test_blocklist_additional_group_acls_write(udm, random_string, slapd_config):
    password = 'univention'
    user_dn, name = udm.create_user(password=password)
    group_dn, group_name = udm.create_group(users=[user_dn])
    slapd_config([f'ldap/database/internal/acl/blocklists/groups/write=cn=justfortesting|{group_dn}'])
    lo = access(base=BASE_BLOCKLISTS, binddn=user_dn, bindpw=password)
    cn = random_string()
    create_container(lo, cn, BASE_BLOCKLISTS)
    with pytest.raises(noObject):
        create_container(lo, cn, BASE)


@pytest.mark.skipif(role() not in ['domaincontroller_master'], reason="check additional acls only on syncprov/primary")
def test_blocklist_additional_group_acls_read(udm, random_string, slapd_config):
    password = 'univention'
    user_dn, name = udm.create_user(password=password)
    group_dn, group_name = udm.create_group(users=[user_dn])
    slapd_config([f'ldap/database/internal/acl/blocklists/groups/read=cn=justfortesting|{group_dn}'])
    lo = access(base=BASE_BLOCKLISTS, binddn=user_dn, bindpw=password)
    cn = random_string()
    lo.search(base=BASE_BLOCKLISTS)
    with pytest.raises(permissionDenied):
        create_container(lo, cn, BASE_BLOCKLISTS)


@pytest.mark.skipif(role() in ['domaincontroller_master', 'domaincontroller_backup'], reason="database exists on primary and backup, but not on the other roles")
def test_no_local_database():
    lo, po = getMachineConnection(ldap_master=False)
    with pytest.raises(noObject):
        lo.search(base=BASE)


@pytest.mark.skipif(role() not in ['domaincontroller_master', 'domaincontroller_backup'], reason="database exists on primary and backup, but not on the other roles")
def test_local_database():
    lo, po = getMachineConnection(ldap_master=False)
    lo.search(base=BASE)


def test_write_with_machine_account_on_primary(random_string):
    lo, po = getMachineConnection(ldap_master=True)
    cn = random_string()
    create_container(lo, cn, BASE)


def test_write_domain_admins_on_primary(account, random_string, ucr):
    lo = access(host=ucr['ldap/master'], base=BASE, binddn=account.binddn, bindpw=account.bindpw)
    cn = random_string()
    create_container(lo, cn, BASE)


@pytest.mark.skipif(role() not in ['domaincontroller_master', 'domaincontroller_backup'], reason="no admin connection on this role")
def test_write_admin_connection_on_primary(random_string):
    lo, pos = getAdminConnection()
    cn = random_string()
    create_container(lo, cn, BASE)


def test_normal_user_can_not_read_internal(udm, ucr):
    dn, name = udm.create_user(password='univention')
    lo = access(host=ucr['ldap/master'], base=BASE, binddn=dn, bindpw='univention')
    with pytest.raises(noObject):
        lo.search(base=BASE)


def test_normal_user_can_read_blocklists(udm, ucr):
    dn, name = udm.create_user(password='univention')
    lo = access(host=ucr['ldap/master'], base=BASE, binddn=dn, bindpw='univention')
    lo.search(base=BASE_BLOCKLISTS)


@pytest.mark.skipif(role() not in ['domaincontroller_master'], reason="check primary config")
def test_primary_config(ucr):
    assert ucr.is_true('ldap/database/internal/syncprov')
    assert not ucr.is_true('ldap/database/internal/syncrepl')


@pytest.mark.skipif(role() not in ['domaincontroller_backup'], reason="check backup config")
def test_backup_config(ucr):
    assert ucr.is_true('ldap/database/internal/syncrepl')
    assert not ucr.is_true('ldap/database/internal/syncprov')


@pytest.mark.skipif(role() not in ['domaincontroller_backup'], reason="syncrepl only on backup")
def test_syncrepl_simple(random_string):
    lo_backup, po = getMachineConnection(ldap_master=False)
    lo_primary, po = getMachineConnection(ldap_master=True)
    cn = random_string()
    objects = 10000

    # create on primary
    for i in range(objects):
        dn = f'cn={cn}-{i},{BASE}'
        lo_primary.add(dn, [('cn', f'{cn}-{i}'.encode('UTF-8')), ('objectClass', b'organizationalRole')])

    # check on backup (just the last object)
    for i in range(30):
        time.sleep(1)
        try:
            lo_backup.get(dn, required=True)
            break
        except Exception:
            pass
    else:
        raise Exception('syncrepl to backup failed or too slow during create')
    # check every object
    for i in range(objects):
        dn = f'cn={cn}-{i},{BASE}'
        lo_backup.get(dn, required=True)

    # delete on primary
    for i in range(objects):
        dn = f'cn={cn}-{i},{BASE}'
        lo_primary.delete(dn)

    # check on backup (just the last object)
    for i in range(30):
        time.sleep(1)
        dn = lo_backup.get(dn)
        if not dn:
            break
    else:
        raise Exception('syncrepl to backup failed or too slow during delete')
    # check every object
    for i in range(objects):
        dn = f'cn={cn}-{i},{BASE}'
        with pytest.raises(ldap.NO_SUCH_OBJECT):
            lo_backup.get(dn, required=True)


@pytest.mark.skipif(role() not in ['domaincontroller_backup'], reason="check access on backup")
def test_access_on_backup(random_string, account, udm, ucr):

    # machine account can read
    lo, po = getMachineConnection(ldap_master=False)
    lo.search(base=BASE)
    cn = random_string()
    with pytest.raises(ldapError):
        create_container(lo, cn)

    # admins can read
    lo = access(host=ucr['ldap/server/name'], base=BASE, binddn=account.binddn, bindpw=account.bindpw)
    lo.search(base=BASE)
    cn = random_string()
    with pytest.raises(ldapError):
        create_container(lo, cn)

    # users can not read
    dn, name = udm.create_user(password='univention')
    lo = access(host=ucr['ldap/server/name'], base=BASE, binddn=dn, bindpw='univention')
    with pytest.raises(noObject):
        lo.search(base=BASE)

    # admin connectiob
    lo, pos = getAdminConnection()
    cn = random_string()
    create_container(lo, cn)


@pytest.mark.skipif(role() not in ['domaincontroller_backup'], reason="check additional acls only on syncrepl/backup")
def test_syncrepl_additional_group_acls_read(udm, random_string, slapd_config):
    password = 'univention'
    user_dn, name = udm.create_user(password=password)
    group_dn, group_name = udm.create_group(users=[user_dn])
    slapd_config([f'ldap/database/internal/acl/blocklists/groups/read=cn=justfortesting|{group_dn}'])
    lo = access(base=BASE, binddn=user_dn, bindpw=password)
    cn = random_string()
    lo.search(base=BASE)
    with pytest.raises(ldapError):
        create_container(lo, cn)
