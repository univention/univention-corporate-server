import contextlib
import os
import subprocess
import sys
from time import sleep

import ldap
from ldap import modlist

import univention.admin.modules
import univention.admin.objects
import univention.admin.uldap
import univention.config_registry
import univention.connector.ad as ad
import univention.testing.connector_common as tcommon
import univention.testing.ucr as testing_ucr
from univention.config_registry import handler_set as ucr_set

configRegistry = univention.config_registry.ConfigRegistry()
configRegistry.load()


TEST_LIB_PATH = os.getenv('TESTLIBPATH', '/usr/share/ucs-test/lib/')
if TEST_LIB_PATH is not None:
	sys.path.append(TEST_LIB_PATH)

import ldap_glue  # noqa: E402


def to_bytes(value):
	if isinstance(value, list):
		return [to_bytes(item) for item in value]
	if not isinstance(value, bytes):
		return value.encode('utf-8')
	return value


class ADConnection(ldap_glue.LDAPConnection):
	'''helper functions to modify AD-objects'''

	def __init__(self, configbase='connector'):
		self.configbase = configbase
		self.adldapbase = configRegistry['%s/ad/ldap/base' % configbase]
		self.addomain = self.adldapbase.replace(',DC=', '.').replace('DC=', '')
		self.kerberos = configRegistry.is_true('%s/ad/ldap/kerberos' % configbase)
		if self.kerberos:  # i.e. if UCR ad/member=true
			# Note: tests/domainadmin/account is an OpenLDAP DN but
			#       we only extract the username from it in ldap_glue
			self.login_dn = configRegistry['tests/domainadmin/account']
			self.principal = ldap.dn.str2dn(self.login_dn)[0][0][1]
			self.pw_file = configRegistry['tests/domainadmin/pwdfile']
		else:
			self.login_dn = configRegistry['%s/ad/ldap/binddn' % configbase]
			self.pw_file = configRegistry['%s/ad/ldap/bindpw' % configbase]
		self.host = configRegistry['%s/ad/ldap/host' % configbase]
		self.port = configRegistry['%s/ad/ldap/port' % configbase]
		self.ca_file = configRegistry['%s/ad/ldap/certificate' % configbase]
		no_starttls = configRegistry.is_false('%s/ad/ldap/ssl' % configbase)
		self.connect(no_starttls)

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
		if ldif:
			self.lo.modify_ext_s(dn, ldif)

	def add_to_group(self, group_dn, member_dn):
		self.append_to_attribute(group_dn, 'member', member_dn)

	def remove_from_group(self, group_dn, member_dn):
		self.remove_from_attribute(group_dn, 'member', member_dn)

	def getdn(self, filter):
		for dn, attr in self.lo.search_ext_s(self.adldapbase, ldap.SCOPE_SUBTREE, filter, timeout=10):
			if dn:
				print(dn)

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
		new_dn = 'cn=%s,%s' % (ldap.dn.escape_dn_chars(tcommon.to_unicode(cn)), new_position)

		defaults = (
			('objectclass', [b'top', b'user', b'person', b'organizationalPerson']),
			('cn', to_bytes(cn)),
			('sn', to_bytes(sn)),
			('sAMAccountName', to_bytes(username)),
			('userPrincipalName', to_bytes('%s@%s' % (tcommon.to_unicode(username), tcommon.to_unicode(self.addomain)))),
			('displayName', to_bytes('%s %s' % (tcommon.to_unicode(username), tcommon.to_unicode(sn))))
		)
		new_attributes = dict(defaults)
		new_attributes.update(attributes)
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
		Create a AD group with attributes as given by the keyword-args
		`attributes`. The created group will be populated with some defaults if
		not otherwise set.

		Returns the dn of the created group.
		"""
		new_position = position or 'cn=groups,%s' % self.adldapbase
		new_dn = 'cn=%s,%s' % (ldap.dn.escape_dn_chars(tcommon.to_unicode(groupname)), new_position)

		defaults = (('objectclass', [b'top', b'group']), ('sAMAccountName', to_bytes(groupname)))
		new_attributes = dict(defaults)
		new_attributes.update(attributes)
		self.create(new_dn, new_attributes)
		return new_dn

	def getprimarygroup(self, user_dn):
		try:
			res = self.lo.search_ext_s(user_dn, ldap.SCOPE_BASE, timeout=10)
		except Exception:
			return None
		primaryGroupID = res[0][1]['primaryGroupID'][0].decode('UTF-8')
		res = self.lo.search_ext_s(
			self.adldapbase,
			ldap.SCOPE_SUBTREE,
			'objectClass=group',
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
		self.set_attribute(user_dn, 'primaryGroupID', groupid.encode('UTF-8'))

	def container_create(self, name, position=None, description=None):

		if not position:
			position = self.adldapbase

		attrs = {}
		attrs['objectClass'] = [b'top', b'container']
		attrs['cn'] = to_bytes(name)
		if description:
			attrs['description'] = to_bytes(description)

		container_dn = 'cn=%s,%s' % (ldap.dn.escape_dn_chars(tcommon.to_unicode(name)), position)
		self.create(container_dn, attrs)
		return container_dn

	def createou(self, name, position=None, description=None):

		if not position:
			position = self.adldapbase

		attrs = {}
		attrs['objectClass'] = [b'top', b'organizationalUnit']
		attrs['ou'] = to_bytes(name)
		if description:
			attrs['description'] = to_bytes(description)

		self.create('ou=%s,%s' % (ldap.dn.escape_dn_chars(tcommon.to_unicode(name)), position), attrs)

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
			for (key, value) in expected_attributes.items():
				ad_value = set(tcommon.to_unicode(x).lower() for x in ad_object.get(key, []))
				expected = set((tcommon.to_unicode(v).lower() for v in value) if isinstance(value, (list, tuple)) else (tcommon.to_unicode(value).lower(),))
				if not expected.issubset(ad_value):
					try:
						ad_value = set(tcommon.normalize_dn(dn) for dn in ad_value)
						expected = set(tcommon.normalize_dn(dn) for dn in expected)
					except ldap.DECODING_ERROR:
						pass
				error_msg = '{}: {} not in {}, object {}'.format(key, expected, ad_value, ad_object)
				assert expected.issubset(ad_value), error_msg


def connector_running_on_this_host():
	return configRegistry.is_true("connector/ad/autostart")


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
	synctime = int(configRegistry.get("connector/ad/poll/sleep", 5))
	synctime = ((synctime + 3) * 2)
	if min_wait_time > synctime:
		synctime = min_wait_time
	print("Waiting {0} seconds for sync...".format(synctime))
	sleep(synctime)


@contextlib.contextmanager
def connector_setup(sync_mode):
	user_syntax = "directory/manager/web/modules/users/user/properties/username/syntax=string"
	group_syntax = "directory/manager/web/modules/groups/group/properties/name/syntax=string"
	with testing_ucr.UCSTestConfigRegistry():
		ucr_set([user_syntax, group_syntax])
		tcommon.restart_univention_cli_server()
		ad_in_sync_mode(sync_mode)
		yield
