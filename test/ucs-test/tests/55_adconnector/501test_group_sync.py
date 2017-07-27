#!/usr/share/ucs-test/runner /usr/bin/py.test -s
# coding: utf-8
## desc: "Test the UCS<->AD sync in {read,write,sync} mode with groups"
## exposure: dangerous
## packages:
## - univention-ad-connector
## bugs:
##  - 11658

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


def normal_group():
	return {"name": tstrings.random_groupname(),
			"description": random_string(alpha=True, numeric=True)}


def utf8_group():
	return {"name": random_string(charset=UTF8_CHARSET),
		"description": random_string(charset=UTF8_CHARSET)}


def special_group():
	return {"name": random_string(charset=SPECIAL_CHARSET_USERNAME),
		"description": random_string(charset=SPECIAL_CHARSET)}


def utf8_user():
	return {"username": random_string(charset=UTF8_CHARSET),
		"firstname": random_string(charset=UTF8_CHARSET),
		"lastname": random_string(charset=UTF8_CHARSET),
		"description": random_string(charset=UTF8_CHARSET)}


def special_user():
	return {"username": random_string(charset=SPECIAL_CHARSET_USERNAME),
		"firstname": tstrings.random_name_special_characters(),
		"lastname": tstrings.random_name_special_characters(),
		"description": random_string(charset=SPECIAL_CHARSET)}


def udm_user_factory(udm_user, udm, ad):
	print("\nCreating UDM user {}\n".format(udm_user))
	(udm_user_dn, username) = udm.create_user(**udm_user)
	ad_user_dn = ldap.dn.dn2str([[("CN", username, ldap.AVA_STRING)],
		[("CN", "users", ldap.AVA_STRING)]] + ldap.dn.str2dn(ad.adldapbase))
	return ({"users": [udm_user_dn]}, {"member": [ad_user_dn]})


def ad_user_factory(udm_user, ad):
	ad_user = adconnector.map_udm_user_to_ad(udm_user)
	print("\nCreating AD user {}\n".format(ad_user))
	username = udm_user.get("username")
	ad_user_dn = ad.createuser(username, **ad_user)
	udm_user_dn = ldap.dn.dn2str([[("uid", username, ldap.AVA_STRING)],
		[("CN", "users", ldap.AVA_STRING)]] + ldap.dn.str2dn(UCSTestUDM.LDAP_BASE))
	return ({"users": [udm_user_dn]}, {"member": [ad_user_dn]})


def udm_group_factory(udm_group, udm, ad):
	print("\nCreating UDM group {}\n".format(udm_group))
	(udm_group_dn, groupname) = udm.create_group(**udm_group)
	ad_group_dn = ldap.dn.dn2str([[("CN", groupname, ldap.AVA_STRING)],
		[("CN", "groups", ldap.AVA_STRING)]] + ldap.dn.str2dn(ad.adldapbase))
	return ({"nestedGroup": [udm_group_dn]}, {"member": [ad_group_dn]})


def ad_group_factory(udm_group, ad):
	ad_group = adconnector.map_udm_group_to_ad(udm_group)
	print("\nCreating AD group {}\n".format(ad_group))
	groupname = udm_group.get("name")
	ad_group_dn = ad.group_create(groupname, **ad_group)
	udm_group_dn = ldap.dn.dn2str([[("cn", groupname, ldap.AVA_STRING)],
		[("CN", "groups", ldap.AVA_STRING)]] + ldap.dn.str2dn(UCSTestUDM.LDAP_BASE))
	return ({"nestedGroup": [udm_group_dn]}, {"member": [ad_group_dn]})


@pytest.mark.skipif(not connector_running_on_this_host(),
	reason="Univention AD Connector not configured.")
def test_group_sync_from_udm_to_ad(udm_group, member_factory, sync_mode):
	print("\n###################")
	print("running test_group_sync_from_udm_to_ad({}, {})".format(udm_group, sync_mode))
	print("###################\n")

	group_syntax = "directory/manager/web/modules/groups/group/properties/name/syntax=string"
	user_syntax = "directory/manager/web/modules/users/user/properties/username/syntax=string"
	with testing_ucr.UCSTestConfigRegistry():
		ucr_set([group_syntax, user_syntax])
		restart_univention_cli_server()
		ad_in_sync_mode(sync_mode)
		with UCSTestUDM() as udm:
			print("\nCreating UDM group {}\n".format(udm_group))
			(udm_group_dn, groupname) = udm.create_group(**udm_group)
			ad_group_dn = ldap.dn.dn2str([[("CN", groupname, ldap.AVA_STRING)],
				[("CN", "groups", ldap.AVA_STRING)]] + ldap.dn.str2dn(AD.adldapbase))
			adconnector.wait_for_sync()
			AD.verify_object(ad_group_dn, adconnector.map_udm_group_to_ad(udm_group))

			if member_factory is not None:
				print("\nModifying UDM group\n")
				(udm_attributes, ad_attributes) = member_factory(udm, AD)
				udm.modify_object('groups/group', dn=udm_group_dn, **udm_attributes)
				adconnector.wait_for_sync()
				ad_group = adconnector.map_udm_group_to_ad(udm_group)
				ad_group.update(ad_attributes)
				AD.verify_object(ad_group_dn, ad_group)

			print("\nDeleting UDM group\n")
			udm.remove_object('groups/group', dn=udm_group_dn)
			adconnector.wait_for_sync()
			AD.verify_object(ad_group_dn, None)


@pytest.mark.skipif(not connector_running_on_this_host(),
	reason="Univention AD Connector not configured.")
def test_group_sync_from_ad_to_udm(udm_group, member_factory, sync_mode):
	print("\n###################")
	print("running test_group_sync_from_ad_to_udm({}, {})".format(udm_group, sync_mode))
	print("###################\n")

	group_syntax = "directory/manager/web/modules/groups/group/properties/name/syntax=string"
	user_syntax = "directory/manager/web/modules/users/user/properties/username/syntax=string"
	with testing_ucr.UCSTestConfigRegistry():
		ucr_set([group_syntax, user_syntax])
		restart_univention_cli_server()
		ad_in_sync_mode(sync_mode)

		ad_group = adconnector.map_udm_group_to_ad(udm_group)

		print("\nCreating AD group {}\n".format(ad_group))
		groupname = udm_group.get("name")
		ad_group_dn = AD.group_create(groupname, **ad_group)
		udm_group_dn = ldap.dn.dn2str([[("cn", groupname, ldap.AVA_STRING)],
			[("CN", "groups", ldap.AVA_STRING)]] + ldap.dn.str2dn(UCSTestUDM.LDAP_BASE))
		adconnector.wait_for_sync()
		adconnector.verify_udm_object("groups/group", udm_group_dn, udm_group)

		if member_factory is not None:
			print("\nModifying AD group\n")
			(udm_attributes, ad_attributes) = member_factory(AD)
			AD.set_attributes(ad_group_dn, **ad_attributes)
			adconnector.wait_for_sync()
			udm_attributes.update(udm_group)
			adconnector.verify_udm_object("groups/group", udm_group_dn, udm_attributes)

		print("\nDeleting AD group\n")
		AD.delete(ad_group_dn)
		adconnector.wait_for_sync()
		adconnector.verify_udm_object("groups/group", udm_group_dn, None)


def pytest_generate_tests(metafunc):
	def generate():
		for udm_group in [normal_group, utf8_group, special_group]:
			if "udm_to_ad" in metafunc.function.__name__:
				yield (udm_group(), None, "sync")
				yield (udm_group(), None, "write")
			if "ad_to_udm" in metafunc.function.__name__:
				yield (udm_group(), None, "sync")
				yield (udm_group(), None, "read")

		# XXX Special-Groups are skipped (see bug #44374)
		for nested_group in [utf8_group]: #, special_group]:
			if "udm_to_ad" in metafunc.function.__name__:
				def udm_member_factory(*args, **kwargs):
					return udm_group_factory(nested_group(), *args, **kwargs)
				udm_member_factory.nested = nested_group.__name__
				yield (special_group(), udm_member_factory, "sync")
				yield (special_group(), udm_member_factory, "write")
			elif "ad_to_udm" in metafunc.function.__name__:
				def ad_member_factory(*args, **kwargs):
					return ad_group_factory(nested_group(), *args, **kwargs)
				ad_member_factory.nested = nested_group.__name__
				yield (special_group(), ad_member_factory, "sync")
				yield (special_group(), ad_member_factory, "read")

		# XXX Special-Groups are skipped (see bug #44374)
		for nested_user in [utf8_user]: #, special_user]:
			if "udm_to_ad" in metafunc.function.__name__:
				def udm_member_factory(*args, **kwargs):
					return udm_user_factory(nested_user(), *args, **kwargs)
				udm_member_factory.nested = nested_user.__name__
				yield (special_group(), udm_member_factory, "sync")
				yield (special_group(), udm_member_factory, "write")
			elif "ad_to_udm" in metafunc.function.__name__:
				def ad_member_factory(*args, **kwargs):
					return ad_user_factory(nested_user(), *args, **kwargs)
				ad_member_factory.nested = nested_user.__name__
				yield (special_group(), ad_member_factory, "sync")
				yield (special_group(), ad_member_factory, "read")

	def id_function(parameter, value):
		if callable(value):
			str_id = getattr(value, "nested", value.__name__)
		else:
			str_id = repr(value)
		return "{}={}".format(parameter, str_id)

	argvalues = list(generate())
	parameters = ("udm_group", "member_factory", "sync_mode")
	ids = [", ".join(id_function(p, v) for (p, v) in zip(parameters, values))
		for values in argvalues]
	metafunc.parametrize(",".join(parameters), argvalues, ids=ids)
