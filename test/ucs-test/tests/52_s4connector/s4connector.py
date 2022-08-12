import contextlib
import subprocess
import sys
from time import sleep

import ldap
from ldap.controls import LDAPControl

import univention.admin.modules
import univention.admin.objects
import univention.admin.uldap
import univention.config_registry
import univention.s4connector.s4 as s4
import univention.testing.connector_common as tcommon
import univention.testing.ucr as testing_ucr
import univention.testing.utils as utils
from univention.config_registry import handler_set as ucr_set
from univention.testing import ldap_glue

configRegistry = univention.config_registry.ConfigRegistry()
configRegistry.load()


def to_bytes(value):
	if isinstance(value, list):
		return [to_bytes(item) for item in value]
	if not isinstance(value, bytes):
		return value.encode('utf-8')
	return value


def get_first(value):
	if isinstance(value, (list, tuple)):
		return value[0]
	return value


class S4Connection(ldap_glue.LDAPConnection):
	'''helper functions to modify AD-objects'''

	def __init__(self, configbase='connector', no_starttls=False):
		self.configbase = configbase
		self.adldapbase = configRegistry['%s/s4/ldap/base' % configbase]
		self.addomain = self.adldapbase.replace(',DC=', '.').replace('DC=', '')
		self.login_dn = configRegistry['%s/s4/ldap/binddn' % configbase]
		self.pw_file = configRegistry['%s/s4/ldap/bindpw' % configbase]
		self.host = configRegistry['%s/s4/ldap/host' % configbase]
		self.port = configRegistry['%s/s4/ldap/port' % configbase]
		self.ca_file = configRegistry['%s/s4/ldap/certificate' % configbase]
		self.protocol = configRegistry.get('%s/s4/ldap/protocol' % self.configbase, 'ldap').lower()
		self.socket = configRegistry.get('%s/s4/ldap/socket' % self.configbase, '')

		self.serverctrls_for_add_and_modify = []
		if 'univention_samaccountname_ldap_check' in configRegistry.get('samba4/ldb/sam/module/prepend', '').split():
			# The S4 connector must bypass this LDB module if it is activated via samba4/ldb/sam/module/prepend
			# The OID of the 'bypass_samaccountname_ldap_check' control is defined in ldb.h
			ldb_ctrl_bypass_samaccountname_ldap_check = LDAPControl('1.3.6.1.4.1.10176.1004.0.4.1', criticality=0)
			self.serverctrls_for_add_and_modify.append(ldb_ctrl_bypass_samaccountname_ldap_check)

		self.connect(no_starttls)

	def createuser(self, username, position=None, **attributes):
		"""
		Create a S4 user with attributes as given by the keyword-args
		`attributes`. The created user will be populated with some defaults if
		not otherwise set.

		Returns the dn of the created user.
		"""
		cn = to_bytes(attributes.get('cn', username))
		sn = to_bytes(attributes.get('sn', b'SomeSurName'))

		new_position = position or 'cn=users,%s' % self.adldapbase
		new_dn = 'cn=%s,%s' % (ldap.dn.escape_dn_chars(get_first(cn).decode("UTF-8")), new_position)

		defaults = (
			('objectclass', [b'top', b'user', b'person', b'organizationalPerson']),
			('cn', cn),
			('sn', sn),
			('sAMAccountName', to_bytes(username)),
			('userPrincipalName', b'%s@%s' % (to_bytes(username), to_bytes(self.addomain))),
			('displayName', b'%s %s' % (to_bytes(username), get_first(sn))))
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
		Create a S4 group with attributes as given by the keyword-args
		`attributes`. The created group will be populated with some defaults if
		not otherwise set.

		Returns the dn of the created group.
		"""
		new_position = position or 'cn=groups,%s' % self.adldapbase
		new_dn = 'cn=%s,%s' % (ldap.dn.escape_dn_chars(groupname), new_position)

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
			if re.search(regex, s4.decode_sid(r[1]['objectSid'][0])):
				return r[0]

	def setprimarygroup(self, user_dn, group_dn):
		res = self.lo.search_ext_s(group_dn, ldap.SCOPE_BASE, timeout=10)
		import re
		groupid = (re.search('^(.*)-(.*?)$', s4.decode_sid(res[0][1]['objectSid'][0]))).group(2)
		self.set_attribute(user_dn, 'primaryGroupID', groupid.encode('UTF-8'))

	def container_create(self, name, position=None, description=None):

		if not position:
			position = self.adldapbase

		attrs = {}
		attrs['objectClass'] = [b'top', b'container']
		attrs['cn'] = to_bytes(name)
		if description:
			attrs['description'] = to_bytes(description)

		container_dn = 'cn=%s,%s' % (ldap.dn.escape_dn_chars(name), position)
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
			for (key, value) in expected_attributes.items():
				s4_value = set(tcommon.to_unicode(x).lower() for x in s4_object.get(key, []))
				expected = set((tcommon.to_unicode(v).lower() for v in value) if isinstance(value, (list, tuple)) else (tcommon.to_unicode(value).lower(),))
				if not expected.issubset(s4_value):
					try:
						s4_value = set(tcommon.normalize_dn(dn) for dn in s4_value)
						expected = set(tcommon.normalize_dn(dn) for dn in expected)
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
			print("Object synced to Samba")
		else:
			sys.exit("Object not synced")
	elif sid:
		object_dn_modified_sid = get_object_sid(object_dn)
		old_object_dn_modified = _replace_uid_with_cn(old_object_dn)
		old_object_gone = not S4.exists(old_object_dn_modified)
		if old_object_gone and object_found and object_dn_modified_sid == sid:
			print("Object synced to Samba")
		else:
			sys.exit("Object not synced")


def get_object_sid(dn):
	S4 = S4Connection()
	dn_modified = _replace_uid_with_cn(dn)
	sid = S4.get_attribute(dn_modified, 'objectSid')
	return sid


def _replace_uid_with_cn(dn):
	if dn.lower().startswith('uid='):
		dn_modified = 'cn=' + dn[4:]
	else:
		dn_modified = dn
	return dn_modified


def correct_cleanup(group_dn, groupname2, udm_test_instance, return_new_dn=False):
	modified_group_dn = 'cn=%s,%s' % (ldap.dn.escape_dn_chars(groupname2), ldap.dn.dn2str(ldap.dn.str2dn(group_dn)[1:4]))
	udm_test_instance._cleanup['groups/group'].append(modified_group_dn)
	if return_new_dn:
		return modified_group_dn


def verify_users(group_dn, users):
	print(" Checking Ldap Objects")
	utils.verify_ldap_object(group_dn, {
		'uniqueMember': [user for user in users],
		'memberUid': [ldap.dn.str2dn(user)[0][0][1] for user in users]
	})


def modify_username(user_dn, new_user_name, udm_instance):
	newdn = ldap.dn.dn2str([[('uid', new_user_name, ldap.AVA_STRING)]] + ldap.dn.str2dn(user_dn)[1:])
	udm_instance._cleanup['users/user'].append(newdn)
	udm_instance.modify_object('users/user', dn=user_dn, username=new_user_name)
	return newdn


def connector_running_on_this_host():
	return configRegistry.is_true("connector/s4/autostart")


def exit_if_connector_not_running():
	if not connector_running_on_this_host():
		print('')
		print("Univention S4 Connector not configured")
		print('')
		sys.exit(77)


def wait_for_sync(min_wait_time=0):
	synctime = int(configRegistry.get("connector/s4/poll/sleep", 7))
	synctime = ((synctime + 3) * 2)
	if min_wait_time > synctime:
		synctime = min_wait_time
	print("Waiting {0} seconds for sync...".format(synctime))
	sleep(synctime)


def stop():
	print("Stopping S4-Connector")
	subprocess.check_call(["service", "univention-s4-connector", "stop"])


def start():
	print("Starting S4-Connector")
	subprocess.check_call(["service", "univention-s4-connector", "start"])


def restart_s4connector():
	print("Restarting S4-Connector")
	subprocess.check_call(["service", "univention-s4-connector", "restart"])


def s4_in_sync_mode(sync_mode, configbase='connector'):
	"""
	Set the S4-Connector into the given `sync_mode` restart.
	"""
	ucr_set(['{}/s4/mapping/syncmode={}'.format(configbase, sync_mode)])
	restart_s4connector()


@contextlib.contextmanager
def connector_setup(sync_mode):
	user_syntax = "directory/manager/web/modules/users/user/properties/username/syntax=string"
	group_syntax = "directory/manager/web/modules/groups/group/properties/name/syntax=string"
	with testing_ucr.UCSTestConfigRegistry():
		ucr_set([user_syntax, group_syntax])
		tcommon.restart_univention_cli_server()
		s4_in_sync_mode(sync_mode)
		yield S4Connection()
