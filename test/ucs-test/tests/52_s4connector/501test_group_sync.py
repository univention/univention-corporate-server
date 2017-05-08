#!/usr/share/ucs-test/runner /usr/bin/py.test -s
# coding: utf-8
## desc: "Test the UCS<->AD sync in {read,write,sync} mode with groups"
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


def udm_user_factory(udm_user, udm, s4):
	print("\nCreating UDM user {}\n".format(udm_user))
	(udm_user_dn, username) = udm.create_user(**udm_user)
	s4_user_dn = ldap.dn.dn2str([[("CN", username, ldap.AVA_STRING)],
		[("CN", "users", ldap.AVA_STRING)]] + ldap.dn.str2dn(s4.adldapbase))
	return ({"users": [udm_user_dn]}, {"member": [s4_user_dn]})


def s4_user_factory(udm_user, s4):
	s4_user = s4connector.map_udm_user_to_s4(udm_user)
	print("\nCreating S4 user {}\n".format(s4_user))
	username = udm_user.get("username")
	s4_user_dn = s4.createuser(username, **s4_user)
	udm_user_dn = ldap.dn.dn2str([[("uid", username, ldap.AVA_STRING)],
		[("CN", "users", ldap.AVA_STRING)]] + ldap.dn.str2dn(UCSTestUDM.LDAP_BASE))
	return ({"users": [udm_user_dn]}, {"member": [s4_user_dn]})


def udm_group_factory(udm_group, udm, s4):
	print("\nCreating UDM group {}\n".format(udm_group))
	(udm_group_dn, groupname) = udm.create_group(**udm_group)
	s4_group_dn = ldap.dn.dn2str([[("CN", groupname, ldap.AVA_STRING)],
		[("CN", "groups", ldap.AVA_STRING)]] + ldap.dn.str2dn(s4.adldapbase))
	return ({"nestedGroup": [udm_group_dn]}, {"member": [s4_group_dn]})


def s4_group_factory(udm_group, s4):
	s4_group = s4connector.map_udm_group_to_s4(udm_group)
	print("\nCreating S4 group {}\n".format(s4_group))
	groupname = udm_group.get("name")
	s4_group_dn = s4.group_create(groupname, **s4_group)
	udm_group_dn = ldap.dn.dn2str([[("cn", groupname, ldap.AVA_STRING)],
		[("CN", "groups", ldap.AVA_STRING)]] + ldap.dn.str2dn(UCSTestUDM.LDAP_BASE))
	return ({"nestedGroup": [udm_group_dn]}, {"member": [s4_group_dn]})


@pytest.mark.skipif(not connector_running_on_this_host(),
	reason="Univention S4 Connector not configured.")
def test_group_sync_from_udm_to_s4(udm_group, member_factory, sync_mode):
	print("\n###################")
	print("running test_group_sync_from_udm_to_s4({}, {})".format(udm_group, sync_mode))
	print("###################\n")

	group_syntax = "directory/manager/web/modules/groups/group/properties/name/syntax=string"
	user_syntax = "directory/manager/web/modules/users/user/properties/username/syntax=string"
	with testing_ucr.UCSTestConfigRegistry():
		ucr_set([group_syntax, user_syntax])
		restart_univention_cli_server()
		s4_in_sync_mode(sync_mode)
		with UCSTestUDM() as udm:
			s4 = s4connector.S4Connection()

			print("\nCreating UDM group {}\n".format(udm_group))
			(udm_group_dn, groupname) = udm.create_group(**udm_group)
			s4_group_dn = ldap.dn.dn2str([[("CN", groupname, ldap.AVA_STRING)],
				[("CN", "groups", ldap.AVA_STRING)]] + ldap.dn.str2dn(s4.adldapbase))
			s4connector.wait_for_sync()
			s4.verify_object(s4_group_dn, s4connector.map_udm_group_to_s4(udm_group))

			if member_factory is not None:
				print("\nModifying UDM group\n")
				(udm_attributes, s4_attributes) = member_factory(udm, s4)
				udm.modify_object('groups/group', dn=udm_group_dn, **udm_attributes)
				s4connector.wait_for_sync()
				s4_group = s4connector.map_udm_group_to_s4(udm_group)
				s4_group.update(s4_attributes)
				s4.verify_object(s4_group_dn, s4_group)

			print("\nDeleting UDM group\n")
			udm.remove_object('groups/group', dn=udm_group_dn)
			s4connector.wait_for_sync()
			s4.verify_object(s4_group_dn, None)


@pytest.mark.skipif(not connector_running_on_this_host(),
	reason="Univention S4 Connector not configured.")
def test_group_sync_from_s4_to_udm(udm_group, member_factory, sync_mode):
	print("\n###################")
	print("running test_group_sync_from_s4_to_udm({}, {})".format(udm_group, sync_mode))
	print("###################\n")

	group_syntax = "directory/manager/web/modules/groups/group/properties/name/syntax=string"
	user_syntax = "directory/manager/web/modules/users/user/properties/username/syntax=string"
	with testing_ucr.UCSTestConfigRegistry():
		ucr_set([group_syntax, user_syntax])
		restart_univention_cli_server()
		s4_in_sync_mode(sync_mode)

		s4 = s4connector.S4Connection()
		s4_group = s4connector.map_udm_group_to_s4(udm_group)

		print("\nCreating S4 group {}\n".format(s4_group))
		groupname = udm_group.get("name")
		s4_group_dn = s4.group_create(groupname, **s4_group)
		udm_group_dn = ldap.dn.dn2str([[("cn", groupname, ldap.AVA_STRING)],
			[("CN", "groups", ldap.AVA_STRING)]] + ldap.dn.str2dn(UCSTestUDM.LDAP_BASE))
		s4connector.wait_for_sync()
		s4connector.verify_udm_object("groups/group", udm_group_dn, udm_group)

		if member_factory is not None:
			print("\nModifying S4 group\n")
			(udm_attributes, s4_attributes) = member_factory(s4)
			s4.set_attributes(s4_group_dn, **s4_attributes)
			s4connector.wait_for_sync()
			udm_attributes.update(udm_group)
			s4connector.verify_udm_object("groups/group", udm_group_dn, udm_attributes)

		print("\nDeleting S4 group\n")
		s4.delete(s4_group_dn)
		s4connector.wait_for_sync()
		s4connector.verify_udm_object("groups/group", udm_group_dn, None)


def pytest_generate_tests(metafunc):
	def generate():
		for udm_group in [normal_group, utf8_group, special_group]:
			if "udm_to_s4" in metafunc.function.__name__:
				yield (udm_group(), None, "sync")
				yield (udm_group(), None, "write")
			elif "s4_to_udm" in metafunc.function.__name__:
				yield (udm_group(), None, "sync")
				yield (udm_group(), None, "read")

		# XXX Special-Groups are skipped until bug #44374 is fixed.
		for nested_group in [utf8_group]: #, special_group]:
			if "udm_to_s4" in metafunc.function.__name__:
				def udm_member_factory(*args, **kwargs):
					return udm_group_factory(nested_group(), *args, **kwargs)
				udm_member_factory.nested = nested_group.__name__
				yield (special_group(), udm_member_factory, "sync")
				yield (special_group(), udm_member_factory, "write")
			elif "s4_to_udm" in metafunc.function.__name__:
				def s4_member_factory(*args, **kwargs):
					return s4_group_factory(nested_group(), *args, **kwargs)
				s4_member_factory.nested = nested_group.__name__
				yield (special_group(), s4_member_factory, "sync")
				yield (special_group(), s4_member_factory, "read")

		# XXX Special-Groups are skipped until bug #44374 is fixed.
		for nested_user in [utf8_user]: #, special_user]:
			if "udm_to_s4" in metafunc.function.__name__:
				def udm_member_factory(*args, **kwargs):
					return udm_user_factory(nested_user(), *args, **kwargs)
				udm_member_factory.nested = nested_user.__name__
				yield (special_group(), udm_member_factory, "sync")
				yield (special_group(), udm_member_factory, "write")
			elif "s4_to_udm" in metafunc.function.__name__:
				def s4_member_factory(*args, **kwargs):
					return s4_user_factory(nested_user(), *args, **kwargs)
				s4_member_factory.nested = nested_user.__name__
				yield (special_group(), s4_member_factory, "sync")
				yield (special_group(), s4_member_factory, "read")

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
