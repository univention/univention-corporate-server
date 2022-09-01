#!/usr/share/ucs-test/runner pytest-3 -s
# coding: utf-8
## desc: "Test the UCS<->AD sync with ignorefilter in {read,write,sync} mode with users"
## exposure: dangerous
## packages:
## - univention-ad-connector
## bugs:
##  - 55150

import pytest

import adconnector
from adconnector import connector_running_on_this_host, connector_setup

# This is something weird. The `adconnector.ADConnection()` MUST be
# instantiated, before `UCSTestUDM` is imported.
AD = adconnector.ADConnection()

import univention.testing.connector_common as tcommon  # noqa: E402
from univention.testing.connector_common import delete_con_user  # noqa: E402
from univention.testing.connector_common import (  # noqa: E402
	NormalUser, SpecialUser, Utf8User, create_con_user, create_udm_user, delete_udm_user,
)
from univention.config_registry import handler_set as ucr_set  # noqa: E402
import univention.testing.ucr as testing_ucr  # noqa: E402


TEST_USERS = [NormalUser, Utf8User, SpecialUser]


@pytest.mark.parametrize("user_class", TEST_USERS)
@pytest.mark.parametrize("sync_mode", ["read", "sync"])
@pytest.mark.skipif(not connector_running_on_this_host(), reason="Univention AD Connector not configured.")
def test_user_sync_from_ad_to_udm_with_ignorefilter(user_class, sync_mode):
	with connector_setup(sync_mode):
		try:
			udm_user = user_class()
			(basic_ad_user, ad_user_dn, udm_user_dn) = create_con_user(AD, udm_user, adconnector.wait_for_sync)
			with testing_ucr.UCSTestConfigRegistry():
				ignorefilter = "(givenName={})".format(udm_user.user["firstname"].decode("utf-8"))
				ucr_set(["connector/ad/mapping/user/ignorefilter={}".format(ignorefilter)])
				adconnector.restart_adconnector()
				udm_user.user["firstname"] = udm_user.user["firstname"] + udm_user.user["lastname"]
				print("\nModifying AD user\n")
				AD.set_attributes(ad_user_dn, **tcommon.map_udm_user_to_con(udm_user.user))
				adconnector.wait_for_sync()
				tcommon.verify_udm_object("users/user", udm_user_dn, udm_user.user)
		finally:
			adconnector.restart_adconnector()
			delete_con_user(AD, ad_user_dn, udm_user_dn, adconnector.wait_for_sync)