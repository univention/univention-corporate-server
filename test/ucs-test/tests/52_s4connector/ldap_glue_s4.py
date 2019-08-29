import ldap
import ldap.dn
from univention.config_registry import ConfigRegistry
from ldap.controls import LDAPControl
import ldap.modlist as modlist
import univention.s4connector.s4 as s4
import univention.uldap

baseConfig = ConfigRegistry()
baseConfig.load()


def get_rdn(dn):
	r"""
	>>> get_rdn(r'a=b\,c+d=e,f=g+h=i\,j')
	'a=b\\,c+d=e'
	>>> get_rdn(r'a=b')
	'a=b'
	"""
	rdn = ldap.dn.str2dn(dn)[0]
	return ldap.dn.dn2str([rdn])


def get_parent_dn(dn):
	r"""
	>>> get_parent_dn(r'a=b\,c+d=e,f=g+h=i\,j')
	'f=g+h=i\\,j'
	>>> get_parent_dn(r'a=b')
	"""
	parent = ldap.dn.str2dn(dn)[1:]
	return ldap.dn.dn2str(parent) if parent else None


class LDAPConnection:
	'''helper functions to modify LDAP-objects intended as glue for shell-scripts'''

	def __init__(self, no_starttls=False):
		self.ldapbase = baseConfig['ldap/base']
		self.login_dn = 'cn=admin,%s' % self.ldapbase
		self.pw_file = '/etc/ldap.secret'
		self.host = 'localhost'
		self.port = baseConfig['ldap/port']
		self.ca_file = None
		self.connect(no_starttls)

	def connect(self, no_starttls=False):
		self.ldapdeleteControl = LDAPControl('1.2.840.113556.1.4.417', criticality=1)

		self.serverctrls_for_add_and_modify = []
		if 'univention_samaccountname_ldap_check' in baseConfig.get('samba4/ldb/sam/module/prepend', '').split():
			## The S4 connector must bypass this LDB module if it is activated via samba4/ldb/sam/module/prepend
			## The OID of the 'bypass_samaccountname_ldap_check' control is defined in ldb.h
			ldb_ctrl_bypass_samaccountname_ldap_check = LDAPControl('1.3.6.1.4.1.10176.1004.0.4.1', criticality=0)
			self.serverctrls_for_add_and_modify.append(ldb_ctrl_bypass_samaccountname_ldap_check)

		self.timeout = 5
		use_starttls = 2
		if no_starttls:
			use_starttls = 0

		if self.pw_file:
			fp = open(self.pw_file, 'r')
			login_pw = fp.readline()
			if login_pw[-1] == '\n':
				login_pw = login_pw[:-1]
			fp.close()

		try:
			tls_mode = 2
			if self.ssl == "no" or use_starttls == 0:
				tls_mode = 0

			if self.protocol == 'ldapi':
				import urllib
				socket = urllib.quote(self.socket, '')
				ldapuri = "%s://%s" % (self.protocol, socket)
			else:
				ldapuri = "%s://%s:%d" % (self.protocol, self.adldapbase, int(self.port))

			# lo=univention.uldap.access(host=self.host, port=int(self.port), base=self.adldapbase, binddn=self.login_dn , bindpw=self.pw_file, start_tls=tls_mode, ca_certfile=self.ca_file, decode_ignorelist=['objectSid', 'objectGUID', 'repsFrom', 'replUpToDateVector', 'ipsecData', 'logonHours', 'userCertificate', 'dNSProperty', 'dnsRecord', 'member'], uri=ldapuri)
			self.lo = ldap.initialize(ldapuri)
			if tls_mode > 0:
				self.lo.start_tls_s()
			self.lo.set_option(ldap.OPT_REFERRALS, 0)

		except:
			ex = 'LDAP Connection to "%s:%s" as "%s" with password "%s" failed (TLS: %s)\n' % (self.host, self.port, self.login_dn, login_pw, not no_starttls)
			import traceback
			raise Exception(ex + traceback.format_exc())

	def exists(self, dn):
		try:
			self.lo.search_ext_s(dn, ldap.SCOPE_BASE, timeout=10)
			return True
		except ldap.NO_SUCH_OBJECT:
			return False

	def get_attribute(self, dn, attribute):
		res = self.lo.search_ext_s(dn, ldap.SCOPE_BASE, timeout=10)
		try:
			return res[0][1][attribute]
		except LookupError:
			return []

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

	def create(self, dn, attrs):
		ldif = modlist.addModlist(attrs)
		self.lo.add_ext_s(s4.compatible_modstring(unicode(dn)), ldif, serverctrls=self.serverctrls_for_add_and_modify)

	def delete(self, dn):
		self.lo.delete_s(s4.compatible_modstring(unicode(dn)))

	def move(self, dn, newdn):
		newrdn = get_rdn(newdn)
		parent1 = get_parent_dn(dn)
		parent2 = get_parent_dn(newdn)

		if parent1 != parent2:
			self.lo.rename_s(s4.compatible_modstring(unicode(dn)),
				s4.compatible_modstring(unicode(newrdn)),
				s4.compatible_modstring(unicode(parent2)))
		else:
			self.lo.modrdn_s(s4.compatible_modstring(unicode(dn)),
				s4.compatible_modstring(unicode(newrdn)))

	def set_attribute(self, dn, key, value):
		if key not in s4.DECODE_IGNORELIST:
			value = s4.compatible_modstring(unicode(value))
		self.lo.modify_ext_s(s4.compatible_modstring(unicode(dn)),
		[(ldap.MOD_REPLACE, key, value)], serverctrls=self.serverctrls_for_add_and_modify)

	def set_attributes(self, dn, **attributes):
		old_attributes = self.get(dn, attr=attributes.keys())
		ldif = modlist.modifyModlist(old_attributes, attributes)
		comp_dn = s4.compatible_modstring(unicode(dn))
		self.lo.modify_ext_s(comp_dn, ldif, serverctrls=self.serverctrls_for_add_and_modify)

	def set_attribute_with_provision_ctrl(self, dn, key, value):
		LDB_CONTROL_PROVISION_OID = '1.3.6.1.4.1.7165.4.3.16'
		DSDB_CONTROL_REPLICATED_UPDATE_OID = '1.3.6.1.4.1.7165.4.3.3'
		ctrls = [
			LDAPControl(LDB_CONTROL_PROVISION_OID, criticality=0),
			LDAPControl(DSDB_CONTROL_REPLICATED_UPDATE_OID, criticality=0),
		] + self.serverctrls_for_add_and_modify
		self.lo.modify_ext_s(s4.compatible_modstring(unicode(dn)),
			[(ldap.MOD_REPLACE, key, value)], serverctrls=ctrls)

	def delete_attribute(self, dn, key):
		self.lo.modify_ext_s(s4.compatible_modstring(unicode(dn)),
			[(ldap.MOD_DELETE, key, None)], serverctrls=self.serverctrls_for_add_and_modify)

	def append_to_attribute(self, dn, key, value):
		self.lo.modify_ext_s(s4.compatible_modstring(unicode(dn)),
			[(ldap.MOD_ADD, key, s4.compatible_modstring(unicode(value)))], serverctrls=self.serverctrls_for_add_and_modify)

	def remove_from_attribute(self, dn, key, value):
		self.lo.modify_ext_s(s4.compatible_modstring(unicode(dn)),
			[(ldap.MOD_DELETE, key, s4.compatible_modstring(unicode(value)))], serverctrls=self.serverctrls_for_add_and_modify)


if __name__ == '__main__':
	import doctest
	doctest.testmod()

# vim: set filetype=python ts=4:
