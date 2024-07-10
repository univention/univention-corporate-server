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

    with allow_filter_setup(sync_mode) as udm:

        objs1 = create_objects_in_ucs(udm)
        objs2 = create_objects_in_ucs(udm)
        objs3 = create_objects_in_ucs(
            udm,
            username=allowed_user,
            groupname=allowed_group,
            containername=allowed_container,
            ouname=allowed_ou,
        )
        for obj in objs1 + objs2 + objs3:
            AD.search(obj.ad_filter, required=True)

        # TODO when deleting a matching object in AD we have the problem that
        # the filter attribute from the AD object can get invalid because
        # AD adds \DEL:ID to the rdn attribute and other attributes are deleted
        # at this point we don't have the full (old) object for the filter match
        # ->
        #  container CN=oxud50ug2c,DC=ucs,DC=test
        #  allow filter (cn=oxud50ug2c)
        #  object after delete in AD
        #    'cn': [b'oxud50ug2c\nDEL:3206cf5b-120d-4dd9-bc7b-21aeb20da325']
        #  sync to UCS fails because (cn=oxud50ug2c) no longer matches

        config = [
            f"connector/ad/mapping/user/allowfilter=(|(uid={allowed_user})(sAMAccountName={allowed_user}))",
            f"connector/ad/mapping/group/allowfilter=(|(cn={allowed_group})(sAMAccountName={allowed_group}))",
            f"connector/ad/mapping/container/allowfilter=(|(cn={allowed_container})(description=sync))",
            f"connector/ad/mapping/ou/allowfilter=(|(ou={allowed_ou})(description=sync))",
        ]
        ucr_set(config)
        restart_adconnector()

        # check delete in UCS is not synced
        if sync_mode in ('sync', 'write'):
            for obj in objs1:
                udm.remove_object(obj.udm_module, dn=obj.udm_dn)
            wait_for_sync()
            for obj in objs1:
                AD.verify_object(obj.ad_dn, {'name': obj.name})
            # cleanup
            for obj in objs1:
                AD.delete(obj.ad_dn)

        # check delete in AD is not synced
        if sync_mode in ('sync', 'read'):
            for obj in objs2:
                AD.delete(obj.ad_dn)
            wait_for_sync()
            for obj in objs2:
                udm.verify_ldap_object(obj.udm_dn)

        # check delete works if filter matches
        if sync_mode in ('sync'):
            for obj in objs3:
                AD.delete(obj.ad_dn)
            wait_for_sync()
            for obj in objs3:
                if obj.udm_module in ['users/user', 'groups/group']:
                    with pytest.raises(LDAPObjectNotFound):
                        udm.verify_ldap_object(obj.udm_dn, retry_count=3, delay=1)


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

# TODO
# test_subtree_filter_prioriry
# test_filter_no_longer_matches
