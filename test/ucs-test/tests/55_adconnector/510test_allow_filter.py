#!/usr/share/ucs-test/runner pytest-3 -s
## desc: "Test the UCS<->AD sync with allowfilter in {sync} mode"
## exposure: dangerous
## packages:
##  - univention-ad-connector
## tags:
##  - skip_admember

import contextlib
from dataclasses import dataclass
from typing import Generator, List, Optional

import pytest
from ldap import NO_SUCH_OBJECT

from univention.config_registry import handler_set as ucr_set
from univention.testing import ucr as testing_ucr
from univention.testing.strings import random_string
from univention.testing.udm import UCSTestUDM
from univention.testing.utils import LDAPObjectNotFound, LDAPObjectValueMissing

from adconnector import ADConnection, connector_running_on_this_host, restart_adconnector, wait_for_sync


# This is something weird. The `adconnector.ADConnection()` MUST be
# instantiated, before `UCSTestUDM` is imported.
AD = ADConnection()


@dataclass
class DomObject:
    name: str
    udm_module: str
    udm_filter: str
    ad_filter: str
    udm_dn: str
    ad_dn: str


@contextlib.contextmanager
def allow_filter_setup(sync_mode: str) -> Generator[UCSTestUDM, None, None]:
    with UCSTestUDM() as udm:
        try:
            with testing_ucr.UCSTestConfigRegistry():
                config = [
                    f"connector/ad/mapping/syncmode={sync_mode}",
                ]
                ucr_set(config)
                restart_adconnector()
                yield udm
        finally:
            restart_adconnector()
    wait_for_sync()


def create_objects_in_ucs(
    udm: UCSTestUDM,
    username: Optional[str] = None,
    groupname: Optional[str] = None,
    containername: Optional[str] = None,
    ouname: Optional[str] = None,
    wait: bool = True
) -> List[DomObject]:

    objects = []

    name = username if username else random_string()
    dn, _ = udm.create_user('users/user', username=name)
    objects.append(
        DomObject(
            name=name,
            ad_filter=f'sAMAccountName={name}',
            udm_filter=f'uid={name}',
            udm_module='users/user',
            udm_dn=dn,
            ad_dn=f'cn={name},cn=users,{AD.adldapbase}'
        )
    )
    name = groupname if groupname else random_string()
    dn = udm.create_object('groups/group', name=name)
    objects.append(
        DomObject(
            name=name,
            ad_filter=f'sAMAccountName={name}',
            udm_filter=f'cn={name}',
            udm_module='groups/group',
            udm_dn=dn,
            ad_dn=f'cn={name},{AD.adldapbase}'
        )
    )
    name = containername if containername else random_string()
    dn = udm.create_object('container/cn', name=name)
    objects.append(
        DomObject(
            name=name,
            ad_filter=f'cn={name}',
            udm_filter=f'cn={name}',
            udm_module='container/cn',
            udm_dn=dn,
            ad_dn=f'cn={name},{AD.adldapbase}'
        )
    )
    name = ouname if ouname else random_string()
    dn = udm.create_object('container/ou', name=name)
    objects.append(
        DomObject(
            name=name,
            ad_filter=f'ou={name}',
            udm_filter=f'ou={name}',
            udm_module='container/ou',
            udm_dn=dn,
            ad_dn=f'ou={name},{AD.adldapbase}'
        )
    )
    if wait:
        wait_for_sync()
    return objects


def create_objects_in_ad(ad: ADConnection, wait: bool = True) -> List[DomObject]:
    objects = []
    name = random_string()
    dn = ad.createuser(name)
    objects.append(
        DomObject(
            name=name,
            ad_filter=f'sAMAccountName={name}',
            udm_filter=f'uid={name}',
            udm_module='users/user',
            ad_dn=dn,
            udm_dn=None,
        )
    )
    name = random_string()
    dn = ad.group_create(name)
    objects.append(
        DomObject(
            name=name,
            ad_filter=f'sAMAccountName={name}',
            udm_filter=f'cn={name}',
            udm_module='groups/group',
            ad_dn=dn,
            udm_dn=None,
        )
    )
    name = random_string()
    dn = ad.container_create(name)
    objects.append(
        DomObject(
            name=name,
            ad_filter=f'cn={name}',
            udm_filter=f'cn={name}',
            udm_module='container/cn',
            ad_dn=dn,
            udm_dn=None,
        )
    )
    name = random_string()
    dn = ad.createou(name)
    objects.append(
        DomObject(
            name=name,
            ad_filter=f'ou={name}',
            udm_filter=f'ou={name}',
            udm_module='container/ou',
            ad_dn=dn,
            udm_dn=None,
        )
    )
    if wait:
        wait_for_sync()
    return objects


@pytest.mark.parametrize("sync_mode", ["sync"])
@pytest.mark.skipif(not connector_running_on_this_host(), reason="Univention AD Connector not configured.")
def test_create(sync_mode: str) -> None:

    allowed_user = random_string()
    allowed_group = random_string()
    allowed_container = random_string()
    allowed_ou = random_string()

    with allow_filter_setup(sync_mode) as udm:

        config = [
            f"connector/ad/mapping/user/allowfilter=(|(uid={allowed_user})(sAMAccountName={allowed_user}))",
            f"connector/ad/mapping/group/allowfilter=cn={allowed_group}",
            f"connector/ad/mapping/container/allowfilter=cn={allowed_container}",
            f"connector/ad/mapping/ou/allowfilter=ou={allowed_ou}",
        ]
        ucr_set(config)
        restart_adconnector()

        # check objects created in UCS are not synced
        if sync_mode in ('sync', 'write'):
            objs = create_objects_in_ucs(udm)
            for obj in objs:
                with pytest.raises(NO_SUCH_OBJECT):
                    AD.search(obj.ad_filter, required=True)

        # check objects created in AD are not synced
        if sync_mode in ('sync', 'read'):
            objs = create_objects_in_ad(AD)
            try:
                for obj in objs:
                    with pytest.raises(NO_SUCH_OBJECT):
                        udm._primary_lo.search(filter=obj.udm_filter, attr=[], required=True)
            finally:
                # cleanup
                for obj in objs:
                    AD.delete(obj.ad_dn)

        if sync_mode in ('sync', 'write'):
            # check sync works if filter applies
            objs = create_objects_in_ucs(
                udm,
                username=allowed_user,
                groupname=allowed_group,
                containername=allowed_container,
                ouname=allowed_ou,
            )
            for obj in objs:
                AD.search(obj.ad_filter, required=True)


@pytest.mark.parametrize("sync_mode", ["sync"])
@pytest.mark.skipif(not connector_running_on_this_host(), reason="Univention AD Connector not configured.")
def test_modify(sync_mode: str) -> None:

    allowed_user = random_string()
    allowed_group = random_string()
    allowed_container = random_string()
    allowed_ou = random_string()

    with allow_filter_setup(sync_mode) as udm:

        objs = create_objects_in_ucs(udm)
        for obj in objs:
            AD.search(obj.ad_filter, required=True)

        config = [
            f"connector/ad/mapping/user/allowfilter=(|(uid={allowed_user})(sAMAccountName={allowed_user}))",
            f"connector/ad/mapping/group/allowfilter=cn={allowed_group}",
            f"connector/ad/mapping/container/allowfilter=cn={allowed_container}",
            f"connector/ad/mapping/ou/allowfilter=ou={allowed_ou}",
        ]
        ucr_set(config)
        restart_adconnector()

        # check modification in UCS is not synced
        if sync_mode in ('sync', 'write'):
            for obj in objs:
                udm.modify_object(obj.udm_module, dn=obj.udm_dn, description='changed in UCS')
            wait_for_sync()
            for obj in objs:
                with pytest.raises(AssertionError):
                    AD.verify_object(obj.ad_dn, {'description': 'changed in UCS'})

        # check modification in AD is not synced
        if sync_mode in ('sync', 'read'):
            for obj in objs:
                AD.set_attribute(obj.ad_dn, 'description', 'changed in AD'.encode('UTF-8'))
                AD.verify_object(obj.ad_dn, {'description': 'changed in AD'})
            wait_for_sync()
            for obj in objs:
                with pytest.raises(LDAPObjectValueMissing):
                    udm.verify_ldap_object(obj.udm_dn, expected_attr={'description': ['changed in AD']}, retry_count=3, delay=1)

        # check modification works
        if sync_mode in ('sync'):
            objs = create_objects_in_ucs(
                udm,
                username=allowed_user,
                groupname=allowed_group,
                containername=allowed_container,
                ouname=allowed_ou,
            )
            for obj in objs:
                AD.set_attribute(obj.ad_dn, 'description', 'changed in AD'.encode('UTF-8'))
                AD.verify_object(obj.ad_dn, {'description': 'changed in AD'})
            wait_for_sync()
            for obj in objs:
                udm.verify_ldap_object(obj.udm_dn, expected_attr={'description': ['changed in AD']})


@pytest.mark.parametrize("sync_mode", ["sync"])
@pytest.mark.skipif(not connector_running_on_this_host(), reason="Univention AD Connector not configured.")
def test_delete(sync_mode: str) -> None:

    allowed_user = random_string()
    allowed_group = random_string()
    allowed_container = random_string()
    allowed_ou = random_string()

    allowed_user2 = random_string()
    allowed_group2 = random_string()
    allowed_container2 = random_string()
    allowed_ou2 = random_string()

    with allow_filter_setup(sync_mode) as udm:

        no_sync_objs_udm_delete = create_objects_in_ucs(udm)
        no_sync_objs_ad_delete = create_objects_in_ucs(udm)
        sync_objs_ad_delete = create_objects_in_ucs(
            udm,
            username=allowed_user,
            groupname=allowed_group,
            containername=allowed_container,
            ouname=allowed_ou,
        )
        sync_objs_udm_delete = create_objects_in_ucs(
            udm,
            username=allowed_user2,
            groupname=allowed_group2,
            containername=allowed_container2,
            ouname=allowed_ou2,

        )

        config = [
            f"connector/ad/mapping/user/allowfilter=(|(uid={allowed_user})(cn={allowed_user})(uid={allowed_user2})(cn={allowed_user2}))",
            f"connector/ad/mapping/group/allowfilter=(|(cn={allowed_group})(cn={allowed_group})(cn={allowed_group2})(cn={allowed_group2}))",
            f"connector/ad/mapping/container/allowfilter=(|(cn={allowed_container})(cn={allowed_container2}))",
            f"connector/ad/mapping/ou/allowfilter=(|(ou={allowed_ou})(ou={allowed_ou2}))",
        ]
        ucr_set(config)
        restart_adconnector()

        # check delete in UCS is not synced
        if sync_mode in ('sync', 'write'):
            for obj in no_sync_objs_udm_delete:
                udm.remove_object(obj.udm_module, dn=obj.udm_dn)
            wait_for_sync()
            for obj in no_sync_objs_udm_delete:
                AD.verify_object(obj.ad_dn, {'name': obj.name})
            # cleanup
            for obj in no_sync_objs_udm_delete:
                AD.delete(obj.ad_dn)

        # check delete in AD is not synced
        if sync_mode in ('sync', 'read'):
            for obj in no_sync_objs_ad_delete:
                AD.delete(obj.ad_dn)
            wait_for_sync()
            for obj in no_sync_objs_ad_delete:
                udm.verify_ldap_object(obj.udm_dn)

        # check delete in AD works if filter matches
        if sync_mode in ('sync', 'read'):
            for obj in sync_objs_ad_delete:
                AD.delete(obj.ad_dn)
            wait_for_sync()
            for obj in sync_objs_ad_delete:
                with pytest.raises(LDAPObjectNotFound):
                    print(obj)
                    udm.verify_ldap_object(obj.udm_dn, retry_count=3, delay=1)

        # check delete in UCS works if filter matches
        if sync_mode in ('sync', 'write'):
            for obj in sync_objs_udm_delete:
                udm.remove_object(obj.udm_module, dn=obj.udm_dn)
            wait_for_sync()
            for obj in sync_objs_udm_delete:
                with pytest.raises(NO_SUCH_OBJECT):
                    AD.search(obj.ad_filter, required=True)


@pytest.mark.parametrize("sync_mode", ["sync"])
@pytest.mark.skipif(not connector_running_on_this_host(), reason="Univention AD Connector not configured.")
def test_filter_matches_after_modification(sync_mode: str) -> None:

    with allow_filter_setup(sync_mode) as udm:
        config = [
            'connector/ad/mapping/user/allowfilter=(description=sync)',
        ]
        ucr_set(config)
        restart_adconnector()

        # create and modify in UCS, check in AD
        if sync_mode in ('sync', 'write'):
            udm_dn, username = udm.create_user('users/user')
            ad_dn = f'cn={username},cn=users,{AD.adldapbase}'
            wait_for_sync()
            with pytest.raises(AssertionError):
                AD.verify_object(ad_dn, {'name': username})
            udm.modify_object('users/user', dn=udm_dn, description='sync')
            wait_for_sync()
            AD.verify_object(ad_dn, {'name': username})

        # create and modify in AD, check in UCS
        if sync_mode in ('sync', 'read'):
            name = random_string()
            ad_dn = AD.createuser(name)
            try:
                udm_dn = f'uid={name},cn=users,{udm.LDAP_BASE}'
                wait_for_sync()
                with pytest.raises(LDAPObjectNotFound):
                    udm.verify_ldap_object(udm_dn, retry_count=3, delay=1)
                AD.set_attribute(ad_dn, 'description', 'sync'.encode('UTF-8'))
                wait_for_sync()
                udm.verify_ldap_object(udm_dn)
            finally:
                AD.delete(ad_dn)


@pytest.mark.parametrize("sync_mode", ["sync"])
@pytest.mark.skipif(not connector_running_on_this_host(), reason="Univention AD Connector not configured.")
def test_filter_no_longer_matches(sync_mode: str) -> None:

    with allow_filter_setup(sync_mode) as udm:
        config = [
            'connector/ad/mapping/user/allowfilter=(description=sync)',
        ]
        ucr_set(config)
        restart_adconnector()

        # create and modify in UCS, check in AD
        if sync_mode in ('sync', 'write'):
            udm_dn, username = udm.create_user('users/user', description='sync')
            ad_dn = f'cn={username},cn=users,{AD.adldapbase}'
            wait_for_sync()
            AD.verify_object(ad_dn, {'name': username})
            udm.modify_object('users/user', dn=udm_dn, description='nosync')
            wait_for_sync()
            # TODO is this OK?
            # Problem: the allowed attribute has been removed from the object,
            # this change is not synced to the other side
            AD.verify_object(ad_dn, {'name': username, 'description': 'sync'})

        # create and modify in AD, check in UCS
        if sync_mode in ('sync', 'read'):
            name = random_string()
            ad_dn = AD.createuser(name, description='sync'.encode('UTF-8'))
            try:
                udm_dn = f'uid={name},cn=users,{udm.LDAP_BASE}'
                wait_for_sync()
                udm.verify_ldap_object(udm_dn)
                AD.set_attribute(ad_dn, 'description', 'nosync'.encode('UTF-8'))
                wait_for_sync()
                # TODO is this OK?
                udm.verify_ldap_object(udm_dn, expected_attr={'description': ['sync']})
            finally:
                AD.delete(ad_dn)


@pytest.mark.parametrize("sync_mode", ["sync"])
@pytest.mark.skipif(not connector_running_on_this_host(), reason="Univention AD Connector not configured.")
def test_allowsubtree_higher_priority_than_allowfilter(sync_mode: str) -> None:

    with allow_filter_setup(sync_mode) as udm:
        username = random_string()
        ucr_set([f'connector/ad/mapping/user/allowfilter=(uid={username})'])
        restart_adconnector()

        # check modify from UCS does not work if allowsubtree does not match
        if sync_mode in ('sync', 'write'):
            udm_dn, _ = udm.create_user('users/user', username=username)
            ad_dn = f'cn={username},cn=users,{AD.adldapbase}'
            wait_for_sync()
            # ok, it is synced
            AD.verify_object(ad_dn, {'name': username})
            # now check that it is no longer synced with allowsubtree config
            ucr_set(['connector/ad/mapping/allowsubtree/test1/ucs=cn=nothing'])
            restart_adconnector()
            udm.modify_object('users/user', dn=udm_dn, description='changed in UCS')
            with pytest.raises(AssertionError):
                AD.verify_object(ad_dn, {'description': 'changed in UCS'})

        # check create in AD is not synced to UCS if allowsubtree does not match
        if sync_mode in ('sync', 'read'):
            username = random_string()
            ucr_set([
                f'connector/ad/mapping/user/allowfilter=(|(uid={username})(sAMAccountName={username}))',
                'connector/ad/mapping/allowsubtree/test1/ucs=cn=nothing',
            ])
            restart_adconnector()
            ad_dn = AD.createuser(username, description='sync'.encode('UTF-8'))
            wait_for_sync()
            try:
                with pytest.raises(NO_SUCH_OBJECT):
                    udm._primary_lo.search(filter=f'uid={username}', attr=[], required=True)
                # make allowsubtree match and check sync works
                ucr_set([
                    f'connector/ad/mapping/allowsubtree/test1/ucs={udm.LDAP_BASE}',
                    f'connector/ad/mapping/allowsubtree/test1/ucs={AD.adldapbase}',
                ])
                restart_adconnector()
                AD.set_attribute(ad_dn, 'description', 'Changed in AD'.encode('UTF-8'))
                wait_for_sync()
                udm._primary_lo.search(filter=f'uid={username}', attr=[], required=True)
            finally:
                AD.delete(ad_dn)
