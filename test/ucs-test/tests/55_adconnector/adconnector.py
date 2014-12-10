import ldap
from univention.config_registry import ConfigRegistry
from ldap.controls import LDAPControl
import ldap.modlist as modlist
import time
import ldap_glue
import univention.connector.ad as ad

baseConfig = ConfigRegistry()
baseConfig.load()

class ADConnection(ldap_glue.LDAPConnection):
	'''helper functions to modify AD-objects'''

	def __init__(self, configbase='connector'):
		self.configbase = configbase
		self.adldapbase = baseConfig['%s/ad/ldap/base' % configbase]
		self.addomain = self.adldapbase.replace (',DC=', '.').replace ('DC=', '')
		self.login_dn = baseConfig['%s/ad/ldap/binddn' % configbase]
		self.pw_file = baseConfig['%s/ad/ldap/bindpw' % configbase]
		self.host = baseConfig['%s/ad/ldap/host' % configbase]
		self.port = baseConfig['%s/ad/ldap/port' % configbase]
		self.ca_file = baseConfig['%s/ad/ldap/certificate' % configbase]
		no_starttls = baseConfig.is_false('%s/ad/ldap/ssl' % configbase)
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
			if re.search (regex, ad.decode_sid(r[1]['objectSid'][0])):
				return r[0]

	def setprimarygroup(self, user_dn, group_dn):
		res = self.lo.search_ext_s(group_dn, ldap.SCOPE_BASE, timeout=10)
		import re
		groupid = (re.search ('^(.*)-(.*?)$', ad.decode_sid (res[0][1]['objectSid'][0]))).group (2)
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
