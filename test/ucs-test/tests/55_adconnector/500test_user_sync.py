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

import ldap
import pytest

import univention.testing.strings as tstrings
import univention.testing.ucr as testing_ucr
from univention.config_registry import handler_set as ucr_set

import adconnector
from adconnector import ad_in_sync_mode
from adconnector import restart_univention_cli_server
from adconnector import connector_running_on_this_host

# This is something weird. The `adconnector.ADConnection()` MUST be
# instantiated, before `UCSTestUDM` is imported.
AD = adconnector.ADConnection()
from univention.testing.udm import UCSTestUDM

UTF8_CHARSET = tstrings.STR_UMLAUT + u"КирилицаКириллицаĆirilicaЋирилица" + u"普通話普通话"
SPECIAL_CHARSET = tstrings.STR_SPECIAL_CHARACTER
# we exclude '$' as it has special meaning and '#' as the ADC sync can't handle
# them (see bug #44373). A '.' (dot) may not be the last character in a
# samAccountName, so we forbid it aswell.
FORBIDDEN_SAMACCOUNTNAME = '"\\/[]:;|=,+*?<> @.' + '$' + '#'
SPECIAL_CHARSET_USERNAME = "".join(set(SPECIAL_CHARSET) - set(FORBIDDEN_SAMACCOUNTNAME))


def random_string(length=10, alpha=False, numeric=False, charset=None, encoding='utf-8'):
	return tstrings.random_string(length, alpha, numeric, charset, encoding)


NORMAL_SIMPLE_USER = {
	"username": tstrings.random_username(),
	"firstname": tstrings.random_name(),
	"lastname": tstrings.random_name(),
	"description": random_string(alpha=True, numeric=True)}

NORMAL_COMPLEX_USER = {
	"username": tstrings.random_username(),
	"firstname": tstrings.random_name(),
	"lastname": tstrings.random_name(),
	"description": random_string(alpha=True, numeric=True),
	"street": random_string(alpha=True, numeric=True),
	"city": random_string(alpha=True, numeric=True),
	"postcode": random_string(numeric=True),
	"profilepath": random_string(alpha=True, numeric=True),
	"scriptpath": random_string(alpha=True, numeric=True),
	"homeTelephoneNumber": random_string(numeric=True),
	"mobileTelephoneNumber": random_string(numeric=True),
	"pagerTelephoneNumber": random_string(numeric=True),
	"sambaUserWorkstations": random_string(numeric=True)}

UTF8_SIMPLE_USER = {
	"username": random_string(charset=UTF8_CHARSET),
	"firstname": random_string(charset=UTF8_CHARSET),
	"lastname": random_string(charset=UTF8_CHARSET),
	"description": random_string(charset=UTF8_CHARSET)}

UTF8_COMPLEX_USER = {
	"username": random_string(charset=UTF8_CHARSET),
	"firstname": random_string(charset=UTF8_CHARSET),
	"lastname": random_string(charset=UTF8_CHARSET),
	"description": random_string(charset=UTF8_CHARSET),
	"street": random_string(charset=UTF8_CHARSET),
	"city": random_string(charset=UTF8_CHARSET),
	"postcode": random_string(numeric=True),
	"profilepath": random_string(charset=UTF8_CHARSET),
	"scriptpath": random_string(charset=UTF8_CHARSET),
	"homeTelephoneNumber": random_string(numeric=True),
	"mobileTelephoneNumber": random_string(numeric=True),
	"pagerTelephoneNumber": random_string(numeric=True),
	"sambaUserWorkstations": random_string(numeric=True)}

SPECIAL_SIMPLE_USER = {
	"username": random_string(charset=SPECIAL_CHARSET_USERNAME),
	"firstname": tstrings.random_name_special_characters(),
	"lastname": tstrings.random_name_special_characters(),
	"description": random_string(charset=SPECIAL_CHARSET)}

SPECIAL_COMPLEX_USER = {
	"username": random_string(charset=SPECIAL_CHARSET_USERNAME),
	"firstname": tstrings.random_name_special_characters(),
	"lastname": tstrings.random_name_special_characters(),
	"description": random_string(charset=SPECIAL_CHARSET),
	"street": random_string(charset=SPECIAL_CHARSET),
	"city": random_string(charset=SPECIAL_CHARSET),
	"postcode": random_string(numeric=True),
	"profilepath": random_string(charset=SPECIAL_CHARSET),
	"scriptpath": random_string(charset=SPECIAL_CHARSET),
	"homeTelephoneNumber": random_string(numeric=True),
	"mobileTelephoneNumber": random_string(numeric=True),
	"pagerTelephoneNumber": random_string(numeric=True),
	"sambaUserWorkstations": random_string(numeric=True)}


@pytest.mark.parametrize("udm_user", [
	NORMAL_SIMPLE_USER, NORMAL_COMPLEX_USER, UTF8_SIMPLE_USER,
	UTF8_COMPLEX_USER, SPECIAL_SIMPLE_USER, SPECIAL_COMPLEX_USER
], ids=[
	"NORMAL_SIMPLE_USER", "NORMAL_COMPLEX_USER", "UTF8_SIMPLE_USER",
	"UTF8_COMPLEX_USER", "SPECIAL_SIMPLE_USER", "SPECIAL_COMPLEX_USER"
])
@pytest.mark.parametrize("sync_mode", ["write", "sync"])
@pytest.mark.skipif(not connector_running_on_this_host(), reason="Univention AD Connector not configured.")
def test_user_sync_from_udm_to_ad(udm_user, sync_mode):
	print("\n###################")
	print("running test_user_sync_from_udm_to_ad({}, {})".format(udm_user, sync_mode))
	print("###################\n")

	user_syntax = "directory/manager/web/modules/users/user/properties/username/syntax=string"
	with testing_ucr.UCSTestConfigRegistry():
		ucr_set([user_syntax])
		restart_univention_cli_server()
		ad_in_sync_mode(sync_mode)
		with UCSTestUDM() as udm:
			selection = ("username", "firstname", "lastname")
			basic_udm_user = {k: v for (k, v) in udm_user.iteritems() if k in selection}

			print("\nCreating UDM user {}\n".format(basic_udm_user))
			(udm_user_dn, username) = udm.create_user(**basic_udm_user)
			ad_user_dn = ldap.dn.dn2str([
				[("CN", username, ldap.AVA_STRING)],
				[("CN", "users", ldap.AVA_STRING)]] + ldap.dn.str2dn(AD.adldapbase))
			adconnector.wait_for_sync()
			AD.verify_object(ad_user_dn, adconnector.map_udm_user_to_ad(basic_udm_user))

			print("\nModifying UDM user\n")
			udm.modify_object('users/user', dn=udm_user_dn, **udm_user)
			adconnector.wait_for_sync()
			AD.verify_object(ad_user_dn, adconnector.map_udm_user_to_ad(udm_user))

			print("\nDeleting UDM user\n")
			udm.remove_object('users/user', dn=udm_user_dn)
			adconnector.wait_for_sync()
			AD.verify_object(ad_user_dn, None)


@pytest.mark.parametrize("udm_user", [
	NORMAL_SIMPLE_USER, NORMAL_COMPLEX_USER, UTF8_SIMPLE_USER,
	UTF8_COMPLEX_USER, SPECIAL_SIMPLE_USER, SPECIAL_COMPLEX_USER
], ids=[
	"NORMAL_SIMPLE_USER", "NORMAL_COMPLEX_USER", "UTF8_SIMPLE_USER",
	"UTF8_COMPLEX_USER", "SPECIAL_SIMPLE_USER", "SPECIAL_COMPLEX_USER"
])
@pytest.mark.parametrize("sync_mode", ["read", "sync"])
@pytest.mark.skipif(not connector_running_on_this_host(), reason="Univention AD Connector not configured.")
def test_user_sync_from_ad_to_udm(udm_user, sync_mode):
	print("\n###################")
	print("running test_user_sync_from_ad_to_udm({}, {})".format(udm_user, sync_mode))
	print("###################\n")

	user_syntax = "directory/manager/web/modules/users/user/properties/username/syntax=string"
	with testing_ucr.UCSTestConfigRegistry():
		ucr_set([user_syntax])
		restart_univention_cli_server()
		ad_in_sync_mode(sync_mode)

		selection = ("username", "firstname", "lastname")
		basic_udm_user = {k: v for (k, v) in udm_user.iteritems() if k in selection}
		basic_ad_user = adconnector.map_udm_user_to_ad(basic_udm_user)

		print("\nCreating AD user {}\n".format(basic_ad_user))
		username = udm_user.get("username")
		ad_user_dn = AD.createuser(username, **basic_ad_user)
		udm_user_dn = ldap.dn.dn2str([
			[("uid", username, ldap.AVA_STRING)],
			[("CN", "users", ldap.AVA_STRING)]] + ldap.dn.str2dn(UCSTestUDM.LDAP_BASE))
		adconnector.wait_for_sync()
		adconnector.verify_udm_object("users/user", udm_user_dn, basic_udm_user)

		print("\nModifying AD user {!r}\n".format(ad_user_dn))
		AD.set_attributes(ad_user_dn, **adconnector.map_udm_user_to_ad(udm_user))
		adconnector.wait_for_sync()
		adconnector.verify_udm_object("users/user", udm_user_dn, udm_user)

		print("\nDeleting AD user {!r}\n".format(ad_user_dn))
		AD.delete(ad_user_dn)
		adconnector.wait_for_sync()
		adconnector.verify_udm_object("users/user", udm_user_dn, None)
