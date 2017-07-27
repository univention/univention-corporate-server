import os
import sys

TEST_LIB_PATH = os.getenv('TESTLIBPATH')
if TEST_LIB_PATH is not None:
	sys.path.append(TEST_LIB_PATH)

import ldap
import copy
import time
import subprocess
import ldap_glue
import ldap.modlist as modlist
import univention.connector.ad as ad
import univention.testing.utils as utils

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
		Returns the given attributes, extented by every property given in defaults if not yet set.
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

	def createuser(self, username, position=None, cn=None, sn=None, description=None):
		if not position:
			position = 'cn=users,%s' % self.adldapbase

		if not cn:
			cn = username

		if not sn:
			sn = 'SomeSurName'

		newdn = 'cn=%s,%s' % (cn, position)

		attrs = {}
		attrs['objectclass'] = ['top', 'user', 'person', 'organizationalPerson']
		attrs['cn'] = cn
		attrs['sn'] = sn
		attrs['sAMAccountName'] = username
		attrs['userPrincipalName'] = '%s@%s' % (username, self.addomain)
		attrs['displayName'] = '%s %s' % (username, sn)
		if description:
			attrs['description'] = description

		self.create(newdn, attrs)

	def group_create(self, groupname, position=None, description=None):
		if not position:
			position = 'cn=groups,%s' % self.adldapbase

		attrs = {}
		attrs['objectclass'] = ['top', 'group']
		attrs['sAMAccountName'] = groupname
		if description:
			attrs['description'] = description

		self.create('cn=%s,%s' % (groupname, position), attrs)

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

		self.create('cn=%s,%s' % (name, position), attrs)

	def createou(self, name, position=None, description=None):

		if not position:
			position = self.adldapbase

		attrs = {}
		attrs['objectClass'] = ['top', 'organizationalUnit']
		attrs['ou'] = name
		if description:
			attrs['description'] = description

		self.create('ou=%s,%s' % (name, position), attrs)

	def resetpassword_in_ad(self, userdn, new_password):
		encoded_new_password = ('"%s"' % new_password).encode("utf-16-le")

		mod_attrs = [(ldap.MOD_REPLACE, 'unicodePwd', encoded_new_password)]
		print 'mod_list: %s' % mod_attrs
		self.lo.modify_s(userdn, mod_attrs)

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
				ad_value = set(to_unicode(x).lower() for x in ad_object.get(key, []))
				expected = set((to_unicode(value).lower(),)) if isinstance(value, basestring) \
					else set(to_unicode(v).lower() for v in value)
				if not expected.issubset(ad_value):
					try:
						ad_value = set(normalize_dn(dn) for dn in ad_value)
						expected = set(normalize_dn(dn) for dn in expected)
					except ldap.DECODING_ERROR:
						pass
				error_msg = '{}: {} not in {}, object {}'.format(key, expected, ad_value, ad_object)
				assert expected.issubset(ad_value), error_msg


def to_unicode(string):
	if isinstance(string, unicode):
		return string
	return unicode(string, 'utf-8')


def normalize_dn(dn):
	"""
	Normalize a given dn. This removes some escaping of special chars in the
	DNs. Note: The S4-LDAP returns DNs with escaping chars, OpenLDAP does not.

	>>> normalize_dn("cn=peter\#,cn=groups")
	'cn=peter#,cn=groups'
	"""
	return ldap.dn.dn2str(ldap.dn.str2dn(dn))


def connector_running_on_this_host():
	return baseConfig.is_true("connector/ad/autostart")


def restart_adconnector():
	print("Restarting AD-Connector")
	subprocess.check_call(["service", "univention-ad-connector", "restart"])


def restart_univention_cli_server():
	print("Restarting Univention-CLI-Server")
	subprocess.call(["pkill", "-f", "univention-cli-server"])


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


def map_udm_user_to_ad(user):
	"""
	Map a UDM user given as a dictionary of `property`:`values` mappings to a
	dictionary of `attributes`:`values` mappings as required by the AD-LDAP.
	Note: This expects the properties from the UDM users/user modul and not
	OpenLDAP-attributes!.
	"""
	mapping = {"username": "sAMAccountName",
		"firstname": "givenName",
		"lastname": "sn",
		"description": "description",
		"street": "streetAddress",
		"city": "l",
		"postcode": "postalCode",
		"profilepath": "profilePath",
		"scriptpath": "scriptPath",
		"homeTelephoneNumber": "homePhone",
		"mobileTelephoneNumber": "mobile",
		"pagerTelephoneNumber": "pager",
		"sambaUserWorkstations": "userWorkstations"}
	return {mapping.get(key): value for (key, value) in user.iteritems()
			if key in mapping}


def map_udm_group_to_ad(group):
	"""
	Map a UDM group given as a dictionary of `property`:`values` mappings to a
	dictionary of `attributes`:`values` mappings as required by the AD-LDAP.
	Note: This expects the properties from the UDM groups/group modul and not
	OpenLDAP-attributes!.
	"""
	mapping = {"name": "sAMAccountName",
		"description": "description"}
	return {mapping.get(key): value for (key, value) in group.iteritems()
			if key in mapping}


def verify_udm_object(module, dn, expected_properties):
	"""
	Verify an object exists with the given `dn` in the given UDM `module` with
	some properties. Setting `expected_properties` to `None` requires the
	object to not exist. `expected_properties` is a dictionary of
	`property`:`value` pairs.

	This will throw an `AssertionError` in case of a mismatch.
	"""
	lo = utils.get_ldap_connection()
	try:
		position = univention.admin.uldap.position(lo.base)
		udm_module = univention.admin.modules.get(module)
		udm_object = univention.admin.objects.get(udm_module, None, lo, position, dn)
		udm_object.open()
	except univention.admin.uexceptions.noObject as e:
		if expected_properties is None:
			return
		raise e

	if expected_properties is None:
		raise AssertionError("UDM object {} should not exist".format(dn))

	for (key, value) in expected_properties.iteritems():
		udm_value = udm_object.info.get(key)
		if isinstance(udm_value, basestring):
			udm_value = set([udm_value])
		if not isinstance(value, (tuple, list)):
			value = set([value])
		value = set(to_unicode(v).lower() for v in value)
		udm_value = set(to_unicode(v).lower() for v in udm_value)
		if udm_value != value:
			try:
				value = set(normalize_dn(dn) for dn in value)
				udm_value = set(normalize_dn(dn) for dn in udm_value)
			except ldap.DECODING_ERROR:
				pass
		assert udm_value == value, '{}: {} != expected {}'.format(key, udm_value, value)
