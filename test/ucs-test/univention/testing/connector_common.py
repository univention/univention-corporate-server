# coding: utf-8

from __future__ import print_function
import ldap
import subprocess

import univention.testing.strings as tstrings
from univention.testing.udm import verify_udm_object

import univention.config_registry

configRegistry = univention.config_registry.ConfigRegistry()
configRegistry.load()

UTF8_CHARSET = tstrings.STR_UMLAUT + u"КирилицаКириллицаĆirilicaЋирилица" + u"普通話普通话"
# the CON sync can't # handle them (see bug #44373)
SPECIAL_CHARSET = "".join(set(tstrings.STR_SPECIAL_CHARACTER) - set('\\#"?'))
# We exclude '$' as it has special meaning . A '.' (dot) may not be the last
# character in a samAccountName, so we forbid it as well.
FORBIDDEN_SAMACCOUNTNAME = "\\/[]:;|=,+*?<>@ " + '$.'
SPECIAL_CHARSET_USERNAME = "".join(set(SPECIAL_CHARSET) - set(FORBIDDEN_SAMACCOUNTNAME))


def random_string(length=10, alpha=False, numeric=False, charset=None, encoding='utf-8'):
	return tstrings.random_string(length, alpha, numeric, charset, encoding)


def normalize_dn(dn):
	"""
	Normalize a given dn. This removes some escaping of special chars in the
	DNs. Note: The CON-LDAP returns DNs with escaping chars, OpenLDAP does not.

	>>> normalize_dn("cn=peter\#,cn=groups")
	'cn=peter#,cn=groups'
	"""
	return ldap.dn.dn2str(ldap.dn.str2dn(dn))


def to_unicode(string):
	if isinstance(string, unicode):
		return string
	return unicode(string, 'utf-8')


def restart_univention_cli_server():
	print("Restarting Univention-CLI-Server")
	subprocess.call(["pkill", "-f", "univention-cli-server"])


class TestUser(object):
	def __init__(self, user, rename={}, container=None, selection=None):
		selection = selection or ("username", "firstname", "lastname")
		self.basic = {k: v for (k, v) in user.iteritems() if k in selection}
		self.user = user
		self.rename = dict(self.basic)
		self.rename.update(rename)
		self.container = container

	def __repr__(self):
		args = (self.user, self.rename, self.container)
		return "{}({})".format(self.__class__.__name__, ", ".join(repr(a) for a in args))


class NormalUser(TestUser):
	def __init__(self, selection=None):
		super(NormalUser, self).__init__(
			user={
				"username": tstrings.random_username(),
				"firstname": tstrings.random_name(),
				"lastname": tstrings.random_name(),
				"description": random_string(alpha=True, numeric=True),
				"street": random_string(alpha=True, numeric=True),
				"city": random_string(alpha=True, numeric=True),
				"postcode": random_string(numeric=True),
				"profilepath": random_string(alpha=True, numeric=True),
				"scriptpath": random_string(alpha=True, numeric=True),
				"phone": random_string(numeric=True),
				"homeTelephoneNumber": random_string(numeric=True),
				"mobileTelephoneNumber": random_string(numeric=True),
				"pagerTelephoneNumber": random_string(numeric=True),
				"sambaUserWorkstations": random_string(numeric=True)
			},
			rename={"username": tstrings.random_username()},
			container=tstrings.random_name(),
			selection=selection,
		)


class Utf8User(TestUser):
	def __init__(self, selection=None):
		super(Utf8User, self).__init__(
			user={
				"username": random_string(charset=UTF8_CHARSET),
				"firstname": random_string(charset=UTF8_CHARSET),
				"lastname": random_string(charset=UTF8_CHARSET),
				"description": random_string(charset=UTF8_CHARSET),
				"street": random_string(charset=UTF8_CHARSET),
				"city": random_string(charset=UTF8_CHARSET),
				"postcode": random_string(numeric=True),
				"profilepath": random_string(charset=UTF8_CHARSET),
				"scriptpath": random_string(charset=UTF8_CHARSET),
				"phone": random_string(numeric=True),
				"homeTelephoneNumber": random_string(numeric=True),
				"mobileTelephoneNumber": random_string(numeric=True),
				"pagerTelephoneNumber": random_string(numeric=True),
				"sambaUserWorkstations": random_string(numeric=True)
			},
			rename={"username": random_string(charset=UTF8_CHARSET)},
			container=random_string(charset=UTF8_CHARSET),
			selection=selection,
		)


class SpecialUser(TestUser):
	def __init__(self, selection=None):
		super(SpecialUser, self).__init__(
			user={
				"username": random_string(charset=SPECIAL_CHARSET_USERNAME),
				"firstname": tstrings.random_name_special_characters(),
				"lastname": tstrings.random_name_special_characters(),
				"description": random_string(charset=SPECIAL_CHARSET),
				"street": random_string(charset=SPECIAL_CHARSET),
				"city": random_string(charset=SPECIAL_CHARSET),
				"postcode": random_string(numeric=True),
				"profilepath": random_string(charset=SPECIAL_CHARSET),
				"scriptpath": random_string(charset=SPECIAL_CHARSET),
				"phone": random_string(numeric=True),
				"homeTelephoneNumber": random_string(numeric=True),
				"mobileTelephoneNumber": random_string(numeric=True),
				"pagerTelephoneNumber": random_string(numeric=True),
				"sambaUserWorkstations": random_string(numeric=True)
			},
			rename={"username": random_string(charset=SPECIAL_CHARSET_USERNAME)},
			container=random_string(charset=SPECIAL_CHARSET),
			selection=selection,
		)


class TestGroup(object):
	def __init__(self, group, rename={}, container=None):
		self.group = group
		self.rename = dict(self.group)
		self.rename.update(rename)
		self.container = container

	def __repr__(self):
		args = (self.group, self.rename, self.container)
		return "{}({})".format(self.__class__.__name__, ", ".join(repr(a) for a in args))


class NormalGroup(TestGroup):
	def __init__(self):
		super(NormalGroup, self).__init__(
			group={
				"name": tstrings.random_groupname(),
				"description": random_string(alpha=True, numeric=True)
			},
			rename={"name": tstrings.random_groupname()},
			container=tstrings.random_name(),
		)


class Utf8Group(TestGroup):
	def __init__(self):
		super(Utf8Group, self).__init__(
			group={
				"name": random_string(charset=UTF8_CHARSET),
				"description": random_string(charset=UTF8_CHARSET)
			},
			rename={"name": tstrings.random_string(charset=UTF8_CHARSET)},
			container=random_string(charset=UTF8_CHARSET),
		)


class SpecialGroup(TestGroup):
	def __init__(self):
		super(SpecialGroup, self).__init__(
			group={
				"name": random_string(charset=SPECIAL_CHARSET_USERNAME),
				"description": random_string(charset=SPECIAL_CHARSET)
			},
			rename={"name": tstrings.random_string(charset=SPECIAL_CHARSET_USERNAME)},
			container=random_string(charset=SPECIAL_CHARSET),
		)


def map_udm_user_to_con(user):
	"""
	Map a UDM user given as a dictionary of `property`:`values` mappings to a
	dictionary of `attributes`:`values` mappings as required by the CON-LDAP.
	Note: This expects the properties from the UDM users/user module and not
	OpenLDAP-attributes!.
	"""
	mapping = {
		"username": "sAMAccountName",
		"firstname": "givenName",
		"lastname": "sn",
		"description": "description",
		"street": "streetAddress",
		"city": "l",
		"postcode": "postalCode",
		"profilepath": "profilePath",
		"scriptpath": "scriptPath",
		"phone": "telephoneNumber",
		"homeTelephoneNumber": "homePhone",
		"mobileTelephoneNumber": "mobile",
		"pagerTelephoneNumber": "pager",
		"sambaUserWorkstations": "userWorkstations"}
	return {mapping.get(key): value for (key, value) in user.iteritems() if key in mapping}


def map_udm_group_to_con(group):
	"""
	Map a UDM group given as a dictionary of `property`:`values` mappings to a
	dictionary of `attributes`:`values` mappings as required by the CON-LDAP.
	Note: This expects the properties from the UDM groups/group module and not
	OpenLDAP-attributes!.
	"""
	mapping = {"name": "sAMAccountName", "description": "description"}
	return {mapping.get(key): value for (key, value) in group.iteritems() if key in mapping}


def create_udm_user(udm, con, user, wait_for_sync):
	print("\nCreating UDM user {}\n".format(user.basic))
	(udm_user_dn, username) = udm.create_user(**user.basic)
	con_user_dn = ldap.dn.dn2str([
		[("CN", username, ldap.AVA_STRING)],
		[("CN", "users", ldap.AVA_STRING)]] + ldap.dn.str2dn(con.adldapbase))
	wait_for_sync()
	con.verify_object(con_user_dn, map_udm_user_to_con(user.basic))
	return (udm_user_dn, con_user_dn)


def delete_udm_user(udm, con, udm_user_dn, con_user_dn, wait_for_sync):
	print("\nDeleting UDM user\n")
	udm.remove_object('users/user', dn=udm_user_dn)
	wait_for_sync()
	con.verify_object(con_user_dn, None)


def create_con_user(con, udm_user, wait_for_sync):
	basic_con_user = map_udm_user_to_con(udm_user.basic)

	print("\nCreating CON user {}\n".format(basic_con_user))
	username = udm_user.basic.get("username")
	con_user_dn = con.createuser(username, **basic_con_user)
	udm_user_dn = ldap.dn.dn2str([
		[("uid", username, ldap.AVA_STRING)],
		[("CN", "users", ldap.AVA_STRING)]] + ldap.dn.str2dn(configRegistry.get('ldap/base')))
	wait_for_sync()
	verify_udm_object("users/user", udm_user_dn, udm_user.basic)
	return (basic_con_user, con_user_dn, udm_user_dn)


def delete_con_user(con, con_user_dn, udm_user_dn, wait_for_sync):
	print("\nDeleting CON user\n")
	con.delete(con_user_dn)
	wait_for_sync()
	verify_udm_object("users/user", udm_user_dn, None)


def create_udm_group(udm, con, group, wait_for_sync):
	print("\nCreating UDM group {}\n".format(group))
	(udm_group_dn, groupname) = udm.create_group(**group.group)
	con_group_dn = ldap.dn.dn2str([
		[("CN", groupname, ldap.AVA_STRING)],
		[("CN", "groups", ldap.AVA_STRING)]] + ldap.dn.str2dn(con.adldapbase))
	wait_for_sync()
	con.verify_object(con_group_dn, map_udm_group_to_con(group.group))
	return (udm_group_dn, con_group_dn)


def delete_udm_group(udm, con, udm_group_dn, con_group_dn, wait_for_sync):
	print("\nDeleting UDM group\n")
	udm.remove_object('groups/group', dn=udm_group_dn)
	wait_for_sync()
	con.verify_object(con_group_dn, None)


def create_con_group(con, udm_group, wait_for_sync):
	con_group = map_udm_group_to_con(udm_group.group)

	print("\nCreating CON group {}\n".format(con_group))
	groupname = udm_group.group.get("name")
	con_group_dn = con.group_create(groupname, **con_group)
	udm_group_dn = ldap.dn.dn2str([
		[("cn", groupname, ldap.AVA_STRING)],
		[("CN", "groups", ldap.AVA_STRING)]] + ldap.dn.str2dn(configRegistry.get('ldap/base')))
	wait_for_sync()
	verify_udm_object("groups/group", udm_group_dn, udm_group.group)
	return (con_group, con_group_dn, udm_group_dn)


def delete_con_group(con, con_group_dn, udm_group_dn, wait_for_sync):
	print("\nDeleting CON group\n")
	con.delete(con_group_dn)
	wait_for_sync()
	verify_udm_object("groups/group", udm_group_dn, None)
