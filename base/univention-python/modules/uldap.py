# -*- coding: utf-8 -*-
#
# Univention Python
#  LDAP access
#
# Copyright 2002-2014 Univention GmbH
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

import ldap
import ldap.schema
import univention.debug
from univention.config_registry import ConfigRegistry
from ldapurl import LDAPUrl
from ldapurl import isLDAPUrl

def _extend_uniq(list1, list2):
	for item in list2:
		if item not in list1:
			list1.append(item)

def parentDn(dn, base=''):
	_d=univention.debug.function('uldap.parentDn dn=%s base=%s' % (dn, base))
	if dn == base:
		return None
	pos=dn.find(',')+1
	if pos == 0:
		return None
	return dn[pos:]

def explodeDn(dn, notypes=0):
	if not dn:
		return []

	exploded_dn=dn.split(',')
	if notypes:
		return map(lambda(x): x[x.find('=')+1:], exploded_dn)
	return exploded_dn

def getAdminConnection(start_tls=2, decode_ignorelist=[], reconnect=True):
	ucr = ConfigRegistry()
	ucr.load()
	bindpw=open('/etc/ldap.secret').read()
	if bindpw[-1] == '\n':
		bindpw=bindpw[0:-1]
	port = int(ucr.get('ldap/master/port', '7389'))
	lo=access(host=ucr['ldap/master'], port=port, base=ucr['ldap/base'], binddn='cn=admin,'+ucr['ldap/base'], bindpw=bindpw, start_tls=start_tls, decode_ignorelist=decode_ignorelist, reconnect=reconnect)
	return lo

def getBackupConnection(start_tls=2, decode_ignorelist=[], reconnect=True):
	ucr = ConfigRegistry()
	ucr.load()
	bindpw=open('/etc/ldap-backup.secret').read()
	if bindpw[-1] == '\n':
		bindpw=bindpw[0:-1]
	port = int(ucr.get('ldap/master/port', '7389'))
	try:
		lo=access(host=ucr['ldap/master'], port=port, base=ucr['ldap/base'], binddn='cn=backup,'+ucr['ldap/base'], bindpw=bindpw, start_tls=start_tls, decode_ignorelist=decode_ignorelist, reconnect=reconnect)
	except ldap.SERVER_DOWN, e:
		if ucr['ldap/backup']:
			backup=ucr['ldap/backup'].split(' ')[0]
			lo=access(host=backup, port=port, base=ucr['ldap/base'], binddn='cn=backup,'+ucr['ldap/base'], bindpw=bindpw, start_tls=start_tls, decode_ignorelist=decode_ignorelist, reconnect=reconnect)
		else:
			raise ldap.SERVER_DOWN, e
	return lo

def getMachineConnection(start_tls=2, decode_ignorelist=[], ldap_master = True, secret_file = "/etc/machine.secret", reconnect=True):
	ucr = ConfigRegistry()
	ucr.load()

	bindpw=open(secret_file).read()
	if bindpw[-1] == '\n':
		bindpw=bindpw[0:-1]

	if ldap_master:
		# Connect to DC Master
		port = int(ucr.get('ldap/master/port', '7389'))
		lo=access(host=ucr['ldap/master'], port=port, base=ucr['ldap/base'], binddn=ucr['ldap/hostdn'], bindpw=bindpw, start_tls=start_tls, decode_ignorelist=decode_ignorelist, reconnect=reconnect)
	else:
		# Connect to ldap/server/name
		port = int(ucr.get('ldap/server/port', '7389'))
		try:
			lo=access(host=ucr['ldap/server/name'], port=port, base=ucr['ldap/base'], binddn=ucr['ldap/hostdn'], bindpw=bindpw, start_tls=start_tls, decode_ignorelist=decode_ignorelist, reconnect=reconnect)
		except ldap.SERVER_DOWN, e:
			# ldap/server/name is down, try next server
			if not ucr.get('ldap/server/addition'):
				raise ldap.SERVER_DOWN, e
			servers = ucr.get('ldap/server/addition', '')
			for server in servers.split():
				try:
					lo=access(host=server, port=port, base=ucr['ldap/base'], binddn=ucr['ldap/hostdn'], bindpw=bindpw, start_tls=start_tls, decode_ignorelist=decode_ignorelist, reconnect=reconnect)
				except ldap.SERVER_DOWN, e:
					pass
				else:
					return lo
			raise ldap.SERVER_DOWN, e

	return lo

class access:

	def __init__(self, host='localhost', port=None, base='', binddn='', bindpw='', start_tls=2, ca_certfile=None, decode_ignorelist=[], use_ldaps=False, uri=None, follow_referral=False, reconnect=True):
		"""start_tls = 0 (no); 1 (try); 2 (must)"""
		ucr = None
		self.host = host
		self.base = base
		self.binddn = binddn
		self.bindpw = bindpw
		self.start_tls = start_tls
		self.ca_certfile = ca_certfile
		self.reconnect = reconnect

		self.port = port

		ucr = ConfigRegistry()
		ucr.load()

		if not self.port:	## if no explicit port is given
			self.port = int(ucr.get('ldap/server/port', 7389))	## take UCR value
			if use_ldaps and self.port == "7389":				## adjust the standard port for ssl
					self.port = "7636"

		# http://www.openldap.org/faq/data/cache/605.html
		self.protocol = 'ldap'
		if use_ldaps:
			self.protocol = 'ldaps'
			self.uri = 'ldaps://%s:%s" % (self.host, self.port)'
		elif uri:
			self.uri = uri
		else:
			self.uri = "ldap://%s:%s" % (self.host, self.port)

		if not decode_ignorelist or decode_ignorelist == []:
			if not ucr:
				ucr = ConfigRegistry()
				ucr.load()
			self.decode_ignorelist = ucr.get('ldap/binaryattributes', 'krb5Key,userCertificate;binary').split(',')
		else:
			self.decode_ignorelist = decode_ignorelist

		# python-ldap does not cache the credentials, so we override the
		# referral handling if follow_referral is set to true
		#  https://forge.univention.org/bugzilla/show_bug.cgi?id=9139
		self.follow_referral = follow_referral

		try:
			client_retry_count = int(ucr.get('ldap/client/retry/count', 10))
		except ValueError:
			univention.debug.debug(univention.debug.LDAP, univention.debug.ERROR, "Unable to read ldap/client/retry/count, please reset to an integer value")
			client_retry_count = 10

		self.client_connection_attempt = client_retry_count+1

		self.__open(ca_certfile)

	def __encode_pwd(self, pwd):
		if isinstance( pwd, unicode ):
			return str( pwd )
		else:
			return pwd

	def bind(self, binddn, bindpw):
		"""Do simple LDAP bind using DN and password."""
		self.binddn=binddn
		self.bindpw=bindpw
		univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, 'bind binddn=%s' % self.binddn)
		self.lo.simple_bind_s(self.binddn, self.__encode_pwd(self.bindpw))

	def __open(self, ca_certfile):
		_d=univention.debug.function('uldap.__open host=%s port=%d base=%s' % (self.host, self.port, self.base))

		if not hasattr(self, 'protocol'):
			self.protocol = 'ldap'

		if self.reconnect:
			univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, 'establishing new connection with retry_max=%d' % self. client_connection_attempt)
			self.lo = ldap.ldapobject.ReconnectLDAPObject(self.uri, trace_stack_limit=None, retry_max=self.client_connection_attempt, retry_delay=1)
		else:
			univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, 'establishing new connection')
			self.lo = ldap.initialize(self.uri, trace_stack_limit=None)

		if ca_certfile:
			self.lo.set_option( ldap.OPT_X_TLS_CACERTFILE, ca_certfile )

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
			self.lo.set_option(ldap.OPT_REFERRALS,0)

	def __encode( self, value ):
		if value == None:
			return value
		elif isinstance(value, unicode):
			return str( value )
		elif isinstance(value, (list, tuple)):
			return map(self.__encode, value)
		elif isinstance(value, dict):
			return dict(map(lambda (k, v): (k, encode(v)), value.items()))
		else:
			return value

	def __recode_attribute( self, attr, val ):
		if attr in self.decode_ignorelist:
			return val
		return self.__encode( val )

	def __recode_entry(self, entry):
		if isinstance(entry, tuple) and len(entry) == 3:
			return ( entry[ 0 ], entry[ 1 ], self.__recode_attribute( entry[ 1 ], entry[ 2 ] ) )
		elif isinstance(entry, tuple) and len(entry) == 2:
			return ( entry[ 0 ], self.__recode_attribute( entry[ 0 ], entry[ 1 ] ) )
		elif isinstance( entry, (list, tuple)):
			return map(self.__recode_entry, entry)
		elif isinstance(entry, dict):
			return dict(map(lambda (k, v): (k, self.__recode_attribute(k, v)), entry.items()))
		else:
			return entry

	def __encode_entry(self, entry):
		return self.__recode_entry( entry )

	def __encode_attribute(self, attr, val):
		return self.__recode_attribute( attr, val )

	def __decode_entry(self, entry):
		return self.__recode_entry( entry )

	def __decode_attribute(self, attr, val):
		return self.__recode_attribute( attr, val )

	def get(self, dn, attr=[], required=False):
		'''returns ldap object'''

		if dn:
			try:
				result=self.lo.search_s( dn, ldap.SCOPE_BASE,
										 '(objectClass=*)', attr )
			except ldap.NO_SUCH_OBJECT:
				result={}
			if result:
				return self.__decode_entry( result[0][1] )
		if required:
			raise ldap.NO_SUCH_OBJECT, {'desc': 'no object'}
		return {}

	def getAttr(self, dn, attr, required=False):
		'''return attribute of ldap object'''

		_d=univention.debug.function('uldap.getAttr %s %s' % (dn, attr))
		if dn:
			try:
				result=self.lo.search_s( dn, ldap.SCOPE_BASE,
										'(objectClass=*)', [ attr ] )
			except ldap.NO_SUCH_OBJECT:
				result={}
			if result and attr in result[0][1]:
				return result[0][1][attr]
		if required:
			raise ldap.NO_SUCH_OBJECT, {'desc': 'no object'}
		return []

	def search(self, filter='(objectClass=*)', base='', scope='sub', attr=[], unique=False, required=False, timeout=-1, sizelimit=0, serverctrls=None):
		'''do ldap search'''

		univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, 'uldap.search filter=%s base=%s scope=%s attr=%s unique=%d required=%d timeout=%d sizelimit=%d' %  (filter, base, scope, attr, unique, required, timeout, sizelimit))

		if not base:
			base=self.base

		if scope == 'base+one':
			res = self.lo.search_ext_s( base,
										ldap.SCOPE_BASE,
										filter,
										attr,
										serverctrls=serverctrls, clientctrls=None,
										timeout=timeout, sizelimit=sizelimit) + \
										self.lo.search_ext_s( base,
															  ldap.SCOPE_ONELEVEL,
															  filter,
															  attr,
															  serverctrls=serverctrls,
															  clientctrls=None,
															  timeout=timeout, sizelimit=sizelimit)
		else:
			if scope == 'sub' or scope == 'domain':
				ldap_scope=ldap.SCOPE_SUBTREE
			elif scope == 'one':
				ldap_scope=ldap.SCOPE_ONELEVEL
			else:
				ldap_scope=ldap.SCOPE_BASE
			res= self.lo.search_ext_s(
				base,
				ldap_scope,filter,
				attr,
				serverctrls=serverctrls, clientctrls=None,
				timeout=timeout, sizelimit=sizelimit)


		if unique and len(res) > 1:
			raise ldap.INAPPROPRIATE_MATCHING, {'desc': 'more than one object'}
		if required and len(res) < 1:
			raise ldap.NO_SUCH_OBJECT, {'desc': 'no object'}

		# The MDB backend returns the ldap base if scope one is used.
		# Remove the base in this case from the search result.
		#  https://forge.univention.org/bugzilla/show_bug.cgi?id=36169
		if scope == 'one':
			return [item for item in res if item[0] != base]

		return res

	def searchDn(self, filter='(objectClass=*)', base='', scope='sub', unique=False, required=False, timeout=-1, sizelimit=0, serverctrls=None):
		_d=univention.debug.function('uldap.searchDn filter=%s base=%s scope=%s unique=%d required=%d' % (filter, base, scope, unique, required))
		return map(lambda(x): x[0], self.search(filter, base, scope, ['dn'], unique, required, timeout, sizelimit, serverctrls))

	def getPolicies(self, dn, policies=None, attrs=None, result=None, fixedattrs=None):
		if attrs is None:
			attrs = {}
		if policies is None:
			policies = []
		_d = univention.debug.function('uldap.getPolicies dn=%s policies=%s attrs=%s' % (
			dn, policies, attrs))
		if not dn and not policies: # if policies is set apply a fictionally referenced list of policies
			return {}

		# get current dn
		if attrs and 'objectClass' in attrs and 'univentionPolicyReference' in attrs:
			oattrs = attrs
		else:
			oattrs = self.get(dn, ['univentionPolicyReference', 'objectClass'])
		if attrs and 'univentionPolicyReference' in attrs:
			policies=attrs['univentionPolicyReference']
		elif not policies and not attrs:
			policies=oattrs.get('univentionPolicyReference', [])

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

	def add(self, dn, al):
		"""Add LDAP entry with dn and attributes in add_list=(attribute-name, old-values. new-values) or (attribute-name, new-values)."""

		univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, 'uldap.add dn=%s' % dn)
		nal={}
		for i in al:
			if len(i) == 3 and i[2]:
				v=i[2]
			elif len(i) == 2 and i[1]:
				v=i[1]
			else:
				continue
			if not isinstance(v, list):
				v=[v]
			templist = nal.setdefault(i[0], [])
			_extend_uniq(templist, v)
		nal = self.__encode_entry(nal.items())
		try:
			self.lo.add_s(dn, nal)
		except ldap.REFERRAL, e:
			if self.follow_referral:
				univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, 'Following LDAP referral')
				lo_ref = self._handle_referral(e)
				lo_ref.add_s(dn, nal)
			else:
				raise

	def modify(self, dn, changes, atomic=0):
		"""Modify LDAP entry dn with attributes in changes=(attribute-name, old-values, new-values)."""

		univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, 'uldap.modify %s' % dn)

		rename=None
		ml=[]
		for key, oldvalue, newvalue in changes:
			if dn.startswith(key+'='):
				rename=key+'='+newvalue
			if oldvalue and newvalue:
				if oldvalue == newvalue:
					continue
				if atomic:
					ml.append((ldap.MOD_DELETE, key, val))
					ml.append((ldap.MOD_ADD, key, val))
					continue
				op=ldap.MOD_REPLACE
				if (key == 'krb5ValidEnd' or key == 'krb5PasswordEnd') and newvalue == '0':
					val=0

				else:
					val=newvalue

			elif not oldvalue and newvalue:
				op=ldap.MOD_ADD
				val=newvalue
			elif oldvalue and not newvalue:
				op=ldap.MOD_DELETE
				if key == "jpegPhoto":
					val=None
				else:
					val=oldvalue
			else:
				continue
			ml.append((op, key, val))

		ml=self.__encode_entry(ml)
		if rename:
			univention.debug.debug(univention.debug.LDAP, univention.debug.WARN, 'rename %s' % rename)
			self.lo.rename_s(dn, rename, None, delold=1)
			dn=rename+dn[dn.find(','):]
		if ml:
			try:
				self.lo.modify_s(dn, ml)
			except ldap.REFERRAL, e:
				if self.follow_referral:
					univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, 'Following LDAP referral')
					lo_ref = self._handle_referral(e)
					lo_ref.modify_s(dn, ml)
				else:
					raise
		return dn

	def modify_s(self, dn, ml):
		"""Redirect modify_s directly to lo"""
		try:
			self.lo.modify_s(dn, ml)
		except ldap.REFERRAL, e:
			if self.follow_referral:
				univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, 'Following LDAP referral')
				lo_ref = self._handle_referral(e)
				lo_ref.modify_s(dn, ml)
			else:
				raise


	def rename(self, dn, newdn):
		univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, 'uldap.rename %s -> %s' % (dn,newdn))
		oldrdn = dn[:dn.find(',')]
		oldsdn = dn[dn.find(',')+1:]
		newrdn = newdn[:newdn.find(',')]
		newsdn = newdn[newdn.find(',')+1:]

		if not newsdn.lower() == oldsdn.lower():
			univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, 'uldap.rename: move %s to %s in %s' % (dn, newrdn, newsdn))
			try:
				self.lo.rename_s(dn, newrdn, newsdn)
			except ldap.REFERRAL, e:
				if self.follow_referral:
					univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, 'Following LDAP referral')
					lo_ref = self._handle_referral(e)
					lo_ref.rename_s(dn, newrdn, newsdn)
				else:
					raise
		else:
			univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, 'uldap.rename: modrdn %s to %s' % (dn, newrdn))
			try:
				self.lo.rename_s(dn, newrdn)
			except ldap.REFERRAL, e:
				if self.follow_referral:
					univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, 'Following LDAP referral')
					lo_ref = self._handle_referral(e)
					lo_ref.rename_s(dn, newrdn)
				else:
					raise

	def delete(self, dn):

		univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, 'uldap.delete %s' % dn)
		if dn:
			univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, 'delete')
			try:
				self.lo.delete_s(dn)
			except ldap.REFERRAL, e:
				if self.follow_referral:
					univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, 'Following LDAP referral')
					lo_ref = self._handle_referral(e)
					lo_ref.delete_s(dn)
				else:
					raise

	def parentDn(self, dn):
		return parentDn(dn, self.base)

	def hasChilds(self, dn):
		# try operational attributes
		attrs=self.lo.search_s(dn, ldap.SCOPE_BASE, '(objectClass=*)', ['hasSubordinates'])
		if 'hasSubordinates' in attrs:
			if attrs['hasSubordinates'][0]=='TRUE':
				return True
			elif attrs['hasSubordinates'][0]=='FALSE':
				return False
		# do onelevel search
		old_sizelimit=ldap.get_option(ldap.OPT_SIZELIMIT)
		ldap.set_option(ldap.OPT_SIZELIMIT, 1)
		result = self.lo.search_s(dn, ldap.SCOPE_ONELEVEL, '(objectClass=*)', [''])
		ldap.set_option(ldap.OPT_SIZELIMIT, old_sizelimit)
		# BUG: evaluate result to TRUE | FALSE is missing here ?!

	def explodeDn(self, dn, notypes=False):
		return explodeDn(dn, notypes)

	def __getstate__(self):

		_d=univention.debug.function('uldap.__getstate__')
		odict=self.__dict__.copy()
		del odict['lo']
		return odict

	def __setstate__(self, dict):

		_d=univention.debug.function('uldap.__setstate__')
		self.__dict__.update(dict)
		self.__open()

	def _handle_referral(self, exception):
		# Following referral
		e = exception.args[0]
		info = e.get('info')
		ldap_url = info[info.find('ldap'):]
 		if isLDAPUrl(ldap_url):
			conn_str = LDAPUrl(ldap_url).initializeUrl()

			lo_ref = ldap.ldapobject.ReconnectLDAPObject(conn_str, trace_stack_limit=None)

			if self.ca_certfile:
				lo_ref.set_option( ldap.OPT_X_TLS_CACERTFILE, self.ca_certfile )

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
			raise ldap.CONNECT_ERROR, 'Bad referral "%s"' % str(e)


	def needed_objectclasses(self, entry):

		dont_remove=['organizationalPerson', 'univentionPerson']

		schema_attrs = ldap.schema.SCHEMA_ATTRS

		ldap.set_option(ldap.OPT_DEBUG_LEVEL,0)

		ldap._trace_level = 0

		subschemasubentry_dn,schema = ldap.schema.urlfetch('%s/cn=subschema',self.uri)

		if subschemasubentry_dn is None:
			univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, 'No sub schema sub entry found!')
			return None

		needed_oc=[]
		for attr_type,schema_class in ldap.schema.SCHEMA_CLASS_MAPPING.items():
			if attr_type == 'objectClasses':
				for element_id in schema.listall(schema_class):
					se_orig = schema.get_obj(schema_class,element_id)
					attributes=se_orig.may+se_orig.must
					for i in range(0,len(se_orig.names)):
						if se_orig.names[i] in entry['objectClass'] and not se_orig.names[i] in needed_oc:
							for j in attributes:
								if (j in res[0][1] or j in dont_remove) and not se_orig.names[i] in needed_oc:
									needed_oc.append(se_orig.names[i])

		return needed_oc
