import sys

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


class LDAPConnection:
	'''helper functions to modify LDAP-objects intended as glue for shell-scripts'''

	def __init__(self, no_starttls=False):
		self.ldapbase = ucr['ldap/base']
		self.login_dn = 'cn=admin,%s' % self.ldapbase
		self.pw_file = '/etc/ldap.secret'
		self.host = 'localhost'
		self.port = ucr['ldap/port']
		self.ca_file = None
		self.connect(no_starttls)

	def connect(self, no_starttls=False):
		self.ldapdeleteControl = LDAPControl('1.2.840.113556.1.4.417', criticality=1)

		self.serverctrls_for_add_and_modify = []
		if 'univention_samaccountname_ldap_check' in ucr.get('samba4/ldb/sam/module/prepend', '').split():
			# The S4 connector must bypass this LDB module if it is activated via samba4/ldb/sam/module/prepend
			# The OID of the 'bypass_samaccountname_ldap_check' control is defined in ldb.h
			ldb_ctrl_bypass_samaccountname_ldap_check = LDAPControl('1.3.6.1.4.1.10176.1004.0.4.1', criticality=0)
			self.serverctrls_for_add_and_modify.append(ldb_ctrl_bypass_samaccountname_ldap_check)

		self.timeout = 5
		use_starttls = 2
		if no_starttls:
			use_starttls = 0

		login_pw = ""
		if self.pw_file:
			with open(self.pw_file, 'r') as fp:
				login_pw = fp.readline().rstrip('\n')

		try:
			tls_mode = 2
			if self.ssl == "no" or use_starttls == 0:
				tls_mode = 0

			if self.protocol == 'ldapi':
				from six.moves import urllib_parse
				socket = urllib_parse.quote(self.socket, '')
				ldapuri = "%s://%s" % (self.protocol, socket)
			else:
				ldapuri = "%s://%s:%d" % (self.protocol, self.adldapbase, int(self.port))

			# lo = univention.uldap.access(host=self.host, port=int(self.port), base=self.adldapbase, binddn=self.login_dn , bindpw=self.pw_file, start_tls=tls_mode, ca_certfile=self.ca_file, decode_ignorelist=[
			# 	'objectSid', 'objectGUID', 'repsFrom', 'replUpToDateVector', 'ipsecData', 'logonHours', 'userCertificate', 'dNSProperty', 'dnsRecord', 'member'
			# ], uri=ldapuri)
			self.lo = ldap.initialize(ldapuri)
			if tls_mode > 0:
				self.lo.start_tls_s()
			self.lo.set_option(ldap.OPT_REFERRALS, 0)

		except Exception:
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
		# attrs = dict((key, [value] if isinstance(value, (str, bytes)) else value) for key, value in attrs.items())
		ldif = modlist.addModlist(attrs)
		print('Creating %r with %r' % (dn, ldif), file=sys.stderr)
		self.lo.add_ext_s(dn, ldif, serverctrls=self.serverctrls_for_add_and_modify)

	def delete(self, dn):
		print('Deleting %r' % (dn,), file=sys.stderr)
		self.lo.delete_s(dn)

	def move(self, dn, newdn):
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
		print('Replace %r=%r at %r' % (key, value, dn), file=sys.stderr)
		self.lo.modify_ext_s(dn, [(ldap.MOD_REPLACE, key, value)], serverctrls=self.serverctrls_for_add_and_modify)

	def set_attributes(self, dn, **attributes):
		old_attributes = self.get(dn, attr=attributes.keys())
		attributes = dict((name, [attr] if not isinstance(attr, (list, tuple)) else attr) for name, attr in attributes.items())
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
		print('Removing %r from %r' % (key, dn), file=sys.stderr)
		self.lo.modify_ext_s(dn, [(ldap.MOD_DELETE, key, None)], serverctrls=self.serverctrls_for_add_and_modify)

	def append_to_attribute(self, dn, key, value):
		print('Appending %r=%r to %r' % (key, value, dn), file=sys.stderr)
		self.lo.modify_ext_s(dn, [(ldap.MOD_ADD, key, value)], serverctrls=self.serverctrls_for_add_and_modify)

	def remove_from_attribute(self, dn, key, value):
		print('Removing %r=%r from %r' % (key, value, dn), file=sys.stderr)
		self.lo.modify_ext_s(dn, [(ldap.MOD_DELETE, key, value)], serverctrls=self.serverctrls_for_add_and_modify)


if __name__ == '__main__':
	import doctest
	doctest.testmod()

# vim: set filetype=python ts=4:
