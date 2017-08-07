#!/usr/share/ucs-test/runner /usr/bin/py.test -s
# coding: utf-8
## desc: "Test the UCS<->AD sync in {read,write,sync} mode with users"
## exposure: dangerous
## packages:
## - univention-s4-connector
## bugs:
##  - 43598

import ldap
import pytest

from univention.testing.udm import UCSTestUDM
import univention.testing.strings as tstrings
import univention.testing.ucr as testing_ucr
from univention.config_registry import handler_set as ucr_set

import s4connector
from s4connector import s4_in_sync_mode
from s4connector import restart_univention_cli_server
from s4connector import connector_running_on_this_host


UTF8_CHARSET = tstrings.STR_UMLAUT + u"КирилицаКириллицаĆirilicaЋирилица" + u"普通話普通话"
SPECIAL_CHARSET = tstrings.STR_SPECIAL_CHARACTER
# we exclude '$' as it has special meaning and '#"' as the S4C sync can't
# handle them (see bug #44373)
FORBIDDEN_SAMACCOUNTNAME = "\\/[]:;|=,+*?<>@ " + '$' + '#"'
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
@pytest.mark.skipif(not connector_running_on_this_host(), reason="Univention S4 Connector not configured.")
def test_user_sync_from_udm_to_s4(udm_user, sync_mode):
	print("\n###################")
	print("running test_user_sync_from_udm_to_s4({}, {})".format(udm_user, sync_mode))
	print("###################\n")

	user_syntax = "directory/manager/web/modules/users/user/properties/username/syntax=string"
	with testing_ucr.UCSTestConfigRegistry():
		ucr_set([user_syntax])
		restart_univention_cli_server()
		s4_in_sync_mode(sync_mode)
		with UCSTestUDM() as udm:
			s4 = s4connector.S4Connection()

			selection = ("username", "firstname", "lastname")
			basic_udm_user = {k: v for (k, v) in udm_user.iteritems() if k in selection}

			print("\nCreating UDM user {}\n".format(basic_udm_user))
			(udm_user_dn, username) = udm.create_user(**basic_udm_user)
			s4_user_dn = ldap.dn.dn2str([
				[("CN", username, ldap.AVA_STRING)],
				[("CN", "users", ldap.AVA_STRING)]] + ldap.dn.str2dn(s4.adldapbase))
			s4connector.wait_for_sync()
			s4.verify_object(s4_user_dn, s4connector.map_udm_user_to_s4(basic_udm_user))

			print("\nModifying UDM user\n")
			udm.modify_object('users/user', dn=udm_user_dn, **udm_user)
			s4connector.wait_for_sync()
			s4.verify_object(s4_user_dn, s4connector.map_udm_user_to_s4(udm_user))

			print("\nDeleting UDM user\n")
			udm.remove_object('users/user', dn=udm_user_dn)
			s4connector.wait_for_sync()
			s4.verify_object(s4_user_dn, None)


@pytest.mark.parametrize("udm_user", [
	NORMAL_SIMPLE_USER, NORMAL_COMPLEX_USER, UTF8_SIMPLE_USER,
	UTF8_COMPLEX_USER, SPECIAL_SIMPLE_USER, SPECIAL_COMPLEX_USER
], ids=[
	"NORMAL_SIMPLE_USER", "NORMAL_COMPLEX_USER", "UTF8_SIMPLE_USER",
	"UTF8_COMPLEX_USER", "SPECIAL_SIMPLE_USER", "SPECIAL_COMPLEX_USER"
])
@pytest.mark.parametrize("sync_mode", ["read", "sync"])
@pytest.mark.skipif(not connector_running_on_this_host(), reason="Univention S4 Connector not configured.")
def test_user_sync_from_s4_to_udm(udm_user, sync_mode):
	print("\n###################")
	print("running test_user_sync_from_s4_to_udm({}, {})".format(udm_user, sync_mode))
	print("###################\n")

	user_syntax = "directory/manager/web/modules/users/user/properties/username/syntax=string"
	with testing_ucr.UCSTestConfigRegistry():
		ucr_set([user_syntax])
		restart_univention_cli_server()
		s4_in_sync_mode(sync_mode)

		s4 = s4connector.S4Connection()

		selection = ("username", "firstname", "lastname")
		basic_udm_user = {k: v for (k, v) in udm_user.iteritems() if k in selection}
		basic_s4_user = s4connector.map_udm_user_to_s4(basic_udm_user)

		print("\nCreating S4 user {}\n".format(basic_s4_user))
		username = udm_user.get("username")
		s4_user_dn = s4.createuser(username, **basic_s4_user)
		udm_user_dn = ldap.dn.dn2str([
			[("uid", username, ldap.AVA_STRING)],
			[("CN", "users", ldap.AVA_STRING)]] + ldap.dn.str2dn(UCSTestUDM.LDAP_BASE))
		s4connector.wait_for_sync()
		s4connector.verify_udm_object("users/user", udm_user_dn, basic_udm_user)

		print("\nModifying S4 user\n")
		s4.set_attributes(s4_user_dn, **s4connector.map_udm_user_to_s4(udm_user))
		s4connector.wait_for_sync()
		s4connector.verify_udm_object("users/user", udm_user_dn, udm_user)

		print("\nDeleting S4 user\n")
		s4.delete(s4_user_dn)
		s4connector.wait_for_sync()
		s4connector.verify_udm_object("users/user", udm_user_dn, None)
