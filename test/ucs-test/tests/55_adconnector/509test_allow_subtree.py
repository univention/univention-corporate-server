#!/usr/share/ucs-test/runner pytest-3 -s
## desc: "Test the UCS<->AD sync with allow_subtree in {read,write,sync} mode with users"
## exposure: dangerous
## packages:
##  - univention-ad-connector
## tags:
##  - skip_admember

import contextlib
from collections.abc import Generator
from dataclasses import dataclass

import pytest

from univention.config_registry import handler_set as ucr_set
from univention.testing import ucr as testing_ucr
from univention.testing.connector_common import delete_con_user
from univention.testing.strings import random_string
from univention.testing.udm import UCSTestUDM
from univention.testing.utils import LDAPObjectNotFound, LDAPObjectValueMissing

from adconnector import ADConnection, connector_running_on_this_host, restart_adconnector, wait_for_sync


# This is something weird. The `adconnector.ADConnection()` MUST be
# instantiated, before `UCSTestUDM` is imported.
AD = ADConnection()


@dataclass
class SubTree:
    name: str
    udm_position: str | None = None
    ad_position: str | None = None
    udm_dn: str | None = None
    ad_dn: str | None = None
    objects: str | None = None


@dataclass
class DomObject:
    name: str
    ad_rdn: str
    ad_position: str
    udm_rdn: str
    udm_position: str
    udm_module: str
    old_udm_position: str | None = None
    old_ad_position: str | None = None

    @property
    def ad_dn(self):
        return f'{self.ad_rdn},{self.ad_position}'

    @property
    def udm_dn(self):
        return f'{self.udm_rdn},{self.udm_position}'

    @property
    def old_ad_dn(self):
        return f'{self.ad_rdn},{self.old_ad_position}'

    @property
    def old_udm_dn(self):
        return f'{self.udm_rdn},{self.old_udm_position}'


@contextlib.contextmanager
def allow_subtree_setup(
    sync_mode: str,
    pre_create_objects: bool = False,
    only_ucs: bool = False,
) -> Generator[tuple[list, list, UCSTestUDM], None, None]:
    with UCSTestUDM() as udm:
        try:
            with testing_ucr.UCSTestConfigRegistry() as ucr:
                # explicitly allow cn=cn1-allowed,base
                # explicitly allow ou=ou2-allowed,ou=ou1,base
                # so implicitly:
                # - don't allow ou=ou1,base
                # - don't allow cn=users,base
                # - don't allow ou=ou3,ou=ou2-allowed,ou=ou1,base  # using ignoresubtree
                # NOTE: consider https://help.univention.com/t/q-a-can-i-create-ous-under-cn-computers/13539
                allowed1 = SubTree(name='cn1-allowed')
                allowed1.udm_position = ucr['ldap/base']
                allowed1.ad_position = ucr['connector/ad/ldap/base']
                allowed1.udm_dn = f'cn={allowed1.name},{allowed1.udm_position}'
                allowed1.ad_dn = f'cn={allowed1.name},{allowed1.ad_position}'

                not_allowed1 = SubTree(name='ou1')
                not_allowed1.udm_position = ucr['ldap/base']
                not_allowed1.ad_position = ucr['connector/ad/ldap/base']
                not_allowed1.udm_dn = f'ou={not_allowed1.name},{not_allowed1.udm_position}'
                not_allowed1.ad_dn = f'ou={not_allowed1.name},{not_allowed1.ad_position}'

                allowed2 = SubTree(name='ou2-allowed')
                allowed2.udm_position = not_allowed1.udm_dn  # position below not explicitly allowed OU
                allowed2.ad_position = not_allowed1.ad_dn    # position below not explicitly allowed OU
                allowed2.udm_dn = f'ou={allowed2.name},{allowed2.udm_position}'
                allowed2.ad_dn = f'ou={allowed2.name},{allowed2.ad_position}'

                not_allowed2 = SubTree(name='users')        # test not allowing the standard cn=users container
                not_allowed2.udm_position = ucr['ldap/base']
                not_allowed2.ad_position = ucr['connector/ad/ldap/base']
                not_allowed2.udm_dn = f'cn={not_allowed2.name},{not_allowed2.udm_position}'
                not_allowed2.ad_dn = f'cn={not_allowed2.name},{not_allowed2.ad_position}'

                not_allowed3 = SubTree(name='ou3')
                not_allowed3.udm_position = allowed2.udm_dn  # position below explicitly allowed OU
                not_allowed3.ad_position = allowed2.ad_dn    # position below explicitly allowed OU
                not_allowed3.udm_dn = f'ou={not_allowed3.name},{not_allowed3.udm_position}'
                not_allowed3.ad_dn = f'ou={not_allowed3.name},{not_allowed3.ad_position}'
                # create container and optionally some objects in the containers
                if ucr['connector/ad/mapping/syncmode'] not in ('sync', 'write'):
                    # configure connector for sync
                    ucr_set(
                        [
                            "connector/ad/mapping/syncmode=sync",
                        ],
                    )
                    restart_adconnector()
                udm.create_object('container/cn', name=allowed1.name, position=allowed1.udm_position)
                udm.create_object('container/ou', name=not_allowed1.name)
                udm.create_object('container/ou', name=allowed2.name, position=allowed2.udm_position)
                # udm.create_object('container/cn', name=not_allowed2.name)   # not necessary to provision/remove, that's cn=users
                udm.create_object('container/ou', name=not_allowed3.name, position=not_allowed3.udm_position)
                if pre_create_objects:
                    not_allowed1.objects = create_objects_in_ucs(udm, not_allowed1, wait=False)
                    not_allowed2.objects = create_objects_in_ucs(udm, not_allowed2, wait=False)
                    not_allowed3.objects = create_objects_in_ucs(udm, not_allowed3, wait=False)
                    allowed1.objects = create_objects_in_ucs(udm, allowed1, wait=False)
                    allowed2.objects = create_objects_in_ucs(udm, allowed2, wait=False)
                wait_for_sync()
                AD.verify_object(allowed1.ad_dn, {'name': allowed1.name})
                AD.verify_object(allowed2.ad_dn, {'name': allowed2.name})
                AD.verify_object(not_allowed1.ad_dn, {'name': not_allowed1.name})
                # AD.verify_object(not_allowed2.ad_dn, {'name': not_allowed2.name})   # that's cn=users
                AD.verify_object(not_allowed3.ad_dn, {'name': not_allowed3.name})
                # configure connector
                ucr_set(
                    [
                        f"connector/ad/mapping/allowsubtree/test1/ucs={allowed1.udm_dn}",
                        f"connector/ad/mapping/allowsubtree/test1/ad={allowed1.ad_dn}",
                        f"connector/ad/mapping/allowsubtree/test2/ucs={allowed2.udm_dn}",
                        f"connector/ad/mapping/allowsubtree/test2/ad={allowed2.ad_dn}",
                        f"connector/ad/mapping/ignoresubtree/test3-ucs={not_allowed3.udm_dn}",
                        f"connector/ad/mapping/ignoresubtree/test3-ad={not_allowed3.ad_dn}",
                        f"connector/ad/mapping/syncmode={sync_mode}",
                    ],
                )
                restart_adconnector()
            yield ([allowed1, allowed2], [not_allowed1, not_allowed2, not_allowed3], udm)
        finally:
            restart_adconnector()
    wait_for_sync()


def create_objects_in_ucs(udm: UCSTestUDM, tree: SubTree, wait: bool = True) -> [DomObject]:
    objects = []
    _, username = udm.create_user(position=tree.udm_dn)
    objects.append(
        DomObject(
            name=username,
            ad_rdn=f'cn={username}',
            ad_position=tree.ad_dn,
            udm_rdn=f'uid={username}',
            udm_position=tree.udm_dn,
            udm_module='users/user',
        ),
    )
    # TODO group
    if wait:
        wait_for_sync()
    return objects


def create_objects_in_ad(ad: ADConnection, tree: SubTree, wait: bool = True) -> [DomObject]:
    objects = []
    username = random_string()
    ad.createuser(username, position=tree.ad_dn)
    objects.append(
        DomObject(
            name=username,
            ad_rdn=f'cn={username}',
            ad_position=tree.ad_dn,
            udm_rdn=f'uid={username}',
            udm_position=tree.udm_dn,
            udm_module='users/user',
        ),
    )
    # TODO group
    if wait:
        wait_for_sync()
    return objects


def move_to_subtree_in_ucs(udm: UCSTestUDM, obj: DomObject, tree: SubTree) -> None:
    udm.move_object(obj.udm_module, dn=obj.udm_dn, position=tree.udm_dn)
    obj.old_udm_position = obj.udm_position
    obj.old_ad_position = obj.ad_position
    obj.udm_position = tree.udm_dn
    obj.ad_position = tree.ad_dn


def move_to_subtree_in_ad(ad: ADConnection, obj: DomObject, tree: SubTree) -> None:
    ad.move(obj.ad_dn, f'{obj.ad_rdn},{tree.ad_dn}')
    obj.old_udm_position = obj.udm_position
    obj.old_ad_position = obj.ad_position
    obj.udm_position = tree.udm_dn
    obj.ad_position = tree.ad_dn


# @pytest.mark.parametrize("sync_mode", ["read", "sync"])
@pytest.mark.parametrize("sync_mode", ["sync"])
@pytest.mark.skipif(not connector_running_on_this_host(), reason="Univention AD Connector not configured.")
def test_create(sync_mode: str) -> None:
    with allow_subtree_setup(sync_mode) as (allowed, denied, udm):
        # check denied for other subtrees
        for tree in denied:
            if sync_mode in ('sync', 'write'):
                # check objects created in UCS are not synced to AD
                for obj in create_objects_in_ucs(udm, tree):
                    with pytest.raises(AssertionError):
                        AD.verify_object(obj.ad_dn, {'name': obj.name})
                    udm.verify_ldap_object(obj.udm_dn)
                # check objects created in AD are not synced to UCS
                for obj in create_objects_in_ad(AD, tree):
                    AD.verify_object(obj.ad_dn, {'name': obj.name})
                    with pytest.raises(LDAPObjectNotFound):
                        udm.verify_ldap_object(obj.udm_dn, retry_count=3, delay=1)
        # check sync works
        for tree in allowed:
            if sync_mode in ('sync', 'write'):
                for obj in create_objects_in_ucs(udm, tree):
                    AD.verify_object(obj.ad_dn, {'name': obj.name})
                    udm.verify_ldap_object(obj.udm_dn)
            if sync_mode in ('sync', 'read'):
                for obj in create_objects_in_ad(AD, tree):
                    AD.verify_object(obj.ad_dn, {'name': obj.name})
                    udm.verify_ldap_object(obj.udm_dn)


# @pytest.mark.parametrize("sync_mode", ["read", "sync"])
@pytest.mark.parametrize("sync_mode", ["sync"])
@pytest.mark.skipif(not connector_running_on_this_host(), reason="Univention AD Connector not configured.")
def test_modify(sync_mode: str) -> None:
    with allow_subtree_setup(sync_mode, pre_create_objects=True) as (allowed, denied, udm):
        for tree in denied:
            if sync_mode in ('sync', 'write'):
                for obj in tree.objects:
                    # modify in UCS, check no change in AD
                    udm.modify_object(obj.udm_module, dn=obj.udm_dn, description='changed in UCS')
                    udm.verify_ldap_object(obj.udm_dn, expected_attr={'description': ['changed in UCS']})
                    wait_for_sync()
                    with pytest.raises(AssertionError):
                        AD.verify_object(obj.ad_dn, {'description': 'changed in UCS'})
            if sync_mode in ('sync', 'read'):
                for obj in tree.objects:
                    # modify in AD, check no change in UCS
                    AD.set_attribute(obj.ad_dn, 'description', b'changed in AD')
                    AD.verify_object(obj.ad_dn, {'description': 'changed in AD'})
                    wait_for_sync()
                    with pytest.raises(LDAPObjectValueMissing):
                        udm.verify_ldap_object(obj.udm_dn, expected_attr={'description': ['changed in AD']}, retry_count=3, delay=1)
        # check sync works
        for tree in allowed:
            if sync_mode in ('sync', 'write'):
                for obj in tree.objects:
                    # modify in UCS, check change in AD
                    udm.modify_object(obj.udm_module, dn=obj.udm_dn, description='changed in UCS')
                    udm.verify_ldap_object(obj.udm_dn, expected_attr={'description': ['changed in UCS']})
                    wait_for_sync()
                    AD.verify_object(obj.ad_dn, {'description': 'changed in UCS'})
            if sync_mode in ('sync', 'read'):
                for obj in tree.objects:
                    # modify in AD, check cange in UCS
                    AD.set_attribute(obj.ad_dn, 'description', b'changed in AD')
                    AD.verify_object(obj.ad_dn, {'description': 'changed in AD'})
                    wait_for_sync()
                    udm.verify_ldap_object(obj.udm_dn, expected_attr={'description': ['changed in AD']})


# @pytest.mark.parametrize("sync_mode", ["read", "sync"])
@pytest.mark.parametrize("sync_mode", ["sync"])
@pytest.mark.skipif(not connector_running_on_this_host(), reason="Univention AD Connector not configured.")
def test_move_into_allowed_subtree(sync_mode: str) -> None:
    with allow_subtree_setup(sync_mode) as (allowed, denied, udm):
        # create objects in denied subtree in UCS/AD
        # and move to allowed subtree, check object is created
        allowed_subtree = allowed[0]
        denied_subtree = denied[0]
        # create/move in UCS and check AD
        if sync_mode in ['sync', 'write']:
            objects = create_objects_in_ucs(udm, denied_subtree)
            for obj in objects:
                with pytest.raises(AssertionError):
                    AD.verify_object(obj.ad_dn, {'name': obj.name})
                move_to_subtree_in_ucs(udm, obj, allowed_subtree)
            wait_for_sync()
            for obj in objects:
                AD.verify_object(obj.ad_dn, {'name': obj.name})
                udm.verify_ldap_object(obj.udm_dn)
        allowed_subtree = allowed[1]
        denied_subtree = denied[1]
        # create/move in AD and check UCS
        if sync_mode in ['sync', 'read']:
            objects = create_objects_in_ad(AD, denied_subtree)
            for obj in objects:
                with pytest.raises(LDAPObjectNotFound):
                    udm.verify_ldap_object(obj.udm_dn, retry_count=3, delay=1)
                move_to_subtree_in_ad(AD, obj, allowed_subtree)
            wait_for_sync()
            for obj in objects:
                AD.verify_object(obj.ad_dn, {'name': obj.name})
                udm.verify_ldap_object(obj.udm_dn)


# @pytest.mark.parametrize("sync_mode", ["read", "sync", "write"])
@pytest.mark.parametrize("sync_mode", ["sync"])
@pytest.mark.skipif(not connector_running_on_this_host(), reason="Univention AD Connector not configured.")
def test_move_out_of_allowed_subtree(sync_mode: str) -> None:
    with allow_subtree_setup(sync_mode) as (allowed, denied, udm):
        # create object in allowed subtree in UCS/AD
        # move out of allowed subtree and check that object is removed
        allowed_subtree = allowed[0]
        denied_subtree = denied[0]
        # create/move in UCS, check AD
        if sync_mode in ['sync', 'write']:
            objects = create_objects_in_ucs(udm, allowed_subtree)
            for obj in objects:
                AD.verify_object(obj.ad_dn, {'name': obj.name})
                move_to_subtree_in_ucs(udm, obj, denied_subtree)
            wait_for_sync()
            for obj in objects:
                with pytest.raises(AssertionError):
                    AD.verify_object(obj.ad_dn, {'name': obj.name})
                with pytest.raises(AssertionError):
                    AD.verify_object(obj.old_ad_dn, {'name': obj.name})
        allowed_subtree = allowed[1]
        denied_subtree = denied[1]
        # create/move in AD, check UCS
        if sync_mode in ['sync', 'read']:
            objects = create_objects_in_ad(AD, allowed_subtree)
            for obj in objects:
                udm.verify_ldap_object(obj.udm_dn)
                move_to_subtree_in_ad(AD, obj, denied_subtree)
            wait_for_sync()
            for obj in objects:
                with pytest.raises(LDAPObjectNotFound):
                    udm.verify_ldap_object(obj.udm_dn, retry_count=3, delay=1)
                with pytest.raises(LDAPObjectNotFound):
                    udm.verify_ldap_object(obj.old_udm_dn, retry_count=3, delay=1)


@pytest.mark.parametrize("sync_mode", ["sync"])
@pytest.mark.skipif(not connector_running_on_this_host(), reason="Univention AD Connector not configured.")
def test_ignored_object_is_not_moved(sync_mode: str, ucr) -> None:
    with allow_subtree_setup(sync_mode, pre_create_objects=True) as (allowed, denied, udm):  # noqa: F841
        username = allowed[0].objects[0].name
        udm_dn = allowed[0].objects[0].udm_dn
        ad_dn = allowed[0].objects[0].ad_dn
        AD.verify_object(ad_dn, {'name': username})
        # set to ignore
        ignorelist = f'{ucr["connector/ad/mapping/user/ignorelist"]},{username}'
        ucr_set([f'connector/ad/mapping/user/ignorelist={ignorelist}'])
        restart_adconnector()
        # move object in UCS to a different allowed subtree and check it didn't got moved in AD
        udm.move_object('users/user', dn=udm_dn, position=allowed[1].udm_dn)
        wait_for_sync()
        AD.verify_object(ad_dn, {'name': username})
        # cleanup
        delete_con_user(AD, ad_dn, udm_dn, wait_for_sync)


@pytest.mark.parametrize("sync_mode", ["sync"])
@pytest.mark.skipif(not connector_running_on_this_host(), reason="Univention AD Connector not configured.")
def test_ignored_object_is_not_removed(sync_mode: str, ucr) -> None:
    with allow_subtree_setup(sync_mode, pre_create_objects=True) as (allowed, denied, udm):  # noqa: F841
        username = allowed[0].objects[0].name
        udm_dn = allowed[0].objects[0].udm_dn
        ad_dn = allowed[0].objects[0].ad_dn
        AD.verify_object(ad_dn, {'name': username})
        # set to ignore
        ignorelist = f'{ucr["connector/ad/mapping/user/ignorelist"]},{username}'
        ucr_set([f'connector/ad/mapping/user/ignorelist={ignorelist}'])
        restart_adconnector()
        # remove object in UCS and check it didn't get deleted in AD
        udm.remove_object('users/user', dn=udm_dn)
        wait_for_sync()
        AD.verify_object(ad_dn, {'name': username})
        # cleanup
        delete_con_user(AD, ad_dn, udm_dn, wait_for_sync)


# TODO
# def test_only_ucs
# def test_only_ad
