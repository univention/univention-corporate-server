import ldap
import univention.config_registry
from ldap.controls import LDAPControl
import ldap.modlist as modlist
import time
import ldap_glue_s4
import univention.s4connector.s4 as s4

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
			if r[0] == None or r[0] == 'None':
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
