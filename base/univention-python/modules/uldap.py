# -*- coding: utf-8 -*-
#
# Univention Python
#  LDAP access
#
# Copyright 2002-2017 Univention GmbH
#
# http://www.univention.de/
#
# All rights reserved.
#
# The source code of this program is made available
# under the terms of the GNU Affero General Public License version 3
# (GNU AGPL V3) as published by the Free Software Foundation.
#
# Binary versions of this program provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention and not subject to the GNU AGPL V3.
#
# In the case you use this program under the terms of the GNU AGPL V3,
# the program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <http://www.gnu.org/licenses/>.

import re
import ldap
import ldap.schema
import ldap.sasl
import univention.debug
from univention.config_registry import ConfigRegistry
from ldapurl import LDAPUrl
from ldapurl import isLDAPUrl


def parentDn(dn, base=''):
	_d = univention.debug.function('uldap.parentDn dn=%s base=%s' % (dn, base))
	if dn.lower() == base.lower():
		return
	dn = ldap.dn.str2dn(dn)
	return ldap.dn.dn2str(dn[1:])


def explodeDn(dn, notypes=0):
	return ldap.dn.explode_dn(dn, notypes)


def getRootDnConnection(start_tls=2, decode_ignorelist=[], reconnect=True):
	ucr = ConfigRegistry()
	ucr.load()
	port = int(ucr.get('slapd/port', '7389').split(',')[0])
	host = ucr['hostname'] + '.' + ucr['domainname']
	if ucr.get('ldap/server/type', 'dummy') == 'master':
		bindpw = open('/etc/ldap.secret').read().rstrip('\n')
		binddn = 'cn=admin,{0}'.format(ucr['ldap/base'])
	else:
		bindpw = open('/etc/ldap/rootpw.conf').read().rstrip('\n').lstrip('rootpw "').rstrip('"')
		binddn = 'cn=update,{0}'.format(ucr['ldap/base'])
	return access(host=host, port=port, base=ucr['ldap/base'], binddn=binddn, bindpw=bindpw, start_tls=start_tls, decode_ignorelist=decode_ignorelist, reconnect=reconnect)


def getAdminConnection(start_tls=2, decode_ignorelist=[], reconnect=True):
	ucr = ConfigRegistry()
	ucr.load()
	bindpw = open('/etc/ldap.secret').read().rstrip('\n')
	port = int(ucr.get('ldap/master/port', '7389'))
	return access(host=ucr['ldap/master'], port=port, base=ucr['ldap/base'], binddn='cn=admin,' + ucr['ldap/base'], bindpw=bindpw, start_tls=start_tls, decode_ignorelist=decode_ignorelist, reconnect=reconnect)


def getBackupConnection(start_tls=2, decode_ignorelist=[], reconnect=True):
	ucr = ConfigRegistry()
	ucr.load()
	bindpw = open('/etc/ldap-backup.secret').read().rstrip('\n')
	port = int(ucr.get('ldap/master/port', '7389'))
	try:
		return access(host=ucr['ldap/master'], port=port, base=ucr['ldap/base'], binddn='cn=backup,' + ucr['ldap/base'], bindpw=bindpw, start_tls=start_tls, decode_ignorelist=decode_ignorelist, reconnect=reconnect)
	except ldap.SERVER_DOWN:
		if not ucr['ldap/backup']:
			raise
		backup = ucr['ldap/backup'].split(' ')[0]
		return access(host=backup, port=port, base=ucr['ldap/base'], binddn='cn=backup,' + ucr['ldap/base'], bindpw=bindpw, start_tls=start_tls, decode_ignorelist=decode_ignorelist, reconnect=reconnect)


def getMachineConnection(start_tls=2, decode_ignorelist=[], ldap_master=True, secret_file="/etc/machine.secret", reconnect=True):
	ucr = ConfigRegistry()
	ucr.load()

	bindpw = open(secret_file).read().rstrip('\n')

	if ldap_master:
		# Connect to DC Master
		port = int(ucr.get('ldap/master/port', '7389'))
		return access(host=ucr['ldap/master'], port=port, base=ucr['ldap/base'], binddn=ucr['ldap/hostdn'], bindpw=bindpw, start_tls=start_tls, decode_ignorelist=decode_ignorelist, reconnect=reconnect)
	else:
		# Connect to ldap/server/name
		port = int(ucr.get('ldap/server/port', '7389'))
		try:
			return access(host=ucr['ldap/server/name'], port=port, base=ucr['ldap/base'], binddn=ucr['ldap/hostdn'], bindpw=bindpw, start_tls=start_tls, decode_ignorelist=decode_ignorelist, reconnect=reconnect)
		except ldap.SERVER_DOWN as exc:
			# ldap/server/name is down, try next server
			if not ucr.get('ldap/server/addition'):
				raise
			servers = ucr.get('ldap/server/addition', '')
			for server in servers.split():
				try:
					return access(host=server, port=port, base=ucr['ldap/base'], binddn=ucr['ldap/hostdn'], bindpw=bindpw, start_tls=start_tls, decode_ignorelist=decode_ignorelist, reconnect=reconnect)
				except ldap.SERVER_DOWN:
					pass
			raise exc


class access:

	def __init__(self, host='localhost', port=None, base='', binddn='', bindpw='', start_tls=2, ca_certfile=None, decode_ignorelist=[], use_ldaps=False, uri=None, follow_referral=False, reconnect=True):
		"""start_tls = 0 (no); 1 (try); 2 (must)"""
		self.host = host
		self.base = base
		self.binddn = binddn
		self.bindpw = bindpw
		self.start_tls = start_tls
		self.ca_certfile = ca_certfile
		self.reconnect = reconnect

		self.port = int(port) if port else None

		ucr = ConfigRegistry()
		ucr.load()

		if not self.port:  # if no explicit port is given
			self.port = int(ucr.get('ldap/server/port', 7389))  # take UCR value
			if use_ldaps and self.port == 7389:  # adjust the standard port for ssl
				self.port = 7636

		# http://www.openldap.org/faq/data/cache/605.html
		self.protocol = 'ldap'
		if use_ldaps:
			self.protocol = 'ldaps'
			self.uri = 'ldaps://%s:%d' % (self.host, self.port)
		elif uri:
			self.uri = uri
		else:
			self.uri = "ldap://%s:%d" % (self.host, self.port)

		self.decode_ignorelist = decode_ignorelist or ucr.get('ldap/binaryattributes', 'krb5Key,userCertificate;binary').split(',')

		# python-ldap does not cache the credentials, so we override the
		# referral handling if follow_referral is set to true
		#  https://forge.univention.org/bugzilla/show_bug.cgi?id=9139
		self.follow_referral = follow_referral

		try:
			client_retry_count = int(ucr.get('ldap/client/retry/count', 10))
		except ValueError:
			univention.debug.debug(univention.debug.LDAP, univention.debug.ERROR, "Unable to read ldap/client/retry/count, please reset to an integer value")
			client_retry_count = 10

		self.client_connection_attempt = client_retry_count + 1

		self.__open(ca_certfile)

	def __encode_pwd(self, pwd):
		if isinstance(pwd, unicode):
			return str(pwd)
		else:
			return pwd

	def bind(self, binddn, bindpw):
		"""Do simple LDAP bind using DN and password."""
		self.binddn = binddn
		self.bindpw = bindpw
		univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, 'bind binddn=%s' % self.binddn)
		self.lo.simple_bind_s(self.binddn, self.__encode_pwd(self.bindpw))

	def bind_saml(self, bindpw):
		"""Do LDAP bind using SAML Message"""
		self.binddn = None
		self.bindpw = bindpw
		saml = ldap.sasl.sasl({
			ldap.sasl.CB_AUTHNAME: None,
			ldap.sasl.CB_PASS: bindpw,
		}, 'SAML')
		self.lo.sasl_interactive_bind_s('', saml)
		self.binddn = re.sub('^dn:', '', self.lo.whoami_s())
		univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, 'SAML bind binddn=%s' % self.binddn)

	def unbind(self):
		self.lo.unbind_s()

	def __open(self, ca_certfile):
		_d = univention.debug.function('uldap.__open host=%s port=%d base=%s' % (self.host, self.port, self.base))

		if self.reconnect:
			univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, 'establishing new connection with retry_max=%d' % self. client_connection_attempt)
			self.lo = ldap.ldapobject.ReconnectLDAPObject(self.uri, trace_stack_limit=None, retry_max=self.client_connection_attempt, retry_delay=1)
		else:
			univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, 'establishing new connection')
			self.lo = ldap.initialize(self.uri, trace_stack_limit=None)

		if ca_certfile:
			self.lo.set_option(ldap.OPT_X_TLS_CACERTFILE, ca_certfile)

		if self.protocol.lower() != 'ldaps':
			if self.start_tls == 1:
				try:
					self.lo.start_tls_s()
				except:
					univention.debug.debug(univention.debug.LDAP, univention.debug.WARN, 'Could not start TLS')
			elif self.start_tls == 2:
				self.lo.start_tls_s()

		if self.binddn and not self.uri.startswith('ldapi://'):
			univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, 'bind binddn=%s' % self.binddn)
			self.lo.simple_bind_s(self.binddn, self.__encode_pwd(self.bindpw))

		# Override referral handling
		if self.follow_referral:
			self.lo.set_option(ldap.OPT_REFERRALS, 0)

		self.__schema = None
		self.__reconnects_done = 0

	def __encode(self, value):
		if value is None:
			return value
		elif isinstance(value, unicode):
			return str(value)
		elif isinstance(value, (list, tuple)):
			return map(self.__encode, value)
		else:
			return value

	def __recode_attribute(self, attr, val):
		if attr in self.decode_ignorelist:
			return val
		return self.__encode(val)

	def __recode_entry(self, entry):
		if isinstance(entry, tuple) and len(entry) == 3:
			return (entry[0], entry[1], self.__recode_attribute(entry[1], entry[2]))
		elif isinstance(entry, tuple) and len(entry) == 2:
			return (entry[0], self.__recode_attribute(entry[0], entry[1]))
		elif isinstance(entry, (list, tuple)):
			return map(self.__recode_entry, entry)
		elif isinstance(entry, dict):
			return dict(map(lambda k_v: (k_v[0], self.__recode_attribute(k_v[0], k_v[1])), entry.items()))
		else:
			return entry

	def __encode_entry(self, entry):
		return self.__recode_entry(entry)

	def __encode_attribute(self, attr, val):
		return self.__recode_attribute(attr, val)

	def __decode_entry(self, entry):
		return self.__recode_entry(entry)

	def __decode_attribute(self, attr, val):
		return self.__recode_attribute(attr, val)

	def get(self, dn, attr=[], required=False):
		'''returns ldap object'''

		if dn:
			try:
				result = self.lo.search_s(dn, ldap.SCOPE_BASE, '(objectClass=*)', attr)
			except ldap.NO_SUCH_OBJECT:
				result = []
			if result:
				return self.__decode_entry(result[0][1])
		if required:
			raise ldap.NO_SUCH_OBJECT({'desc': 'no object'})
		return {}

	def getAttr(self, dn, attr, required=False):
		'''return attribute of ldap object'''

		_d = univention.debug.function('uldap.getAttr %s %s' % (dn, attr))
		if dn:
			try:
				result = self.lo.search_s(dn, ldap.SCOPE_BASE, '(objectClass=*)', [attr])
			except ldap.NO_SUCH_OBJECT:
				result = []
			if result and attr in result[0][1]:
				return result[0][1][attr]
		if required:
			raise ldap.NO_SUCH_OBJECT({'desc': 'no object'})
		return []

	def search(self, filter='(objectClass=*)', base='', scope='sub', attr=[], unique=False, required=False, timeout=-1, sizelimit=0, serverctrls=None):
		'''do ldap search'''

		univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, 'uldap.search filter=%s base=%s scope=%s attr=%s unique=%d required=%d timeout=%d sizelimit=%d' % (filter, base, scope, attr, unique, required, timeout, sizelimit))

		if not base:
			base = self.base

		if scope == 'base+one':
			res = self.lo.search_ext_s(base, ldap.SCOPE_BASE, filter, attr, serverctrls=serverctrls, clientctrls=None, timeout=timeout, sizelimit=sizelimit) + \
				self.lo.search_ext_s(base, ldap.SCOPE_ONELEVEL, filter, attr, serverctrls=serverctrls, clientctrls=None, timeout=timeout, sizelimit=sizelimit)
		else:
			if scope == 'sub' or scope == 'domain':
				ldap_scope = ldap.SCOPE_SUBTREE
			elif scope == 'one':
				ldap_scope = ldap.SCOPE_ONELEVEL
			else:
				ldap_scope = ldap.SCOPE_BASE
			res = self.lo.search_ext_s(base, ldap_scope, filter, attr, serverctrls=serverctrls, clientctrls=None, timeout=timeout, sizelimit=sizelimit)

		if unique and len(res) > 1:
			raise ldap.INAPPROPRIATE_MATCHING({'desc': 'more than one object'})
		if required and len(res) < 1:
			raise ldap.NO_SUCH_OBJECT({'desc': 'no object'})
		return res

	def searchDn(self, filter='(objectClass=*)', base='', scope='sub', unique=False, required=False, timeout=-1, sizelimit=0, serverctrls=None):
		_d = univention.debug.function('uldap.searchDn filter=%s base=%s scope=%s unique=%d required=%d' % (filter, base, scope, unique, required))
		return [x[0] for x in self.search(filter, base, scope, ['dn'], unique, required, timeout, sizelimit, serverctrls)]

	def getPolicies(self, dn, policies=None, attrs=None, result=None, fixedattrs=None):
		if attrs is None:
			attrs = {}
		if policies is None:
			policies = []
		_d = univention.debug.function('uldap.getPolicies dn=%s policies=%s attrs=%s' % (
			dn, policies, attrs))
		if not dn and not policies:  # if policies is set apply a fictionally referenced list of policies
			return {}

		# get current dn
		if attrs and 'objectClass' in attrs and 'univentionPolicyReference' in attrs:
			oattrs = attrs
		else:
			oattrs = self.get(dn, ['univentionPolicyReference', 'objectClass'])
		if attrs and 'univentionPolicyReference' in attrs:
			policies = attrs['univentionPolicyReference']
		elif not policies and not attrs:
			policies = oattrs.get('univentionPolicyReference', [])

		object_classes = set(oc.lower() for oc in oattrs.get('objectClass', []))

		result = {}
		if dn:
			obj_dn = dn
			while True:
				for policy_dn in policies:
					self._merge_policy(policy_dn, obj_dn, object_classes, result)
				dn = self.parentDn(dn)
				if not dn:
					break
				try:
					parent = self.get(dn, attr=['univentionPolicyReference'], required=True)
				except ldap.NO_SUCH_OBJECT:
					break
				policies = parent.get('univentionPolicyReference', [])

		univention.debug.debug(
			univention.debug.LDAP, univention.debug.INFO,
			"getPolicies: result: %s" % result)
		return result

	def _merge_policy(self, policy_dn, obj_dn, object_classes, result):
		pattrs = self.get(policy_dn)
		if not pattrs:
			return

		try:
			classes = set(pattrs['objectClass']) - set(('top', 'univentionPolicy', 'univentionObject'))
			ptype = classes.pop()
		except KeyError:
			return

		if pattrs.get('ldapFilter'):
			try:
				self.search(pattrs['ldapFilter'][0], base=obj_dn, scope='base', unique=True, required=True)
			except ldap.NO_SUCH_OBJECT:
				return

		if not all(oc.lower() in object_classes for oc in pattrs.get('requiredObjectClasses', [])):
			return
		if any(oc.lower() in object_classes for oc in pattrs.get('prohibitedObjectClasses', [])):
			return

		fixed = set(pattrs.get('fixedAttributes', ()))
		empty = set(pattrs.get('emptyAttributes', ()))
		values = result.setdefault(ptype, {})
		for key in list(empty) + pattrs.keys() + list(fixed):
			if key in ('requiredObjectClasses', 'prohibitedObjectClasses', 'fixedAttributes', 'emptyAttributes', 'objectClass', 'cn', 'univentionObjectType', 'ldapFilter'):
				continue

			if key not in values or key in fixed:
				value = [] if key in empty else pattrs.get(key, [])
				univention.debug.debug(
					univention.debug.LDAP, univention.debug.INFO,
					"getPolicies: %s sets: %s=%s" % (policy_dn, key, value))
				values[key] = {
					'policy': policy_dn,
					'value': value,
					'fixed': 1 if key in fixed else 0,
				}

	def get_schema(self):
		if self.reconnect and self.lo._reconnects_done > self.__reconnects_done:
			# the schema might differ after reconnecting (e.g. slapd restart)
			self.__schema = None
			self.__reconnects_done = self.lo._reconnects_done
		if not self.__schema:
			self.__schema = ldap.schema.SubSchema(self.lo.read_subschemasubentry_s(self.lo.search_subschemasubentry_s()), 0)
		return self.__schema

	def add(self, dn, al, serverctrls=None, response=None):
		"""Add LDAP entry with dn and attributes in add_list=(attribute-name, old-values. new-values) or (attribute-name, new-values)."""
		if not serverctrls:
			serverctrls = []

		univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, 'uldap.add dn=%s' % dn)
		nal = {}
		for i in al:
			key, val = i[0], i[-1]
			if not val:
				continue
			if isinstance(val, basestring):
				val = [val]
			nal.setdefault(key, set())
			nal[key] |= set(val)

		nal = self.__encode_entry([(k, list(v)) for k, v in nal.items()])

		try:
			rtype, rdata, rmsgid, resp_ctrls = self.lo.add_ext_s(dn, nal, serverctrls=serverctrls)
		except ldap.REFERRAL as exc:
			if not self.follow_referral:
				raise
			lo_ref = self._handle_referral(exc)
			rtype, rdata, rmsgid, resp_ctrls = lo_ref.add_ext_s(dn, nal, serverctrls=serverctrls)

		if serverctrls and isinstance(response, dict):
			response['ctrls'] = resp_ctrls

	def modify(self, dn, changes, serverctrls=None, response=None):
		"""Modify LDAP entry dn with attributes in changes=(attribute-name, old-values, new-values)."""

		univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, 'uldap.modify %s' % dn)

		if not serverctrls:
			serverctrls = []

		ml = []
		for key, oldvalue, newvalue in changes:
			if oldvalue and newvalue:
				if oldvalue == newvalue or (not isinstance(oldvalue, basestring) and not isinstance(newvalue, basestring) and set(oldvalue) == set(newvalue)):
					continue  # equal values
				op = ldap.MOD_REPLACE
				val = newvalue
				if (key == 'krb5ValidEnd' or key == 'krb5PasswordEnd') and newvalue == '0':  # TODO: move into the specific handlers
					val = 0
			elif not oldvalue and newvalue:
				op = ldap.MOD_ADD
				val = newvalue
			elif oldvalue and not newvalue:
				op = ldap.MOD_DELETE
				val = oldvalue
				# These attributes don't have a matching rule:
				#   https://forge.univention.org/bugzilla/show_bug.cgi?id=15171
				#   https://forge.univention.org/bugzilla/show_bug.cgi?id=44019
				if key in ['jpegPhoto', 'univentionPortalBackground', 'univentionPortalLogo', 'univentionPortalEntryIcon', 'univentionUMCIcon']:
					val = None
			else:
				continue
			ml.append((op, key, val))
		ml = self.__encode_entry(ml)

		# check if we need to rename the object
		new_dn, new_rdn = self.__get_new_dn(dn, ml)
		if not self.compare_dn(dn, new_dn):
			univention.debug.debug(univention.debug.LDAP, univention.debug.WARN, 'rename %s' % (new_rdn,))
			self.rename_ext_s(dn, new_rdn, serverctrls=serverctrls, response=response)
			dn = new_dn
		if ml:
			self.modify_ext_s(dn, ml, serverctrls=serverctrls, response=response)

		return dn

	@classmethod
	def __get_new_dn(self, dn, ml):
		"""
		>>> get_dn = access._access__get_new_dn
		>>> get_dn('univentionAppID=foo,dc=bar', [(ldap.MOD_REPLACE, 'univentionAppID', 'foo')])[0]
		'univentionAppID=foo,dc=bar'
		>>> get_dn('univentionAppID=foo,dc=bar', [(ldap.MOD_REPLACE, 'univentionAppID', 'föo')])[0]
		'univentionAppID=f\\xc3\\xb6o,dc=bar'
		>>> get_dn('univentionAppID=foo,dc=bar', [(ldap.MOD_REPLACE, 'univentionAppID', 'bar')])[0]
		'univentionAppID=bar,dc=bar'
		"""
		rdn = ldap.dn.str2dn(dn)[0]
		dn_vals = dict((x[0].lower(), x[1]) for x in rdn)
		new_vals = dict((key.lower(), val if isinstance(val, basestring) else val[0]) for op, key, val in ml if val and op not in (ldap.MOD_DELETE,))
		new_rdn = ldap.dn.dn2str([[(x, new_vals.get(x.lower(), dn_vals[x.lower()]), ldap.AVA_STRING) for x in [y[0] for y in rdn]]])
		rdn = ldap.dn.dn2str([rdn])
		if rdn != new_rdn:
			return ldap.dn.dn2str([ldap.dn.str2dn(new_rdn)[0]] + ldap.dn.str2dn(dn)[1:]), new_rdn
		return dn, rdn

	def modify_s(self, dn, ml):
		"""Redirect modify_s directly to lo"""
		try:
			self.lo.modify_ext_s(dn, ml)
		except ldap.REFERRAL as exc:
			if not self.follow_referral:
				raise
			lo_ref = self._handle_referral(exc)
			lo_ref.modify_ext_s(dn, ml)

	def modify_ext_s(self, dn, ml, serverctrls=None, response=None):
		"""Redirect modify_ext_s directly to lo"""
		if not serverctrls:
			serverctrls = []

		try:
			rtype, rdata, rmsgid, resp_ctrls = self.lo.modify_ext_s(dn, ml, serverctrls=serverctrls)
		except ldap.REFERRAL as exc:
			if not self.follow_referral:
				raise
			lo_ref = self._handle_referral(exc)
			rtype, rdata, rmsgid, resp_ctrls = lo_ref.modify_ext_s(dn, ml, serverctrls=serverctrls)

		if serverctrls and isinstance(response, dict):
			response['ctrls'] = resp_ctrls

	def rename(self, dn, newdn, serverctrls=None, response=None):
		univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, 'uldap.rename %s -> %s' % (dn, newdn))
		oldsdn = self.parentDn(dn)
		newrdn = ldap.dn.dn2str([ldap.dn.str2dn(newdn)[0]])
		newsdn = ldap.dn.dn2str(ldap.dn.str2dn(newdn)[1:])

		if not serverctrls:
			serverctrls = []

		if not newsdn.lower() == oldsdn.lower():
			univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, 'uldap.rename: move %s to %s in %s' % (dn, newrdn, newsdn))
			self.rename_ext_s(dn, newrdn, newsdn, serverctrls=serverctrls, response=response)
		else:
			univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, 'uldap.rename: modrdn %s to %s' % (dn, newrdn))
			self.rename_ext_s(dn, newrdn, serverctrls=serverctrls, response=response)

	def rename_ext_s(self, dn, newrdn, newsuperior=None, serverctrls=None, response=None):
		"""Redirect rename_ext_s directly to lo"""
		if not serverctrls:
			serverctrls = []

		try:
			rtype, rdata, rmsgid, resp_ctrls = self.lo.rename_s(dn, newrdn, newsuperior, serverctrls=serverctrls)
		except ldap.REFERRAL as exc:
			if not self.follow_referral:
				raise
			lo_ref = self._handle_referral(exc)
			rtype, rdata, rmsgid, resp_ctrls = lo_ref.rename_s(dn, newrdn, newsuperior, serverctrls=serverctrls)

		if serverctrls and isinstance(response, dict):
			response['ctrls'] = resp_ctrls

	def delete(self, dn):
		univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, 'uldap.delete %s' % dn)
		if dn:
			univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, 'delete')
			try:
				self.lo.delete_s(dn)
			except ldap.REFERRAL as exc:
				if not self.follow_referral:
					raise
				lo_ref = self._handle_referral(exc)
				lo_ref.delete_s(dn)

	def parentDn(self, dn):
		return parentDn(dn, self.base)

	def explodeDn(self, dn, notypes=False):
		return explodeDn(dn, notypes)

	@classmethod
	def compare_dn(cls, a, b):
		r"""Test DNs are same

		>>> compare_dn = access.compare_dn
		>>> compare_dn('foo=1', 'foo=1')
		True
		>>> compare_dn('foo=1', 'foo=2')
		False
		>>> compare_dn('Foo=1', 'foo=1')
		True
		>>> compare_dn('Foo=1', 'foo=2')
		False
		>>> compare_dn('foo=1,bar=2', 'foo=1,bar=2')
		True
		>>> compare_dn('bar=2,foo=1', 'foo=1,bar=2')
		False
		>>> compare_dn('foo=1+bar=2', 'foo=1+bar=2')
		True
		>>> compare_dn('bar=2+foo=1', 'foo=1+bar=2')
		True
		>>> compare_dn('bar=2+Foo=1', 'foo=1+Bar=2')
		True
		>>> compare_dn(r'foo=\31', r'foo=1')
		True
		"""
		return [sorted((x.lower(), y, z) for x, y, z in rdn) for rdn in ldap.dn.str2dn(a)] == [sorted((x.lower(), y, z) for x, y, z in rdn) for rdn in ldap.dn.str2dn(b)]

	def __getstate__(self):
		_d = univention.debug.function('uldap.__getstate__')
		odict = self.__dict__.copy()
		del odict['lo']
		return odict

	def __setstate__(self, dict):
		_d = univention.debug.function('uldap.__setstate__')
		self.__dict__.update(dict)
		self.__open(self.ca_certfile)

	def _handle_referral(self, exception):
		univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, 'Following LDAP referral')
		exc = exception.args[0]
		info = exc.get('info')
		ldap_url = info[info.find('ldap'):]
		if isLDAPUrl(ldap_url):
			conn_str = LDAPUrl(ldap_url).initializeUrl()

			lo_ref = ldap.ldapobject.ReconnectLDAPObject(conn_str, trace_stack_limit=None)

			if self.ca_certfile:
				lo_ref.set_option(ldap.OPT_X_TLS_CACERTFILE, self.ca_certfile)

			if self.start_tls == 1:
				try:
					lo_ref.start_tls_s()
				except:
					univention.debug.debug(univention.debug.LDAP, univention.debug.WARN, 'Could not start TLS')
			elif self.start_tls == 2:
				lo_ref.start_tls_s()

			lo_ref.simple_bind_s(self.binddn, self.__encode_pwd(self.bindpw))
			return lo_ref

		else:
			raise ldap.CONNECT_ERROR('Bad referral "%s"' % (exc,))


if __name__ == '__main__':
	import doctest
	doctest.testmod()
