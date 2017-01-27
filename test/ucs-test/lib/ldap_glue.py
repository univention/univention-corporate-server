import ldap
import ldap.dn
from univention.config_registry import ConfigRegistry
from ldap.controls import LDAPControl
import ldap.modlist as modlist
try:
	from univention.connector.ad import compatible_modstring
except ImportError:
	try:
		from univention.s4connector.s4 import compatible_modstring
	except ImportError:
		def compatible_modstring(dn):
			return dn

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


class LDAPConnection(object):

	'''helper functions to modify LDAP-objects intended as glue for shell-scripts'''

	def __init__(self, no_starttls=False):
		self.ldapbase = baseConfig['ldap/base']
		self.login_dn = 'cn=admin,%s' % self.ldapbase
		self.pw_file = '/etc/ldap.secret'
		self.host = 'localhost'
		self.port = baseConfig.get('ldap/server/port', 389)
		self.ca_file = None
		self.connect(no_starttls)

	def connect(self, no_starttls=False):
		self.ldapdeleteControl = LDAPControl('1.2.840.113556.1.4.417', criticality=1)
		self.timeout = 5
		use_starttls = 2
		if no_starttls:
			use_starttls = 0

		fp = open(self.pw_file, 'r')
		login_pw = fp.readline()
		if login_pw[-1] == '\n':
			login_pw = login_pw[:-1]
		fp.close()

		try:
			self.lo = ldap.initialize(uri="ldap://%s:%s" % (self.host, self.port))
			if self.ca_file:
				ldap.set_option(ldap.OPT_X_TLS_CACERTFILE, self.ca_file)
			if use_starttls:
				self.lo.start_tls_s()
			self.lo.simple_bind_s(self.login_dn, login_pw)

		except:
			ex = 'LDAP Connection to "%s:%s" as "%s" with password "%s" failed (TLS: %s, Certificate: %s)\n' % (self.host, self.port, self.login_dn, login_pw, not no_starttls, self.ca_file)
			import traceback
			raise Exception(ex + traceback.format_exc())

		self.lo.set_option(ldap.OPT_REFERRALS, 0)

	def exists(self, dn):
		try:
			self.lo.search_ext_s(dn, ldap.SCOPE_BASE, timeout=10)
			return True
		except ldap.NO_SUCH_OBJECT:
			return False

	def get_attribute(self, dn, attribute):
		"""Get attributes 'key' of LDAP object at 'dn'."""
		res = self.lo.search_ext_s(dn, ldap.SCOPE_BASE, timeout=10)
		try:
			first = res[0]
			_dn, key_values = first
			return key_values[attribute]
		except (IndexError, TypeError, KeyError):
			return []

	def create(self, dn, attrs):
		"""Create LDAP object at 'dn' with attributes 'attrs'."""
		ldif = modlist.addModlist(attrs)
		self.lo.add_s(compatible_modstring(unicode(dn)), ldif)

	def delete(self, dn):
		"""Delete LDAP object at 'dn'."""
		self.lo.delete_s(compatible_modstring(unicode(dn)))

	def move(self, dn, newdn):
		"""Move LDAP object from 'dn' to 'newdn'."""
		newrdn = get_rdn(newdn)
		parent1 = get_parent_dn(dn)
		parent2 = get_parent_dn(newdn)

		if parent1 != parent2:
			self.lo.rename_s(compatible_modstring(unicode(dn)),
				compatible_modstring(unicode(newrdn)),
				compatible_modstring(unicode(parent2)))
		else:
			self.lo.modrdn_s(compatible_modstring(unicode(dn)),
				compatible_modstring(unicode(newrdn)))

	def set_attribute(self, dn, key, value):
		"""Set attribute 'key' of LDAP object at 'dn' to 'value'."""
		ml = [(ldap.MOD_REPLACE, key, compatible_modstring(unicode(value)))]
		self.lo.modify_s(compatible_modstring(unicode(dn)), ml)

	def delete_attribute(self, dn, key):
		"""Delete attribute 'key' of LDAP object at 'dn'."""
		ml = [(ldap.MOD_DELETE, key, None)]
		self.lo.modify_s(compatible_modstring(unicode(dn)), ml)

	def append_to_attribute(self, dn, key, value):
		"""Add 'value' to attribute 'key' of LDAP object at 'dn'."""
		ml = [(ldap.MOD_ADD, key, compatible_modstring(unicode(value)))]
		self.lo.modify_s(compatible_modstring(unicode(dn)), ml)

	def remove_from_attribute(self, dn, key, value):
		"""Remove 'value' from attribute 'key' of LDAP object at 'dn'."""
		ml = [(ldap.MOD_DELETE, key, compatible_modstring(unicode(value)))]
		self.lo.modify_s(compatible_modstring(unicode(dn)), ml)


if __name__ == '__main__':
	import doctest
	doctest.testmod()

# vim: set filetype=python ts=4:
