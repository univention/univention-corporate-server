#!/usr/share/ucs-test/runner /usr/bin/py.test -s
# coding: utf-8
## desc: "Test the UCS<->AD sync in {read,write,sync} mode with groups"
## exposure: dangerous
## packages:
## - univention-ad-connector
## bugs:
##  - 11658
## tags:
##  - skip_admember

from __future__ import print_function

import ldap
import pytest

import adconnector
from adconnector import (connector_running_on_this_host, connector_setup)

# This is something weird. The `adconnector.ADConnection()` MUST be
# instantiated, before `UCSTestUDM` is imported.
AD = adconnector.ADConnection()
from univention.testing.udm import UCSTestUDM

from univention.testing.connector_common import (Utf8User, SpecialUser,
	NormalGroup, Utf8Group, SpecialGroup, create_udm_group, delete_udm_group,
	create_con_group, delete_con_group, create_udm_user, delete_udm_user,
	create_con_user, delete_con_user)
import univention.testing.connector_common as tcommon


TEST_GROUPS = [NormalGroup, Utf8Group, SpecialGroup]
NESTED_USERS = [Utf8User, SpecialUser]
NESTED_GROUPS = [Utf8Group, SpecialGroup]


@pytest.mark.parametrize("group_class", TEST_GROUPS)
@pytest.mark.parametrize("sync_mode", ["write", "sync"])
@pytest.mark.skipif(not connector_running_on_this_host(),
	reason="Univention AD Connector not configured.")
def test_group_sync_from_udm_to_ad(group_class, sync_mode):
	with connector_setup(sync_mode), UCSTestUDM() as udm:
		udm_group = group_class()
		(udm_group_dn, ad_group_dn) = create_udm_group(udm, AD, udm_group, adconnector.wait_for_sync)
		delete_udm_group(udm, AD, udm_group_dn, ad_group_dn, adconnector.wait_for_sync)


@pytest.mark.parametrize("group_class", TEST_GROUPS)
@pytest.mark.parametrize("sync_mode", ["write", "sync"])
@pytest.mark.skipif(not connector_running_on_this_host(),
	reason="Univention AD Connector not configured.")
def test_group_sync_from_udm_to_ad_with_rename(group_class, sync_mode):
	with connector_setup(sync_mode), UCSTestUDM() as udm:
		udm_group = group_class()
		(udm_group_dn, ad_group_dn) = create_udm_group(udm, AD, udm_group, adconnector.wait_for_sync)

		print("\nRename UDM group\n")
		old_udm_dn = udm_group_dn  # part of the workaround for bug #41694
		udm_group_dn = udm.modify_object('groups/group', dn=udm_group_dn, **udm_group.rename)
		# XXX after a modify, the old DN is _wrongly_ returned: see bug #41694
		if old_udm_dn == udm_group_dn:
			udm_group_dn = ldap.dn.dn2str([[("CN", udm_group.rename.get("name"), ldap.AVA_STRING)]] +
				ldap.dn.str2dn(udm_group_dn)[1:])
			if old_udm_dn in udm._cleanup.get('groups/group', []):
				udm._cleanup.setdefault('groups/group', []).append(udm_group_dn)
				udm._cleanup['groups/group'].remove(old_udm_dn)
		# XXX end of workaround for bug #41694
		adconnector.wait_for_sync()

		AD.verify_object(ad_group_dn, None)
		ad_group_dn = ldap.dn.dn2str([
			[("CN", udm_group.rename.get("name"), ldap.AVA_STRING)],
			[("CN", "groups", ldap.AVA_STRING)]] + ldap.dn.str2dn(AD.adldapbase))
		AD.verify_object(ad_group_dn, tcommon.map_udm_group_to_con(udm_group.rename))

		delete_udm_group(udm, AD, udm_group_dn, ad_group_dn, adconnector.wait_for_sync)


@pytest.mark.parametrize("group_class", TEST_GROUPS)
@pytest.mark.parametrize("sync_mode", ["write", "sync"])
@pytest.mark.skipif(not connector_running_on_this_host(),
	reason="Univention AD Connector not configured.")
def test_group_sync_from_udm_to_ad_with_move(group_class, sync_mode):
	with connector_setup(sync_mode), UCSTestUDM() as udm:
		udm_group = group_class()
		(udm_group_dn, ad_group_dn) = create_udm_group(udm, AD, udm_group, adconnector.wait_for_sync)

		print("\nMove UDM group\n")
		udm_container_dn = udm.create_object('container/cn', name=udm_group.container)
		udm_group_dn = udm.move_object('groups/group', dn=udm_group_dn,
			position=udm_container_dn)

		adconnector.wait_for_sync()
		AD.verify_object(ad_group_dn, None)
		ad_group_dn = ldap.dn.dn2str([
			[("CN", udm_group.group.get("name"), ldap.AVA_STRING)],
			[("CN", udm_group.container, ldap.AVA_STRING)]] + ldap.dn.str2dn(AD.adldapbase))
		AD.verify_object(ad_group_dn, tcommon.map_udm_group_to_con(udm_group.group))

		delete_udm_group(udm, AD, udm_group_dn, ad_group_dn, adconnector.wait_for_sync)


@pytest.mark.parametrize("group_class", TEST_GROUPS)
@pytest.mark.parametrize("sync_mode", ["read", "sync"])
@pytest.mark.skipif(not connector_running_on_this_host(),
	reason="Univention AD Connector not configured.")
def test_group_sync_from_ad_to_udm(group_class, sync_mode):
	with connector_setup(sync_mode):
		udm_group = group_class()
		(ad_group, ad_group_dn, udm_group_dn) = create_con_group(AD, udm_group, adconnector.wait_for_sync)
		delete_con_group(AD, ad_group_dn, udm_group_dn, adconnector.wait_for_sync)


@pytest.mark.parametrize("group_class", TEST_GROUPS)
@pytest.mark.parametrize("sync_mode", ["read", "sync"])
@pytest.mark.skipif(not connector_running_on_this_host(),
	reason="Univention AD Connector not configured.")
def test_group_sync_from_ad_to_udm_with_rename(group_class, sync_mode):
	with connector_setup(sync_mode):
		udm_group = group_class()
		(ad_group, ad_group_dn, udm_group_dn) = create_con_group(AD, udm_group, adconnector.wait_for_sync)

		print("\nRename AD group {!r} to {!r}\n".format(ad_group_dn, udm_group.rename.get("name")))
		ad_group_dn = AD.rename_or_move_user_or_group(ad_group_dn,
			name=udm_group.rename.get("name"))
		AD.set_attributes(ad_group_dn, **tcommon.map_udm_group_to_con(udm_group.rename))
		adconnector.wait_for_sync()

		tcommon.verify_udm_object("groups/group", udm_group_dn, None)
		udm_group_dn = ldap.dn.dn2str([
			[("CN", udm_group.rename.get("name"), ldap.AVA_STRING)],
			[("CN", "groups", ldap.AVA_STRING)]] + ldap.dn.str2dn(tcommon.configRegistry['ldap/base']))
		tcommon.verify_udm_object("groups/group", udm_group_dn, udm_group.rename)

		delete_con_group(AD, ad_group_dn, udm_group_dn, adconnector.wait_for_sync)


@pytest.mark.parametrize("group_class", TEST_GROUPS)
@pytest.mark.parametrize("sync_mode", ["read", "sync"])
@pytest.mark.skipif(not connector_running_on_this_host(),
	reason="Univention AD Connector not configured.")
def test_group_sync_from_ad_to_udm_with_move(group_class, sync_mode):
	with connector_setup(sync_mode):
		udm_group = group_class()
		(ad_group, ad_group_dn, udm_group_dn) = create_con_group(AD, udm_group, adconnector.wait_for_sync)

		print("\nMove AD group {!r} to {!r}\n".format(ad_group_dn, udm_group.container))
		container_dn = AD.container_create(udm_group.container)
		ad_group_dn = AD.rename_or_move_user_or_group(ad_group_dn, position=container_dn)
		AD.set_attributes(ad_group_dn, **tcommon.map_udm_group_to_con(udm_group.group))
		adconnector.wait_for_sync()

		tcommon.verify_udm_object("groups/group", udm_group_dn, None)
		udm_group_dn = ldap.dn.dn2str([
			[("CN", udm_group.group.get("name"), ldap.AVA_STRING)],
			[("CN", udm_group.container, ldap.AVA_STRING)]] + ldap.dn.str2dn(tcommon.configRegistry['ldap/base']))
		tcommon.verify_udm_object("groups/group", udm_group_dn, udm_group.group)

		delete_con_group(AD, ad_group_dn, udm_group_dn, adconnector.wait_for_sync)


@pytest.mark.parametrize("group_class", [SpecialGroup])
@pytest.mark.parametrize("nested_class", NESTED_USERS)
@pytest.mark.parametrize("sync_mode", ["write", "sync"])
@pytest.mark.skipif(not connector_running_on_this_host(),
	reason="Univention AD Connector not configured.")
def test_group_sync_from_udm_to_ad_with_nested_user(group_class, nested_class, sync_mode):
	with connector_setup(sync_mode), UCSTestUDM() as udm:
		udm_group = group_class()
		nested_user = nested_class()
		(udm_group_dn, ad_group_dn) = create_udm_group(udm, AD, udm_group, adconnector.wait_for_sync)

		print("\nModifying UDM group\n")
		(nested_user_dn, ad_nested_user_dn) = create_udm_user(udm, AD, nested_user, adconnector.wait_for_sync)
		udm.modify_object('groups/group', dn=udm_group_dn, users=[nested_user_dn])
		adconnector.wait_for_sync()
		ad_group = tcommon.map_udm_group_to_con(udm_group.group)
		ad_group.update({"member": [ad_nested_user_dn]})
		AD.verify_object(ad_group_dn, ad_group)
		delete_udm_user(udm, AD, nested_user_dn, ad_nested_user_dn, adconnector.wait_for_sync)

		delete_udm_group(udm, AD, udm_group_dn, ad_group_dn, adconnector.wait_for_sync)


@pytest.mark.parametrize("group_class", [SpecialGroup])
@pytest.mark.parametrize("nested_class", NESTED_USERS)
@pytest.mark.parametrize("sync_mode", ["read", "sync"])
@pytest.mark.skipif(not connector_running_on_this_host(),
	reason="Univention AD Connector not configured.")
def test_group_sync_from_ad_to_udm_with_nested_user(group_class, nested_class, sync_mode):
	with connector_setup(sync_mode):
		udm_group = group_class()
		nested_user = nested_class()
		(ad_group, ad_group_dn, udm_group_dn) = create_con_group(AD, udm_group, adconnector.wait_for_sync)

		print("\nModifying AD group\n")
		(nested_ad_user, nested_ad_user_dn, nested_udm_user_dn) = create_con_user(AD, nested_user, adconnector.wait_for_sync)
		AD.set_attributes(ad_group_dn, member=[nested_ad_user_dn])
		adconnector.wait_for_sync()
		udm_attributes = {"users": [nested_udm_user_dn]}
		udm_attributes.update(udm_group.group)
		tcommon.verify_udm_object("groups/group", udm_group_dn, udm_attributes)
		delete_con_user(AD, nested_ad_user_dn, nested_udm_user_dn, adconnector.wait_for_sync)

		delete_con_group(AD, ad_group_dn, udm_group_dn, adconnector.wait_for_sync)


@pytest.mark.parametrize("group_class", [SpecialGroup])
@pytest.mark.parametrize("nested_class", NESTED_GROUPS)
@pytest.mark.parametrize("sync_mode", ["write", "sync"])
@pytest.mark.skipif(not connector_running_on_this_host(),
	reason="Univention AD Connector not configured.")
def test_group_sync_from_udm_to_ad_with_nested_group(group_class, nested_class, sync_mode):
	with connector_setup(sync_mode), UCSTestUDM() as udm:
		udm_group = group_class()
		nested_group = nested_class()
		(udm_group_dn, ad_group_dn) = create_udm_group(udm, AD, udm_group, adconnector.wait_for_sync)

		print("\nModifying UDM group\n")
		(nested_group_dn, ad_nested_group_dn) = create_udm_group(udm, AD, nested_group, adconnector.wait_for_sync)
		udm.modify_object('groups/group', dn=udm_group_dn, nestedGroup=[nested_group_dn])
		adconnector.wait_for_sync()
		ad_group = tcommon.map_udm_group_to_con(udm_group.group)
		ad_group.update({"member": [ad_nested_group_dn]})
		AD.verify_object(ad_group_dn, ad_group)
		delete_udm_group(udm, AD, nested_group_dn, ad_nested_group_dn, adconnector.wait_for_sync)

		delete_udm_group(udm, AD, udm_group_dn, ad_group_dn, adconnector.wait_for_sync)


@pytest.mark.parametrize("group_class", [SpecialGroup])
@pytest.mark.parametrize("nested_class", NESTED_GROUPS)
@pytest.mark.parametrize("sync_mode", ["read", "sync"])
@pytest.mark.skipif(not connector_running_on_this_host(),
	reason="Univention AD Connector not configured.")
def test_group_sync_from_ad_to_udm_with_nested_group(group_class, nested_class, sync_mode):
	with connector_setup(sync_mode):
		udm_group = group_class()
		nested_group = nested_class()
		(ad_group, ad_group_dn, udm_group_dn) = create_con_group(AD, udm_group, adconnector.wait_for_sync)

		print("\nModifying AD group\n")
		(nested_ad_user, nested_ad_user_dn, nested_udm_user_dn) = create_con_group(AD, nested_group, adconnector.wait_for_sync)
		AD.set_attributes(ad_group_dn, member=[nested_ad_user_dn])
		adconnector.wait_for_sync()
		udm_attributes = {"nestedGroup": [nested_udm_user_dn]}
		udm_attributes.update(udm_group.group)
		tcommon.verify_udm_object("groups/group", udm_group_dn, udm_attributes)
		delete_con_group(AD, nested_ad_user_dn, nested_udm_user_dn, adconnector.wait_for_sync)

		delete_con_group(AD, ad_group_dn, udm_group_dn, adconnector.wait_for_sync)
