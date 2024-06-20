#!/usr/share/ucs-test/runner pytest-3 -s
## desc: "Test the UCS<->AD sync with allow_subtree in {read,write,sync} mode with users"
## exposure: dangerous
## packages:
## - univention-ad-connector

import contextlib
from dataclasses import dataclass
from typing import Generator, List, Optional, Tuple

import pytest

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
class SubTree:
    name: str
    udm_position: Optional[str] = None
    ad_position: Optional[str] = None
    udm_dn: Optional[str] = None
    ad_dn: Optional[str] = None
    objects: Optional[List] = None


@dataclass
class DomObject:
    name: str
    ad_dn: str
    udm_dn: str
    udm_module: str


@contextlib.contextmanager
def allow_subtree_setup(sync_mode: str, create_objects: bool = False) -> Generator[Tuple[List, List, UCSTestUDM], None, None]:
    try:
        with testing_ucr.UCSTestConfigRegistry() as ucr, UCSTestUDM() as udm:
            # allow ou=ou1-allowed,base
            # allow cn=cn2-allowed,cn=users
            # deny  cn=users,base
            # deny  cn=cn3-denied,base
            allowed1 = SubTree(name='ou1-allowed')
            allowed1.udm_position = ucr['ldap/base']
            allowed1.ad_position = ucr['connector/ad/ldap/base']
            allowed1.udm_dn = f'ou={allowed1.name},{allowed1.udm_position}'
            allowed1.ad_dn = f'ou={allowed1.name},{allowed1.ad_position}'
            allowed2 = SubTree(name='cn2-allowed')
            allowed2.udm_position = f'cn=users,{ucr["ldap/base"]}'
            allowed2.ad_position = f'cn=users,{ucr["connector/ad/ldap/base"]}'
            allowed2.udm_dn = f'cn={allowed2.name},{allowed2.udm_position}'
            allowed2.ad_dn = f'cn={allowed2.name},{allowed2.ad_position}'
            not_allowed1 = SubTree(name='users')
            not_allowed1.udm_position = ucr['ldap/base']
            not_allowed1.ad_position = ucr['connector/ad/ldap/base']
            not_allowed1.udm_dn = f'cn={not_allowed1.name},{not_allowed1.udm_position}'
            not_allowed1.ad_dn = f'cn={not_allowed1.name},{not_allowed1.ad_position}'
            not_allowed2 = SubTree(name='cn3-denied')
            not_allowed2.udm_position = ucr['ldap/base']
            not_allowed2.ad_position = ucr['connector/ad/ldap/base']
            not_allowed2.udm_dn = f'cn={not_allowed2.name},{not_allowed2.udm_position}'
            not_allowed2.ad_dn = f'cn={not_allowed2.name},{not_allowed2.ad_position}'
            # create container and optionally some objects in the containers
            udm.create_object('container/ou', name=allowed1.name)
            udm.create_object('container/cn', name=allowed2.name, position=allowed2.udm_position)
            udm.create_object('container/cn', name=not_allowed2.name, position=not_allowed2.udm_position)
            if create_objects:
                not_allowed1.objects = create_objects_in_ucs(udm, not_allowed1, wait=False)
                not_allowed2.objects = create_objects_in_ucs(udm, not_allowed2, wait=False)
                allowed1.objects = create_objects_in_ucs(udm, allowed1, wait=False)
                allowed2.objects = create_objects_in_ucs(udm, allowed2, wait=False)
            wait_for_sync()
            AD.verify_object(allowed1.ad_dn, {'name': allowed1.name})
            AD.verify_object(allowed2.ad_dn, {'name': allowed2.name})
            AD.verify_object(not_allowed2.ad_dn, {'name': not_allowed2.name})
            # configure connector
            ucr_set(
                [
                    f"connector/ad/allow-subtree/test1/ucs={allowed1.udm_dn}",
                    f"connector/ad/allow-subtree/test1/ad={allowed1.ad_dn}",
                    f"connector/ad/allow-subtree/test2/ucs={allowed2.udm_dn}",
                    f"connector/ad/allow-subtree/test2/ad={allowed2.ad_dn}",
                ]
            )
            restart_adconnector()
            yield ([allowed1, allowed2], [not_allowed1, not_allowed2], udm)
    finally:
        restart_adconnector()


def create_objects_in_ucs(udm: UCSTestUDM, tree: SubTree, wait: bool = False) -> List[DomObject]:
    objects = []
    udm_dn, username = udm.create_user(position=tree.udm_dn)
    ad_dn = f'cn={username},{tree.ad_dn}'
    objects.append(DomObject(name=username, ad_dn=ad_dn, udm_dn=udm_dn, udm_module='users/user'))
    # TODO group
    if wait:
        wait_for_sync()
    return objects


def create_objects_in_ad(ad: ADConnection, tree: SubTree, wait: bool = False) -> List[DomObject]:
    objects = []
    username = random_string()
    ad_dn = ad.createuser(username, position=tree.ad_dn)
    udm_dn = f'uid={username},{tree.udm_dn}'
    objects.append(DomObject(name=username, ad_dn=ad_dn, udm_dn=udm_dn, udm_module='users/user'))
    # TODO group
    if wait:
        wait_for_sync()
    return objects


# @pytest.mark.parametrize("sync_mode", ["read", "sync"])
@pytest.mark.parametrize("sync_mode", ["sync"])
@pytest.mark.skipif(not connector_running_on_this_host(), reason="Univention AD Connector not configured.")
def test_create(sync_mode: str) -> None:
    with allow_subtree_setup(sync_mode) as (allowed, denied, udm):
        # check denied for other subtrees
        for tree in denied:
            if sync_mode in ['sync', 'write']:
                # check objects creates in UCS are not synced to AD
                for obj in create_objects_in_ucs(udm, tree):
                    with pytest.raises(AssertionError):
                        AD.verify_object(obj.ad_dn, {'name': obj.name})
                    udm.verify_ldap_object(obj.udm_dn)
                # check objects creates in AD are not synced to UCS
                for obj in create_objects_in_ad(AD, tree):
                    AD.verify_object(obj.ad_dn, {'name': obj.name})
                    with pytest.raises(LDAPObjectNotFound):
                        udm.verify_ldap_object(obj.udm_dn, retry_count=3, delay=1)
        # check sync works
        for tree in allowed:
            if sync_mode in ['sync', 'write']:
                for obj in create_objects_in_ucs(udm, tree):
                    AD.verify_object(obj.ad_dn, {'name': obj.name})
                    udm.verify_ldap_object(obj.udm_dn)
            if sync_mode in ['sync', 'read']:
                for obj in create_objects_in_ad(AD, tree):
                    AD.verify_object(obj.ad_dn, {'name': obj.name})
                    udm.verify_ldap_object(obj.udm_dn)


# @pytest.mark.parametrize("sync_mode", ["read", "sync"])
@pytest.mark.parametrize("sync_mode", ["sync"])
@pytest.mark.skipif(not connector_running_on_this_host(), reason="Univention AD Connector not configured.")
def test_modify(sync_mode: str) -> None:
    with allow_subtree_setup(sync_mode, create_objects=True) as (allowed, denied, udm):
        for tree in denied:
            if sync_mode in ['sync', 'write']:
                for obj in tree.objects:
                    # modify in UCS, check no change in AD
                    udm.modify_object(obj.udm_module, dn=obj.udm_dn, description='changed in UCS')
                    udm.verify_ldap_object(obj.udm_dn, expected_attr={'description': ['changed in UCS']})
                    wait_for_sync()
                    with pytest.raises(AssertionError):
                        AD.verify_object(obj.ad_dn, {'description': 'changed in UCS'})
            if sync_mode in ['sync', 'read']:
                for obj in tree.objects:
                    # modify in AD, check no change in UCS
                    AD.set_attribute(obj.ad_dn, 'description', 'changed in AD'.encode('UTF-8'))
                    AD.verify_object(obj.ad_dn, {'description': 'changed in AD'})
                    wait_for_sync()
                    with pytest.raises(LDAPObjectValueMissing):
                        udm.verify_ldap_object(obj.udm_dn, expected_attr={'description': ['changed in AD']}, retry_count=3, delay=1)
        # check sync works
        for tree in allowed:
            if sync_mode in ['sync', 'write']:
                for obj in tree.objects:
                    # modify in UCS, check change in AD
                    # TODO
                    print(obj)
            if sync_mode in ['sync', 'read']:
                for obj in tree.objects:
                    # modify in AD, check cange in UCS
                    # TODO
                    print(obj)


# TODO
# def test_remove
# def test_move
