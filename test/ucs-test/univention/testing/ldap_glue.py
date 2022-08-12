import os
import sys
import subprocess

import ldap
import ldap.dn
import ldap.modlist as modlist
from ldap.controls import LDAPControl

from univention.config_registry import ConfigRegistry

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
		self.protocol = 'ldap'
		self.kerberos = False
		self.serverctrls_for_add_and_modify = []
		self.connect(no_starttls)

	def connect(self, no_starttls=False):
		self.timeout = 5
		tls_mode = 0 if no_starttls else 2

		login_pw = ""
		if self.pw_file:
			with open(self.pw_file, 'r') as fp:
				login_pw = fp.readline().rstrip('\n')

		try:
			if self.protocol == 'ldapi':
				from six.moves import urllib_parse
				socket = urllib_parse.quote(self.socket, '')
				ldapuri = "%s://%s" % (self.protocol, socket)
			else:
				ldapuri = "%s://%s:%d" % (self.protocol, self.host, int(self.port))

			# lo = univention.uldap.access(host=self.host, port=int(self.port), base=self.adldapbase, binddn=self.login_dn , bindpw=self.pw_file, start_tls=tls_mode, ca_certfile=self.ca_file, uri=ldapuri)
			self.lo = ldap.initialize(ldapuri)
			if self.ca_file:
				self.lo.set_option(ldap.OPT_X_TLS_CACERTFILE, self.ca_file)
				self.lo.set_option(ldap.OPT_X_TLS_NEWCTX, 0)
			if tls_mode > 0:
				self.lo.start_tls_s()
		except Exception:
			ex = 'LDAP Connection to "%s:%s" failed (TLS: %s, Certificate: %s)\n' % (self.host, self.port, not no_starttls, self.ca_file)
			import traceback
			raise Exception(ex + traceback.format_exc())

		self.lo.set_option(ldap.OPT_REFERRALS, 0)

		try:
			if self.kerberos:
				os.environ['KRB5CCNAME'] = '/tmp/ucs-test-ldap-glue.cc'
				self.get_kerberos_ticket()
				auth = ldap.sasl.gssapi("")
				self.lo.sasl_interactive_bind_s("", auth)
			elif login_pw:
				self.lo.simple_bind_s(self.login_dn, login_pw)
		except Exception:
			if self.kerberos:
				cred_msg = '%r with Kerberos password %r' % (self.principal, login_pw)
			else:
				cred_msg = '%r with simplebind password %r' % (self.login_dn, login_pw)
			ex = 'LDAP Bind as %s failed over connection to "%s:%s" (TLS: %s, Certificate: %s)\n' % (cred_msg, self.host, self.port, not no_starttls, self.ca_file)
			import traceback
			raise Exception(ex + traceback.format_exc())

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
		"""Create LDAP object at 'dn' with attributes 'attrs'."""
		# attrs = {key,:[value] if isinstance(value, (str, bytes)) else value for key, value in attrs.items()}
		ldif = modlist.addModlist(attrs)
		print('Creating %r with %r' % (dn, ldif), file=sys.stderr)
		self.lo.add_ext_s(dn, ldif, serverctrls=self.serverctrls_for_add_and_modify)

	def delete(self, dn):
		"""Delete LDAP object at 'dn'."""
		print('Deleting %r' % (dn,), file=sys.stderr)
		self.lo.delete_s(dn)

	def move(self, dn, newdn):
		"""Move LDAP object from 'dn' to 'newdn'."""
		newrdn = get_rdn(newdn)
		parent1 = get_parent_dn(dn)
		parent2 = get_parent_dn(newdn)

		if parent1 != parent2:
			print('Moving %r as %r into %r' % (dn, newdn, parent2), file=sys.stderr)
			self.lo.rename_s(dn, newrdn, parent2)
		else:
			print('Renaming %r to %r' % (dn, newrdn), file=sys.stderr)
			self.lo.modrdn_s(dn, newrdn)

	def set_attribute(self, dn, key, value):
		"""Set attribute 'key' of LDAP object at 'dn' to 'value'."""
		print('Replace %r=%r at %r' % (key, value, dn), file=sys.stderr)
		self.lo.modify_ext_s(dn, [(ldap.MOD_REPLACE, key, value)], serverctrls=self.serverctrls_for_add_and_modify)

	def set_attributes(self, dn, **attributes):
		old_attributes = self.get(dn, attr=attributes.keys())
		attributes = {name: [attr] if not isinstance(attr, (list, tuple)) else attr for name, attr in attributes.items()}
		ldif = modlist.modifyModlist(old_attributes, attributes)
		comp_dn = dn
		if ldif:
			print('Modifying %r: %r' % (comp_dn, ldif), file=sys.stderr)
			self.lo.modify_ext_s(comp_dn, ldif, serverctrls=self.serverctrls_for_add_and_modify)

	def set_attribute_with_provision_ctrl(self, dn, key, value):
		LDB_CONTROL_PROVISION_OID = '1.3.6.1.4.1.7165.4.3.16'
		DSDB_CONTROL_REPLICATED_UPDATE_OID = '1.3.6.1.4.1.7165.4.3.3'
		ctrls = [
			LDAPControl(LDB_CONTROL_PROVISION_OID, criticality=0),
			LDAPControl(DSDB_CONTROL_REPLICATED_UPDATE_OID, criticality=0),
		] + self.serverctrls_for_add_and_modify
		print('Replace %r=%r at %r (with provision control)' % (key, value, dn), file=sys.stderr)
		self.lo.modify_ext_s(dn, [(ldap.MOD_REPLACE, key, value)], serverctrls=ctrls)

	def delete_attribute(self, dn, key):
		"""Delete attribute 'key' of LDAP object at 'dn'."""
		print('Removing %r from %r' % (key, dn), file=sys.stderr)
		self.lo.modify_ext_s(dn, [(ldap.MOD_DELETE, key, None)], serverctrls=self.serverctrls_for_add_and_modify)

	def append_to_attribute(self, dn, key, value):
		"""Add 'value' to attribute 'key' of LDAP object at 'dn'."""
		print('Appending %r=%r to %r' % (key, value, dn), file=sys.stderr)
		self.lo.modify_ext_s(dn, [(ldap.MOD_ADD, key, value)], serverctrls=self.serverctrls_for_add_and_modify)

	def remove_from_attribute(self, dn, key, value):
		"""Remove 'value' from attribute 'key' of LDAP object at 'dn'."""
		print('Removing %r=%r from %r' % (key, value, dn), file=sys.stderr)
		self.lo.modify_ext_s(dn, [(ldap.MOD_DELETE, key, value)], serverctrls=self.serverctrls_for_add_and_modify)


if __name__ == '__main__':
	import doctest
	doctest.testmod()

# vim: set filetype=python ts=4:
