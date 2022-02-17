import os
import subprocess

import ldap
import ldap.dn
from univention.config_registry import ConfigRegistry
from ldap.controls import LDAPControl
import ldap.modlist as modlist

ucr = ConfigRegistry()
ucr.load()


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
		self.ldapbase = ucr['ldap/base']
		self.login_dn = 'cn=admin,%s' % self.ldapbase
		self.pw_file = '/etc/ldap.secret'
		self.host = 'localhost'
		self.port = ucr.get('ldap/server/port', 389)
		self.ca_file = None
		self.kerberos = False
		self.connect(no_starttls)

	def connect(self, no_starttls=False):
		self.ldapdeleteControl = LDAPControl('1.2.840.113556.1.4.417', criticality=1)
		self.timeout = 5
		use_starttls = 2
		if no_starttls:
			use_starttls = 0

		login_pw = ""
		if self.pw_file:
			with open(self.pw_file, 'r') as fp:
				login_pw = fp.readline().rstrip('\n')

		try:
			self.lo = ldap.initialize(uri="ldap://%s:%s" % (self.host, self.port))
			if self.ca_file:
				ldap.set_option(ldap.OPT_X_TLS_CACERTFILE, self.ca_file)
				ldap.set_option(ldap.OPT_X_TLS_NEWCTX, 0)
			if use_starttls:
				self.lo.start_tls_s()
		except Exception:
			ex = 'LDAP Connection to "%s:%s" failed (TLS: %s, Certificate: %s)\n' % (self.host, self.port, not no_starttls, self.ca_file)
			import traceback
			raise Exception(ex + traceback.format_exc())

		try:
			if self.kerberos:
				os.environ['KRB5CCNAME'] = '/tmp/ucs-test-ldap-glue.cc'
				self.get_kerberos_ticket()
				auth = ldap.sasl.gssapi("")
				self.lo.sasl_interactive_bind_s("", auth)
			else:
				self.lo.simple_bind_s(self.login_dn, login_pw)
		except Exception:
			if self.kerberos:
				cred_msg = '"%s" with Kerberos password "%s"' % (self.principal, login_pw)
			else:
				cred_msg = '"%s" with simplebind password "%s"' % (self.login_dn, login_pw)
			ex = 'LDAP Bind as %s failed over connection to "%s:%s" (TLS: %s, Certificate: %s)\n' % (cred_msg, self.host, self.port, not no_starttls, self.ca_file)
			import traceback
			raise Exception(ex + traceback.format_exc())

		self.lo.set_option(ldap.OPT_REFERRALS, 0)

	def get_kerberos_ticket(self):
		p1 = subprocess.Popen(['kdestroy', ], close_fds=True)
		p1.wait()
		cmd_block = ['kinit', '--no-addresses', '--password-file=%s' % self.pw_file, self.principal]
		p1 = subprocess.Popen(cmd_block, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=True)
		stdout, stderr = p1.communicate()
		if p1.returncode != 0:
			raise Exception('The following command failed: "%s" (%s): %s' % (''.join(cmd_block), p1.returncode, stdout.decode('UTF-8')))

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
			return res[0][1][attribute]
		except LookupError:
			return []

	def create(self, dn, attrs):
		"""Create LDAP object at 'dn' with attributes 'attrs'."""
		ldif = modlist.addModlist(attrs)
		self.lo.add_ext_s(dn, ldif)

	def delete(self, dn):
		"""Delete LDAP object at 'dn'."""
		self.lo.delete_s(dn)

	def move(self, dn, newdn):
		"""Move LDAP object from 'dn' to 'newdn'."""
		newrdn = get_rdn(newdn)
		parent1 = get_parent_dn(dn)
		parent2 = get_parent_dn(newdn)

		if parent1 != parent2:
			self.lo.rename_s(dn, newrdn, parent2)
		else:
			self.lo.modrdn_s(dn, newrdn)

	def set_attribute(self, dn, key, value):
		"""Set attribute 'key' of LDAP object at 'dn' to 'value'."""
		ml = [(ldap.MOD_REPLACE, key, value)]
		self.lo.modify_s(dn, ml)

	def delete_attribute(self, dn, key):
		"""Delete attribute 'key' of LDAP object at 'dn'."""
		ml = [(ldap.MOD_DELETE, key, None)]
		self.lo.modify_s(dn, ml)

	def append_to_attribute(self, dn, key, value):
		"""Add 'value' to attribute 'key' of LDAP object at 'dn'."""
		ml = [(ldap.MOD_ADD, key, value)]
		self.lo.modify_s(dn, ml)

	def remove_from_attribute(self, dn, key, value):
		"""Remove 'value' from attribute 'key' of LDAP object at 'dn'."""
		ml = [(ldap.MOD_DELETE, key, value)]
		self.lo.modify_s(dn, ml)


if __name__ == '__main__':
	import doctest
	doctest.testmod()

# vim: set filetype=python ts=4:
