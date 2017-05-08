import ldap
import sys
import copy
import subprocess
import ldap_glue_s4
import univention.s4connector.s4 as s4
from time import sleep
import univention.testing.utils as utils
import univention.admin.uldap
import univention.admin.modules
import univention.admin.objects

import univention.config_registry
from univention.config_registry import handler_set as ucr_set

configRegistry = univention.config_registry.ConfigRegistry()
configRegistry.load()


class S4Connection(ldap_glue_s4.LDAPConnection):
	'''helper functions to modify AD-objects'''

	def __init__(self, configbase='connector', no_starttls=False):
		self.configbase = configbase
		self.adldapbase = configRegistry['%s/s4/ldap/base' % configbase]
		self.addomain = self.adldapbase.replace(',DC=', '.').replace('DC=', '')
		self.login_dn = configRegistry['%s/s4/ldap/binddn' % configbase]
		self.pw_file = configRegistry['%s/s4/ldap/bindpw' % configbase]
		self.host = configRegistry['%s/s4/ldap/host' % configbase]
		self.port = configRegistry['%s/s4/ldap/port' % configbase]
		self.ssl = configRegistry.get('%s/s4/ldap/ssl', "no")
		self.ca_file = configRegistry['%s/s4/ldap/certificate' % configbase]
		self.protocol = configRegistry.get('%s/s4/ldap/protocol' % self.configbase, 'ldap').lower()
		self.socket = configRegistry.get('%s/s4/ldap/socket' % self.configbase, '')
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

	def createuser(self, username, position=None, **attributes):
		"""
		Create a S4 user with attributes as given by the keyword-args
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
			'objectClass=group',
			timeout=10
		)

		import re
		regex = '^(.*?)-%s$' % primaryGroupID
		for r in res:
			if r[0] is None or r[0] == 'None':
				continue  # Referral
			if re.search(regex, s4.decode_sid(r[1]['objectSid'][0])):
				return r[0]

	def setprimarygroup(self, user_dn, group_dn):
		res = self.lo.search_ext_s(group_dn, ldap.SCOPE_BASE, timeout=10)
		import re
		groupid = (re.search('^(.*)-(.*?)$', s4.decode_sid(res[0][1]['objectSid'][0]))).group(2)
		self.set_attribute(user_dn, 'primaryGroupID', groupid)

	def container_create(self, name, position=None, description=None):

		if not position:
			position = self.adldapbase

		attrs = {}
		attrs['objectClass'] = ['top', 'container']
		attrs['cn'] = name
		if description:
			attrs['description'] = description

		self.create('cn=%s,%s' % (ldap.dn.escape_dn_chars(name), position), attrs)

	def createou(self, name, position=None, description=None):

		if not position:
			position = self.adldapbase

		attrs = {}
		attrs['objectClass'] = ['top', 'organizationalUnit']
		attrs['ou'] = name
		if description:
			attrs['description'] = description

		self.create('ou=%s,%s' % (ldap.dn.escape_dn_chars(name), position), attrs)

	def verify_object(self, dn, expected_attributes):
		"""
		Verify an object exists with the given `dn` and attributes in the
		S4-LDAP. Setting `expected_attributes` to `None` requires the object to
		not exist. `expected_attributes` is a dictionary of
		`attribute`:`list-of-values`.

		This will throw an `AssertionError` in case of a mismatch.
		"""
		if expected_attributes is None:
			assert not self.exists(dn), "S4 object {} should not exist".format(dn)
		else:
			s4_object = self.get(dn)
			for (key, value) in expected_attributes.iteritems():
				s4_value = set(to_unicode(x).lower() for x in s4_object.get(key, []))
				expected = set((to_unicode(value).lower(),)) if isinstance(value, basestring) \
					else set(to_unicode(v).lower() for v in value)
				if not expected.issubset(s4_value):
					try:
						s4_value = set(normalize_dn(dn) for dn in s4_value)
						expected = set(normalize_dn(dn) for dn in expected)
					except ldap.DECODING_ERROR:
						pass
				error_msg = '{}: {} not in {}, object {}'.format(key, expected, s4_value, s4_object)
				assert expected.issubset(s4_value), error_msg


def check_object(object_dn, sid=None, old_object_dn=None):
	S4 = S4Connection()
	object_dn_modified = _replace_uid_with_cn(object_dn)
	object_found = S4.exists(object_dn_modified)
	if not sid:
		if object_found:
			print ("Object synced to Samba")
		else:
			sys.exit("Object not synced")
	elif sid:
		object_dn_modified_sid = get_object_sid(object_dn)
		old_object_dn_modified = _replace_uid_with_cn(old_object_dn)
		old_object_gone = not S4.exists(old_object_dn_modified)
		if old_object_gone and object_found and object_dn_modified_sid == sid:
			print ("Object synced to Samba")
		else:
			sys.exit("Object not synced")


def normalize_dn(dn):
	"""
	Normalize a given dn. This removes some escaping of special chars in the
	DNs. Note: The S4-LDAP returns DNs with escaping chars, OpenLDAP does not.

	>>> normalize_dn("cn=peter\#,cn=groups")
	'cn=peter#,cn=groups'
	"""
	return ldap.dn.dn2str(ldap.dn.str2dn(dn))


def to_unicode(string):
	if isinstance(string, unicode):
		return string
	return unicode(string, 'utf-8')


def get_object_sid(dn):
	S4 = S4Connection()
	dn_modified = _replace_uid_with_cn(dn)
	sid = S4.get_attribute(dn_modified, 'objectSid')
	return sid


def _replace_uid_with_cn(dn):
	if dn.startswith('uid') or dn.startswith('UID'):
		dn_modified = 'cn' + dn[3:]
	else:
		dn_modified = dn
	return dn_modified


def correct_cleanup(group_dn, groupname2, udm_test_instance, return_new_dn=False):
	modified_group_dn = 'cn=%s,%s' % (ldap.dn.escape_dn_chars(groupname2), ldap.dn.dn2str(ldap.dn.str2dn(group_dn)[1:4]))
	udm_test_instance._cleanup['groups/group'].append(modified_group_dn)
	if return_new_dn:
		return modified_group_dn


def verify_users(group_dn, users):
	print (" Checking Ldap Objects")
	utils.verify_ldap_object(group_dn, {
		'uniqueMember': [user for user in users],
		'memberUid': [ldap.dn.str2dn(user)[0][0][1] for user in users]
	})


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
			value = set([value])
			udm_value = set([udm_value])
		value = set(to_unicode(v).lower() for v in value)
		udm_value = set(to_unicode(v).lower() for v in udm_value)
		if udm_value != value:
			try:
				value = set(normalize_dn(dn) for dn in value)
				udm_value = set(normalize_dn(dn) for dn in udm_value)
			except ldap.DECODING_ERROR:
				pass
		assert udm_value == value, '{}: {} != expected {}'.format(key, udm_value, value)


def modify_username(user_dn, new_user_name, udm_instance):
	newdn = ldap.dn.dn2str([[('uid', new_user_name, ldap.AVA_STRING)]] + ldap.dn.str2dn(user_dn)[1:])
	udm_instance._cleanup['users/user'].append(newdn)
	udm_instance.modify_object('users/user', dn=user_dn, username=new_user_name)
	return newdn


def connector_running_on_this_host():
	return configRegistry.is_true("connector/s4/autostart")


def exit_if_connector_not_running():
	if not connector_running_on_this_host():
		print
		print ("Univention S4 Connector not configured")
		print
		sys.exit(77)


def wait_for_sync(min_wait_time=0):
	synctime = int(configRegistry.get("connector/s4/poll/sleep", 7))
	synctime = ((synctime + 3) * 2)
	if min_wait_time > synctime:
		synctime = min_wait_time
	print ("Waiting {0} seconds for sync...".format(synctime))
	sleep(synctime)


def restart_s4connector():
	print("Restarting S4-Connector")
	subprocess.check_call(["service", "univention-s4-connector", "restart"])


def restart_univention_cli_server():
	print("Restarting Univention-CLI-Server")
	subprocess.call(["pkill", "-f", "univention-cli-server"])


def s4_in_sync_mode(sync_mode, configbase='connector'):
	"""
	Set the S4-Connector into the given `sync_mode` restart.
	"""
	ucr_set(['{}/s4/mapping/syncmode={}'.format(configbase, sync_mode)])
	restart_s4connector()


def map_udm_user_to_s4(user):
	"""
	Map a UDM user given as a dictionary of `property`:`values` mappings to a
	dictionary of `attributes`:`values` mappings as required by the S4-LDAP.
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


def map_udm_group_to_s4(group):
	"""
	Map a UDM group given as a dictionary of `property`:`values` mappings to a
	dictionary of `attributes`:`values` mappings as required by the S4-LDAP.
	Note: This expects the properties from the UDM groups/group modul and not
	OpenLDAP-attributes!.
	"""
	mapping = {"name": "sAMAccountName",
		"description": "description"}
	return {mapping.get(key): value for (key, value) in group.iteritems()
			if key in mapping}
