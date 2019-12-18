#!/usr/share/ucs-test/runner /usr/bin/py.test -s
# coding: utf-8
## desc: "Test the UCS<->AD sync in {read,write,sync} mode with users"
## exposure: dangerous
## packages:
## - univention-s4-connector
## bugs:
##  - 43598

from __future__ import print_function

import ldap
import pytest

from univention.testing.udm import UCSTestUDM
from univention.testing.connector_common import (NormalUser, Utf8User,
	SpecialUser, create_udm_user, delete_udm_user, create_con_user,
	delete_con_user)
import univention.testing.connector_common as tcommon

import s4connector
from s4connector import (connector_running_on_this_host, connector_setup)


TEST_USERS = [NormalUser, Utf8User, SpecialUser]


@pytest.mark.parametrize("user_class", TEST_USERS)
@pytest.mark.parametrize("sync_mode", ["write", "sync"])
@pytest.mark.skipif(not connector_running_on_this_host(),
	reason="Univention S4 Connector not configured.")
def test_user_sync_from_udm_to_s4(user_class, sync_mode):
	with connector_setup(sync_mode) as s4, UCSTestUDM() as udm:
		udm_user = user_class()
		(udm_user_dn, s4_user_dn) = create_udm_user(udm, s4, udm_user, s4connector.wait_for_sync)

		print("\nModifying UDM user\n")
		udm.modify_object('users/user', dn=udm_user_dn, **udm_user.user)
		s4connector.wait_for_sync()
		s4.verify_object(s4_user_dn, tcommon.map_udm_user_to_con(udm_user.user))

		delete_udm_user(udm, s4, udm_user_dn, s4_user_dn, s4connector.wait_for_sync)


@pytest.mark.parametrize("user_class", TEST_USERS)
@pytest.mark.parametrize("sync_mode", ["write", "sync"])
@pytest.mark.skipif(not connector_running_on_this_host(),
	reason="Univention S4 Connector not configured.")
def test_user_sync_from_udm_to_s4_with_rename(user_class, sync_mode):
	with connector_setup(sync_mode) as s4, UCSTestUDM() as udm:
		udm_user = user_class()
		(udm_user_dn, s4_user_dn) = create_udm_user(udm, s4, udm_user, s4connector.wait_for_sync)

		print("\nRename UDM user\n")
		udm_user_dn = udm.modify_object('users/user', dn=udm_user_dn, **udm_user.rename)
		s4connector.wait_for_sync()

		s4.verify_object(s4_user_dn, None)
		s4_user_dn = ldap.dn.dn2str([
			[("CN", udm_user.rename.get("username"), ldap.AVA_STRING)],
			[("CN", "users", ldap.AVA_STRING)]] + ldap.dn.str2dn(s4.adldapbase))
		s4.verify_object(s4_user_dn, tcommon.map_udm_user_to_con(udm_user.rename))

		delete_udm_user(udm, s4, udm_user_dn, s4_user_dn, s4connector.wait_for_sync)


@pytest.mark.parametrize("user_class", TEST_USERS)
@pytest.mark.parametrize("sync_mode", ["write", "sync"])
@pytest.mark.skipif(not connector_running_on_this_host(),
	reason="Univention S4 Connector not configured.")
def test_user_sync_from_udm_to_s4_with_move(user_class, sync_mode):
	with connector_setup(sync_mode) as s4, UCSTestUDM() as udm:
		udm_user = user_class()
		(udm_user_dn, s4_user_dn) = create_udm_user(udm, s4, udm_user, s4connector.wait_for_sync)

		print("\nMove UDM user\n")
		udm_container_dn = udm.create_object('container/cn', name=udm_user.container)
		udm_user_dn = udm.move_object('users/user', dn=udm_user_dn,
			position=udm_container_dn)

		s4connector.wait_for_sync()
		s4.verify_object(s4_user_dn, None)
		s4_user_dn = ldap.dn.dn2str([
			[("CN", udm_user.basic.get("username"), ldap.AVA_STRING)],
			[("CN", udm_user.container, ldap.AVA_STRING)]] + ldap.dn.str2dn(s4.adldapbase))
		s4.verify_object(s4_user_dn, tcommon.map_udm_user_to_con(udm_user.basic))

		delete_udm_user(udm, s4, udm_user_dn, s4_user_dn, s4connector.wait_for_sync)


@pytest.mark.parametrize("user_class", TEST_USERS)
@pytest.mark.parametrize("sync_mode", ["read", "sync"])
@pytest.mark.skipif(not connector_running_on_this_host(),
	reason="Univention S4 Connector not configured.")
def test_user_sync_from_s4_to_udm(user_class, sync_mode):
	with connector_setup(sync_mode) as s4:
		udm_user = user_class()
		(basic_s4_user, s4_user_dn, udm_user_dn) = create_con_user(s4, udm_user, s4connector.wait_for_sync)

		print("\nModifying S4 user\n")
		s4.set_attributes(s4_user_dn, **tcommon.map_udm_user_to_con(udm_user.user))
		s4connector.wait_for_sync()
		tcommon.verify_udm_object("users/user", udm_user_dn, udm_user.user)

		delete_con_user(s4, s4_user_dn, udm_user_dn, s4connector.wait_for_sync)


@pytest.mark.parametrize("user_class", TEST_USERS)
@pytest.mark.parametrize("sync_mode", ["read", "sync"])
@pytest.mark.skipif(not connector_running_on_this_host(),
	reason="Univention S4 Connector not configured.")
def test_user_sync_from_s4_to_udm_with_rename(user_class, sync_mode):
	with connector_setup(sync_mode) as s4:
		udm_user = user_class()
		(basic_s4_user, s4_user_dn, udm_user_dn) = create_con_user(s4, udm_user, s4connector.wait_for_sync)

		print("\nRename S4 user {!r} to {!r}\n".format(s4_user_dn, udm_user.rename.get("username")))
		s4_user_dn = s4.rename_or_move_user_or_group(s4_user_dn,
			name=udm_user.rename.get("username"))
		s4.set_attributes(s4_user_dn, **tcommon.map_udm_user_to_con(udm_user.rename))
		s4connector.wait_for_sync()

		tcommon.verify_udm_object("users/user", udm_user_dn, None)
		udm_user_dn = ldap.dn.dn2str([
			[("uid", udm_user.rename.get("username"), ldap.AVA_STRING)],
			[("CN", "users", ldap.AVA_STRING)]] + ldap.dn.str2dn(tcommon.configRegistry['ldap/base']))
		tcommon.verify_udm_object("users/user", udm_user_dn, udm_user.rename)

		delete_con_user(s4, s4_user_dn, udm_user_dn, s4connector.wait_for_sync)


@pytest.mark.parametrize("user_class", TEST_USERS)
@pytest.mark.parametrize("sync_mode", ["read", "sync"])
@pytest.mark.skipif(not connector_running_on_this_host(),
	reason="Univention S4 Connector not configured.")
def test_user_sync_from_s4_to_udm_with_move(user_class, sync_mode):
	with connector_setup(sync_mode) as s4:
		udm_user = user_class()
		(basic_s4_user, s4_user_dn, udm_user_dn) = create_con_user(s4, udm_user, s4connector.wait_for_sync)

		print("\nMove S4 user {!r} to {!r}\n".format(s4_user_dn, udm_user.container))
		container_dn = s4.container_create(udm_user.container)
		s4_user_dn = s4.rename_or_move_user_or_group(s4_user_dn, position=container_dn)
		s4.set_attributes(s4_user_dn, **tcommon.map_udm_user_to_con(udm_user.basic))
		s4connector.wait_for_sync()

		tcommon.verify_udm_object("users/user", udm_user_dn, None)
		udm_user_dn = ldap.dn.dn2str([
			[("uid", udm_user.basic.get("username"), ldap.AVA_STRING)],
			[("CN", udm_user.container, ldap.AVA_STRING)]] + ldap.dn.str2dn(tcommon.configRegistry['ldap/base']))
		tcommon.verify_udm_object("users/user", udm_user_dn, udm_user.basic)

		delete_con_user(s4, s4_user_dn, udm_user_dn, s4connector.wait_for_sync)
