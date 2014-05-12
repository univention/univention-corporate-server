import ldap
import univention.config_registry
from ldap.controls import LDAPControl
import ldap.modlist as modlist
import time
import ldap_glue_s4
import univention.s4connector.s4 as s4
from time import sleep
import univention.testing.utils as utils

configRegistry = univention.config_registry.ConfigRegistry()
configRegistry.load()

class S4Connection(ldap_glue_s4.LDAPConnection):
	'''helper functions to modify AD-objects'''

	def __init__(self, configbase='connector', no_starttls=False):
		self.configbase = configbase
		self.adldapbase = configRegistry['%s/s4/ldap/base' % configbase]
		self.addomain = self.adldapbase.replace (',DC=', '.').replace ('DC=', '')
		self.login_dn = configRegistry['%s/s4/ldap/binddn' % configbase]
		self.pw_file = configRegistry['%s/s4/ldap/bindpw' % configbase]
		self.host = configRegistry['%s/s4/ldap/host' % configbase]
		self.port = configRegistry['%s/s4/ldap/port' % configbase]
		self.ssl = configRegistry.get('%s/s4/ldap/ssl', "no")
		self.ca_file = configRegistry['%s/s4/ldap/certificate' % configbase]
		self.protocol = configRegistry.get('%s/s4/ldap/protocol' % self.configbase, 'ldap').lower()
		self.socket = configRegistry.get('%s/s4/ldap/socket' % self.configbase, '')
		self.connect (no_starttls)

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
		res = self.lo.search_ext_s(self.adldapbase,
								   ldap.SCOPE_SUBTREE,
								   'objectClass=group'.encode ('utf8'),
								   timeout=10)

		import re
		regex = '^(.*?)-%s$' % primaryGroupID
		for r in res:
			if r[0] is None or r[0] == 'None':
				continue # Referral
			if re.search (regex, s4.decode_sid(r[1]['objectSid'][0])):
				return r[0]

	def setprimarygroup(self, user_dn, group_dn):
		res = self.lo.search_ext_s(group_dn, ldap.SCOPE_BASE, timeout=10)
		import re
		groupid = (re.search ('^(.*)-(.*?)$', s4.decode_sid (res[0][1]['objectSid'][0]))).group (2)
		self.set_attribute (user_dn, 'primaryGroupID', groupid)

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




def check_group(group_dn, old_group_dn = None):
	S4 = S4Connection()
	group_found = S4.exists(group_dn)
	if not old_group_dn:
		if group_found:
			print ("Group synced to Samba")
		else:
			sys.exit("Groupname not synced")
	else:
		old_group_gone = not S4.exists(old_group_dn)
		if group_found and old_group_gone:
			print ("Group synced to Samba")
		else:
			sys.exit("Groupname not synced")


def check_user(user_dn, surname = None, old_user_dn = None):
	S4 = S4Connection()
	user_dn_modified = modify_user_dn(user_dn)
	user_found = S4.exists(user_dn_modified)
	if not surname:
		if user_found:
			print ("User synced to Samba")
		else:
			sys.exit("Username not synced")
	elif surname:
		user_dn_modified_surname = get_user_surname(user_dn)
		old_user_dn_modified = modify_user_dn(old_user_dn)
		old_user_gone = not S4.exists(old_user_dn_modified)
		if old_user_gone and user_found and user_dn_modified_surname == surname:
			print ("User synced to Samba")
		else:
			sys.exit("Username not synced")

def get_user_surname(user_dn):
	S4 = S4Connection()
	user_dn_modified = modify_user_dn(user_dn)
	surname = S4.get_attribute(user_dn_modified,'sn')
	return surname

def modify_user_dn(user_dn):
	user_dn_modified = 'cn' + user_dn[3:]
	return user_dn_modified


def correct_cleanup(group_dn, groupname2, udm_test_instance, return_new_dn = False):
	tmp = group_dn.split(',')
	modified_group_dn = 'cn={0},{1},{2},{3}'.format(groupname2, tmp[1], tmp[2], tmp[3])
	udm_test_instance._cleanup['groups/group'].append(modified_group_dn)
	if return_new_dn:
		return modified_group_dn

def verify_users(group_dn,users):
	print (" Checking Ldap Objects")
	utils.verify_ldap_object(group_dn, {
	'uniqueMember': [user for user in users],
	'memberUid': [(user.split('=')[1]).split(',')[0] for user in users]
	})

def modify_username(user_dn, new_user_name, udm_instance):
	newdn = 'uid=%s,%s' % (new_user_name, user_dn.split(",", 1)[1])
	udm_instance._cleanup['users/user'].append(newdn)
	udm_instance.modify_object('users/user', dn = user_dn, username = new_user_name)
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
	synctime = int(configRegistry.get("connector/s4/poll/sleep",7))
	synctime = ((synctime + 3)*2)
	if min_wait_time > synctime:
		synctime = min_wait_time
	print ("Waiting {0} seconds for sync...".format(synctime))
	sleep (synctime)
