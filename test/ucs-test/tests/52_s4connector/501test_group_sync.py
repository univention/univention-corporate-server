#!/usr/share/ucs-test/runner /usr/bin/py.test -s
# coding: utf-8
## desc: "Test the UCS<->AD sync in {read,write,sync} mode with groups"
## exposure: dangerous
## timeout: 7200
## packages:
## - univention-s4-connector
## bugs:
##  - 43598

from __future__ import print_function

import ldap
import pytest

from univention.testing.udm import UCSTestUDM
from univention.testing.connector_common import (Utf8User, SpecialUser,
	NormalGroup, Utf8Group, SpecialGroup, create_udm_group, delete_udm_group,
	create_con_group, delete_con_group, create_udm_user, delete_udm_user,
	create_con_user, delete_con_user)
import univention.testing.connector_common as tcommon

import s4connector
from s4connector import (connector_running_on_this_host, connector_setup)

TEST_GROUPS = [NormalGroup, Utf8Group, SpecialGroup]
NESTED_USERS = [Utf8User, SpecialUser]
NESTED_GROUPS = [Utf8Group, SpecialGroup]


@pytest.mark.parametrize("group_class", TEST_GROUPS)
@pytest.mark.parametrize("sync_mode", ["write", "sync"])
@pytest.mark.skipif(not connector_running_on_this_host(),
	reason="Univention S4 Connector not configured.")
def test_group_sync_from_udm_to_s4(group_class, sync_mode):
	with connector_setup(sync_mode) as s4, UCSTestUDM() as udm:
		udm_group = group_class()
		(udm_group_dn, s4_group_dn) = create_udm_group(udm, s4, udm_group, s4connector.wait_for_sync)
		delete_udm_group(udm, s4, udm_group_dn, s4_group_dn, s4connector.wait_for_sync)


@pytest.mark.parametrize("group_class", TEST_GROUPS)
@pytest.mark.parametrize("sync_mode", ["write", "sync"])
@pytest.mark.skipif(not connector_running_on_this_host(),
	reason="Univention S4 Connector not configured.")
def test_group_sync_from_udm_to_s4_with_rename(group_class, sync_mode):
	with connector_setup(sync_mode) as s4, UCSTestUDM() as udm:
		udm_group = group_class()
		(udm_group_dn, s4_group_dn) = create_udm_group(udm, s4, udm_group, s4connector.wait_for_sync)

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
		s4connector.wait_for_sync()

		s4.verify_object(s4_group_dn, None)
		s4_group_dn = ldap.dn.dn2str([
			[("CN", udm_group.rename.get("name"), ldap.AVA_STRING)],
			[("CN", "groups", ldap.AVA_STRING)]] + ldap.dn.str2dn(s4.adldapbase))
		s4.verify_object(s4_group_dn, tcommon.map_udm_group_to_con(udm_group.rename))

		delete_udm_group(udm, s4, udm_group_dn, s4_group_dn, s4connector.wait_for_sync)


@pytest.mark.parametrize("group_class", TEST_GROUPS)
@pytest.mark.parametrize("sync_mode", ["write", "sync"])
@pytest.mark.skipif(not connector_running_on_this_host(),
	reason="Univention S4 Connector not configured.")
def test_group_sync_from_udm_to_s4_with_move(group_class, sync_mode):
	with connector_setup(sync_mode) as s4, UCSTestUDM() as udm:
		udm_group = group_class()
		(udm_group_dn, s4_group_dn) = create_udm_group(udm, s4, udm_group, s4connector.wait_for_sync)

		print("\nMove UDM group\n")
		udm_container_dn = udm.create_object('container/cn', name=udm_group.container)
		udm_group_dn = udm.move_object('groups/group', dn=udm_group_dn,
			position=udm_container_dn)

		s4connector.wait_for_sync()
		s4.verify_object(s4_group_dn, None)
		s4_group_dn = ldap.dn.dn2str([
			[("CN", udm_group.group.get("name"), ldap.AVA_STRING)],
			[("CN", udm_group.container, ldap.AVA_STRING)]] + ldap.dn.str2dn(s4.adldapbase))
		s4.verify_object(s4_group_dn, tcommon.map_udm_group_to_con(udm_group.group))

		delete_udm_group(udm, s4, udm_group_dn, s4_group_dn, s4connector.wait_for_sync)


@pytest.mark.parametrize("group_class", TEST_GROUPS)
@pytest.mark.parametrize("sync_mode", ["read", "sync"])
@pytest.mark.skipif(not connector_running_on_this_host(),
	reason="Univention S4 Connector not configured.")
def test_group_sync_from_s4_to_udm(group_class, sync_mode):
	with connector_setup(sync_mode) as s4:
		udm_group = group_class()
		(s4_group, s4_group_dn, udm_group_dn) = create_con_group(s4, udm_group, s4connector.wait_for_sync)
		delete_con_group(s4, s4_group_dn, udm_group_dn, s4connector.wait_for_sync)


@pytest.mark.parametrize("group_class", TEST_GROUPS)
@pytest.mark.parametrize("sync_mode", ["read", "sync"])
@pytest.mark.skipif(not connector_running_on_this_host(),
	reason="Univention S4 Connector not configured.")
def test_group_sync_from_s4_to_udm_with_rename(group_class, sync_mode):
	with connector_setup(sync_mode) as s4:
		udm_group = group_class()
		(s4_group, s4_group_dn, udm_group_dn) = create_con_group(s4, udm_group, s4connector.wait_for_sync)

		print("\nRename S4 group {!r} to {!r}\n".format(s4_group_dn, udm_group.rename.get("name")))
		s4_group_dn = s4.rename_or_move_user_or_group(s4_group_dn,
			name=udm_group.rename.get("name"))
		s4.set_attributes(s4_group_dn, **tcommon.map_udm_group_to_con(udm_group.rename))
		s4connector.wait_for_sync()

		tcommon.verify_udm_object("groups/group", udm_group_dn, None)
		udm_group_dn = ldap.dn.dn2str([
			[("CN", udm_group.rename.get("name"), ldap.AVA_STRING)],
			[("CN", "groups", ldap.AVA_STRING)]] + ldap.dn.str2dn(tcommon.configRegistry['ldap/base']))
		tcommon.verify_udm_object("groups/group", udm_group_dn, udm_group.rename)

		delete_con_group(s4, s4_group_dn, udm_group_dn, s4connector.wait_for_sync)


@pytest.mark.parametrize("group_class", TEST_GROUPS)
@pytest.mark.parametrize("sync_mode", ["read", "sync"])
@pytest.mark.skipif(not connector_running_on_this_host(),
	reason="Univention S4 Connector not configured.")
def test_group_sync_from_s4_to_udm_with_move(group_class, sync_mode):
	with connector_setup(sync_mode) as s4:
		udm_group = group_class()
		(s4_group, s4_group_dn, udm_group_dn) = create_con_group(s4, udm_group, s4connector.wait_for_sync)

		print("\nMove S4 group {!r} to {!r}\n".format(s4_group_dn, udm_group.container))
		container_dn = s4.container_create(udm_group.container)
		s4_group_dn = s4.rename_or_move_user_or_group(s4_group_dn, position=container_dn)
		s4.set_attributes(s4_group_dn, **tcommon.map_udm_group_to_con(udm_group.group))
		s4connector.wait_for_sync()

		tcommon.verify_udm_object("groups/group", udm_group_dn, None)
		udm_group_dn = ldap.dn.dn2str([
			[("CN", udm_group.group.get("name"), ldap.AVA_STRING)],
			[("CN", udm_group.container, ldap.AVA_STRING)]] + ldap.dn.str2dn(tcommon.configRegistry['ldap/base']))
		tcommon.verify_udm_object("groups/group", udm_group_dn, udm_group.group)

		delete_con_group(s4, s4_group_dn, udm_group_dn, s4connector.wait_for_sync)


@pytest.mark.parametrize("group_class", [SpecialGroup])
@pytest.mark.parametrize("nested_class", NESTED_USERS)
@pytest.mark.parametrize("sync_mode", ["write", "sync"])
@pytest.mark.skipif(not connector_running_on_this_host(),
	reason="Univention S4 Connector not configured.")
def test_group_sync_from_udm_to_s4_with_nested_user(group_class, nested_class, sync_mode):
	with connector_setup(sync_mode) as s4, UCSTestUDM() as udm:
		udm_group = group_class()
		nested_user = nested_class()
		(udm_group_dn, s4_group_dn) = create_udm_group(udm, s4, udm_group, s4connector.wait_for_sync)

		print("\nModifying UDM group\n")
		(nested_user_dn, s4_nested_user_dn) = create_udm_user(udm, s4, nested_user, s4connector.wait_for_sync)
		udm.modify_object('groups/group', dn=udm_group_dn, users=[nested_user_dn])
		s4connector.wait_for_sync()
		s4_group = tcommon.map_udm_group_to_con(udm_group.group)
		s4_group.update({"member": [s4_nested_user_dn]})
		s4.verify_object(s4_group_dn, s4_group)
		delete_udm_user(udm, s4, nested_user_dn, s4_nested_user_dn, s4connector.wait_for_sync)

		delete_udm_group(udm, s4, udm_group_dn, s4_group_dn, s4connector.wait_for_sync)


@pytest.mark.parametrize("group_class", [SpecialGroup])
@pytest.mark.parametrize("nested_class", NESTED_USERS)
@pytest.mark.parametrize("sync_mode", ["read", "sync"])
@pytest.mark.skipif(not connector_running_on_this_host(),
	reason="Univention S4 Connector not configured.")
def test_group_sync_from_s4_to_udm_with_nested_user(group_class, nested_class, sync_mode):
	with connector_setup(sync_mode) as s4:
		udm_group = group_class()
		nested_user = nested_class()
		(s4_group, s4_group_dn, udm_group_dn) = create_con_group(s4, udm_group, s4connector.wait_for_sync)

		print("\nModifying S4 group\n")
		(nested_s4_user, nested_s4_user_dn, nested_udm_user_dn) = create_con_user(s4, nested_user, s4connector.wait_for_sync)
		s4.set_attributes(s4_group_dn, member=[nested_s4_user_dn])
		s4connector.wait_for_sync()
		udm_attributes = {"users": [nested_udm_user_dn]}
		udm_attributes.update(udm_group.group)
		tcommon.verify_udm_object("groups/group", udm_group_dn, udm_attributes)
		delete_con_user(s4, nested_s4_user_dn, nested_udm_user_dn, s4connector.wait_for_sync)

		delete_con_group(s4, s4_group_dn, udm_group_dn, s4connector.wait_for_sync)


@pytest.mark.parametrize("group_class", [SpecialGroup])
@pytest.mark.parametrize("nested_class", NESTED_GROUPS)
@pytest.mark.parametrize("sync_mode", ["write", "sync"])
@pytest.mark.skipif(not connector_running_on_this_host(),
	reason="Univention S4 Connector not configured.")
def test_group_sync_from_udm_to_s4_with_nested_group(group_class, nested_class, sync_mode):
	with connector_setup(sync_mode) as s4, UCSTestUDM() as udm:
		udm_group = group_class()
		nested_group = nested_class()
		(udm_group_dn, s4_group_dn) = create_udm_group(udm, s4, udm_group, s4connector.wait_for_sync)

		print("\nModifying UDM group\n")
		(nested_group_dn, s4_nested_group_dn) = create_udm_group(udm, s4, nested_group, s4connector.wait_for_sync)
		udm.modify_object('groups/group', dn=udm_group_dn, nestedGroup=[nested_group_dn])
		s4connector.wait_for_sync()
		s4_group = tcommon.map_udm_group_to_con(udm_group.group)
		s4_group.update({"member": [s4_nested_group_dn]})
		s4.verify_object(s4_group_dn, s4_group)
		delete_udm_group(udm, s4, nested_group_dn, s4_nested_group_dn, s4connector.wait_for_sync)

		delete_udm_group(udm, s4, udm_group_dn, s4_group_dn, s4connector.wait_for_sync)


@pytest.mark.parametrize("group_class", [SpecialGroup])
@pytest.mark.parametrize("nested_class", NESTED_GROUPS)
@pytest.mark.parametrize("sync_mode", ["read", "sync"])
@pytest.mark.skipif(not connector_running_on_this_host(),
	reason="Univention S4 Connector not configured.")
def test_group_sync_from_s4_to_udm_with_nested_group(group_class, nested_class, sync_mode):
	with connector_setup(sync_mode) as s4:
		udm_group = group_class()
		nested_group = nested_class()
		(s4_group, s4_group_dn, udm_group_dn) = create_con_group(s4, udm_group, s4connector.wait_for_sync)

		print("\nModifying S4 group\n")
		(nested_s4_user, nested_s4_user_dn, nested_udm_user_dn) = create_con_group(s4, nested_group, s4connector.wait_for_sync)
		s4.set_attributes(s4_group_dn, member=[nested_s4_user_dn])
		s4connector.wait_for_sync()
		udm_attributes = {"nestedGroup": [nested_udm_user_dn]}
		udm_attributes.update(udm_group.group)
		tcommon.verify_udm_object("groups/group", udm_group_dn, udm_attributes)
		delete_con_group(s4, nested_s4_user_dn, nested_udm_user_dn, s4connector.wait_for_sync)

		delete_con_group(s4, s4_group_dn, udm_group_dn, s4connector.wait_for_sync)
