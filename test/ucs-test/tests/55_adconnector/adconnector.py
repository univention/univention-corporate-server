import os
import sys

TEST_LIB_PATH = os.getenv('TESTLIBPATH')
if TEST_LIB_PATH is not None:
	sys.path.append(TEST_LIB_PATH)

import ldap
import copy
import time
import subprocess
import contextlib
import ldap_glue
import ldap.modlist as modlist
import univention.connector.ad as ad
import univention.testing.utils as utils
import univention.testing.ucr as testing_ucr
import univention.testing.connector_common as tcommon

import univention.admin.modules
import univention.admin.objects

from univention.config_registry import ConfigRegistry
from univention.config_registry import handler_set as ucr_set
baseConfig = ConfigRegistry()
baseConfig.load()


class ADConnection(ldap_glue.LDAPConnection):
	'''helper functions to modify AD-objects'''

	def __init__(self, configbase='connector'):
		self.configbase = configbase
		self.adldapbase = baseConfig['%s/ad/ldap/base' % configbase]
		self.addomain = self.adldapbase.replace(',DC=', '.').replace('DC=', '')
		self.login_dn = baseConfig['%s/ad/ldap/binddn' % configbase]
		self.pw_file = baseConfig['%s/ad/ldap/bindpw' % configbase]
		self.host = baseConfig['%s/ad/ldap/host' % configbase]
		self.port = baseConfig['%s/ad/ldap/port' % configbase]
		self.ca_file = baseConfig['%s/ad/ldap/certificate' % configbase]
		no_starttls = baseConfig.is_false('%s/ad/ldap/ssl' % configbase)
		self.connect(no_starttls)

	def _set_module_default_attr(self, attributes, defaults):
		"""
		Returns the given attributes, extended by every property given in defaults if not yet set.
		"defaults" should be a tupel containing tupels like "('username', <default_value>)".
		"""
		attr = copy.deepcopy(attributes)
		for prop, value in defaults:
			attr.setdefault(prop, value)
		return attr

	def get(self, dn, attr=[], required=False):
		'''returns ldap object'''

		if dn:
			try:
				result = self.lo.search_ext_s(dn, ldap.SCOPE_BASE, '(objectClass=*)', attr, timeout=10)
			except ldap.NO_SUCH_OBJECT:
				result = []
			if result:
				return result[0][1]
		if required:
			raise ldap.NO_SUCH_OBJECT({'desc': 'no object'})
		return {}

	def set_attributes(self, dn, **attributes):
		old_attributes = self.get(dn, attr=attributes.keys())
		ldif = modlist.modifyModlist(old_attributes, attributes)
		self.lo.modify_ext_s(ldap_glue.compatible_modstring(unicode(dn)), ldif)

	def add_to_group(self, group_dn, member_dn):
		self.append_to_attribute(group_dn, 'member', member_dn)

	def remove_from_group(self, group_dn, member_dn):
		self.remove_from_attribute(group_dn, 'member', member_dn)

	def getdn(self, filter):
		for dn, attr in self.lo.search_ext_s(self.adldapbase, ldap.SCOPE_SUBTREE, filter, timeout=10):
			if dn:
				print dn

	def createuser(self, username, position=None, **attributes):
		"""
		Create a AD user with attributes as given by the keyword-args
		`attributes`. The created user will be populated with some defaults if
		not otherwise set.

		Returns the dn of the created user.
		"""
		cn = attributes.get('cn', username)
		sn = attributes.get('sn', 'SomeSurName')

		new_position = position or 'cn=users,%s' % self.adldapbase
		new_dn = 'cn=%s,%s' % (ldap.dn.escape_dn_chars(cn), new_position)

		defaults = (('objectclass', ['top', 'user', 'person', 'organizationalPerson']),
			('cn', cn), ('sn', sn), ('sAMAccountName', username),
			('userPrincipalName', '%s@%s' % (username, self.addomain)),
			('displayName', '%s %s' % (username, sn)))

		new_attributes = self._set_module_default_attr(attributes, defaults)
		self.create(new_dn, new_attributes)
		return new_dn

	def rename_or_move_user_or_group(self, dn, name=None, position=None):
		exploded = ldap.dn.str2dn(dn)
		new_rdn = [("cn", name, ldap.AVA_STRING)] if name else exploded[0]
		new_position = ldap.dn.str2dn(position) if position else exploded[1:]
		new_dn = ldap.dn.dn2str([new_rdn] + new_position)
		self.move(dn, new_dn)
		return new_dn

	def group_create(self, groupname, position=None, **attributes):
		"""
		Create a S4 group with attributes as given by the keyword-args
		`attributes`. The created group will be populated with some defaults if
		not otherwise set.

		Returns the dn of the created group.
		"""
		new_position = position or 'cn=groups,%s' % self.adldapbase
		new_dn = 'cn=%s,%s' % (ldap.dn.escape_dn_chars(groupname), new_position)

		defaults = (('objectclass', ['top', 'group']), ('sAMAccountName', groupname))

		new_attributes = self._set_module_default_attr(attributes, defaults)
		self.create(new_dn, new_attributes)
		return new_dn

	def getprimarygroup(self, user_dn):
		try:
			res = self.lo.search_ext_s(user_dn, ldap.SCOPE_BASE, timeout=10)
		except:
			return None
		primaryGroupID = res[0][1]['primaryGroupID'][0]
		res = self.lo.search_ext_s(
			self.adldapbase,
			ldap.SCOPE_SUBTREE,
			'objectClass=group'.encode('utf8'),
			timeout=10
		)

		import re
		regex = '^(.*?)-%s$' % primaryGroupID
		for r in res:
			if r[0] is None or r[0] == 'None':
				continue  # Referral
			if re.search(regex, ad.decode_sid(r[1]['objectSid'][0])):
				return r[0]

	def setprimarygroup(self, user_dn, group_dn):
		res = self.lo.search_ext_s(group_dn, ldap.SCOPE_BASE, timeout=10)
		import re
		groupid = (re.search('^(.*)-(.*?)$', ad.decode_sid(res[0][1]['objectSid'][0]))).group(2)
		self.set_attribute(user_dn, 'primaryGroupID', groupid)

	def container_create(self, name, position=None, description=None):

		if not position:
			position = self.adldapbase

		attrs = {}
		attrs['objectClass'] = ['top', 'container']
		attrs['cn'] = name
		if description:
			attrs['description'] = description

		container_dn = 'cn=%s,%s' % (ldap.dn.escape_dn_chars(name), position)
		self.create(container_dn, attrs)
		return container_dn

	def createou(self, name, position=None, description=None):

		if not position:
			position = self.adldapbase

		attrs = {}
		attrs['objectClass'] = ['top', 'organizationalUnit']
		attrs['ou'] = name
		if description:
			attrs['description'] = description

		self.create('ou=%s,%s' % (name, position), attrs)

	def verify_object(self, dn, expected_attributes):
		"""
		Verify an object exists with the given `dn` and attributes in the
		AD-LDAP. Setting `expected_attributes` to `None` requires the object to
		not exist. `expected_attributes` is a dictionary of
		`attribute`:`list-of-values`.

		This will throw an `AssertionError` in case of a mismatch.
		"""
		if expected_attributes is None:
			assert not self.exists(dn), "AD object {} should not exist".format(dn)
		else:
			ad_object = self.get(dn)
			for (key, value) in expected_attributes.iteritems():
				ad_value = set(tcommon.to_unicode(x).lower() for x in ad_object.get(key, []))
				expected = set((tcommon.to_unicode(value).lower(),)) if isinstance(value, basestring) \
					else set(tcommon.to_unicode(v).lower() for v in value)
				if not expected.issubset(ad_value):
					try:
						ad_value = set(tcommon.normalize_dn(dn) for dn in ad_value)
						expected = set(tcommon.normalize_dn(dn) for dn in expected)
					except ldap.DECODING_ERROR:
						pass
				error_msg = '{}: {} not in {}, object {}'.format(key, expected, ad_value, ad_object)
				assert expected.issubset(ad_value), error_msg


def connector_running_on_this_host():
	return baseConfig.is_true("connector/ad/autostart")


def restart_adconnector():
	print("Restarting AD-Connector")
	subprocess.check_call(["service", "univention-ad-connector", "restart"])


def ad_in_sync_mode(sync_mode, configbase='connector'):
	"""
	Set the AD-Connector into the given `sync_mode` restart.
	"""
	ucr_set(['{}/ad/mapping/syncmode={}'.format(configbase, sync_mode)])
	restart_adconnector()


def wait_for_sync(min_wait_time=0):
	poll_sleep = baseConfig.get("connector/ad/poll/sleep", 5)
	try:
		sleep_time = int(poll_sleep)
	except ValueError:
		sleep_time = 5
	synctime = max((sleep_time + 3) * 2, min_wait_time)
	print ("Waiting {0} seconds for sync...".format(synctime))
	time.sleep(synctime)


@contextlib.contextmanager
def connector_setup(sync_mode):
	user_syntax = "directory/manager/web/modules/users/user/properties/username/syntax=string"
	group_syntax = "directory/manager/web/modules/groups/group/properties/name/syntax=string"
	with testing_ucr.UCSTestConfigRegistry():
		ucr_set([user_syntax, group_syntax])
		tcommon.restart_univention_cli_server()
		ad_in_sync_mode(sync_mode)
		yield
