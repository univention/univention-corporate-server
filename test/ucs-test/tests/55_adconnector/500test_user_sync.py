#!/usr/share/ucs-test/runner /usr/bin/py.test -s
# coding: utf-8
## desc: "Test the UCS<->AD sync in {read,write,sync} mode with users"
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

from univention.testing.connector_common import (NormalUser, Utf8User,
	SpecialUser, create_udm_user, delete_udm_user, create_con_user,
	delete_con_user)
import univention.testing.connector_common as tcommon


TEST_USERS = [NormalUser, Utf8User, SpecialUser]


@pytest.mark.parametrize("user_class", TEST_USERS)
@pytest.mark.parametrize("sync_mode", ["write", "sync"])
@pytest.mark.skipif(not connector_running_on_this_host(),
	reason="Univention AD Connector not configured.")
def test_user_sync_from_udm_to_ad(user_class, sync_mode):
	with connector_setup(sync_mode), UCSTestUDM() as udm:
		udm_user = user_class()
		(udm_user_dn, ad_user_dn) = create_udm_user(udm, AD, udm_user, adconnector.wait_for_sync)

		print("\nModifying UDM user\n")
		udm.modify_object('users/user', dn=udm_user_dn, **udm_user.user)
		adconnector.wait_for_sync()
		AD.verify_object(ad_user_dn, tcommon.map_udm_user_to_con(udm_user.user))

		delete_udm_user(udm, AD, udm_user_dn, ad_user_dn, adconnector.wait_for_sync)


@pytest.mark.parametrize("user_class", TEST_USERS)
@pytest.mark.parametrize("sync_mode", ["write", "sync"])
@pytest.mark.skipif(not connector_running_on_this_host(),
	reason="Univention AD Connector not configured.")
def test_user_sync_from_udm_to_ad_with_rename(user_class, sync_mode):
	with connector_setup(sync_mode), UCSTestUDM() as udm:
		udm_user = user_class()
		(udm_user_dn, ad_user_dn) = create_udm_user(udm, AD, udm_user, adconnector.wait_for_sync)

		print("\nRename UDM user\n")
		udm_user_dn = udm.modify_object('users/user', dn=udm_user_dn, **udm_user.rename)
		adconnector.wait_for_sync()

		AD.verify_object(ad_user_dn, None)
		ad_user_dn = ldap.dn.dn2str([
			[("CN", udm_user.rename.get("username"), ldap.AVA_STRING)],
			[("CN", "users", ldap.AVA_STRING)]] + ldap.dn.str2dn(AD.adldapbase))
		AD.verify_object(ad_user_dn, tcommon.map_udm_user_to_con(udm_user.rename))

		delete_udm_user(udm, AD, udm_user_dn, ad_user_dn, adconnector.wait_for_sync)


@pytest.mark.parametrize("user_class", TEST_USERS)
@pytest.mark.parametrize("sync_mode", ["write", "sync"])
@pytest.mark.skipif(not connector_running_on_this_host(),
	reason="Univention AD Connector not configured.")
def test_user_sync_from_udm_to_ad_with_move(user_class, sync_mode):
	with connector_setup(sync_mode), UCSTestUDM() as udm:
		udm_user = user_class()
		(udm_user_dn, ad_user_dn) = create_udm_user(udm, AD, udm_user, adconnector.wait_for_sync)

		print("\nMove UDM user\n")
		udm_container_dn = udm.create_object('container/cn', name=udm_user.container)
		udm_user_dn = udm.move_object('users/user', dn=udm_user_dn,
			position=udm_container_dn)

		adconnector.wait_for_sync()
		AD.verify_object(ad_user_dn, None)
		ad_user_dn = ldap.dn.dn2str([
			[("CN", udm_user.basic.get("username"), ldap.AVA_STRING)],
			[("CN", udm_user.container, ldap.AVA_STRING)]] + ldap.dn.str2dn(AD.adldapbase))
		AD.verify_object(ad_user_dn, tcommon.map_udm_user_to_con(udm_user.basic))

		delete_udm_user(udm, AD, udm_user_dn, ad_user_dn, adconnector.wait_for_sync)


@pytest.mark.parametrize("user_class", TEST_USERS)
@pytest.mark.parametrize("sync_mode", ["read", "sync"])
@pytest.mark.skipif(not connector_running_on_this_host(),
	reason="Univention AD Connector not configured.")
def test_user_sync_from_ad_to_udm(user_class, sync_mode):
	with connector_setup(sync_mode):
		udm_user = user_class()
		(basic_ad_user, ad_user_dn, udm_user_dn) = create_con_user(AD, udm_user, adconnector.wait_for_sync)

		print("\nModifying AD user\n")
		AD.set_attributes(ad_user_dn, **tcommon.map_udm_user_to_con(udm_user.user))
		adconnector.wait_for_sync()
		tcommon.verify_udm_object("users/user", udm_user_dn, udm_user.user)

		delete_con_user(AD, ad_user_dn, udm_user_dn, adconnector.wait_for_sync)


@pytest.mark.parametrize("user_class", TEST_USERS)
@pytest.mark.parametrize("sync_mode", ["read", "sync"])
@pytest.mark.skipif(not connector_running_on_this_host(),
	reason="Univention AD Connector not configured.")
def test_user_sync_from_ad_to_udm_with_rename(user_class, sync_mode):
	with connector_setup(sync_mode):
		udm_user = user_class()
		(basic_ad_user, ad_user_dn, udm_user_dn) = create_con_user(AD, udm_user, adconnector.wait_for_sync)

		print("\nRename AD user {!r} to {!r}\n".format(ad_user_dn, udm_user.rename.get("username")))
		ad_user_dn = AD.rename_or_move_user_or_group(ad_user_dn,
			name=udm_user.rename.get("username"))
		AD.set_attributes(ad_user_dn, **tcommon.map_udm_user_to_con(udm_user.rename))
		adconnector.wait_for_sync()

		tcommon.verify_udm_object("users/user", udm_user_dn, None)
		udm_user_dn = ldap.dn.dn2str([
			[("uid", udm_user.rename.get("username"), ldap.AVA_STRING)],
			[("CN", "users", ldap.AVA_STRING)]] + ldap.dn.str2dn(tcommon.configRegistry['ldap/base']))
		tcommon.verify_udm_object("users/user", udm_user_dn, udm_user.rename)

		delete_con_user(AD, ad_user_dn, udm_user_dn, adconnector.wait_for_sync)


@pytest.mark.parametrize("user_class", TEST_USERS)
@pytest.mark.parametrize("sync_mode", ["read", "sync"])
@pytest.mark.skipif(not connector_running_on_this_host(),
	reason="Univention AD Connector not configured.")
def test_user_sync_from_ad_to_udm_with_move(user_class, sync_mode):
	with connector_setup(sync_mode):
		udm_user = user_class()
		(basic_ad_user, ad_user_dn, udm_user_dn) = create_con_user(AD, udm_user, adconnector.wait_for_sync)

		print("\nMove AD user {!r} to {!r}\n".format(ad_user_dn, udm_user.container))
		container_dn = AD.container_create(udm_user.container)
		ad_user_dn = AD.rename_or_move_user_or_group(ad_user_dn, position=container_dn)
		AD.set_attributes(ad_user_dn, **tcommon.map_udm_user_to_con(udm_user.basic))
		adconnector.wait_for_sync()

		tcommon.verify_udm_object("users/user", udm_user_dn, None)
		udm_user_dn = ldap.dn.dn2str([
			[("uid", udm_user.basic.get("username"), ldap.AVA_STRING)],
			[("CN", udm_user.container, ldap.AVA_STRING)]] + ldap.dn.str2dn(tcommon.configRegistry['ldap/base']))
		tcommon.verify_udm_object("users/user", udm_user_dn, udm_user.basic)

		delete_con_user(AD, ad_user_dn, udm_user_dn, adconnector.wait_for_sync)
