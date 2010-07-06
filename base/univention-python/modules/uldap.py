#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Python
#  LDAP access
#
# Copyright 2002-2010 Univention GmbH
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

import ldap, re, types, codecs
import sys,ldap.schema
import univention.debug
import univention_baseconfig

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

def getAdminConnection(start_tls=2, decode_ignorelist=[]):
	baseConfig=univention_baseconfig.baseConfig()
	baseConfig.load()
	bindpw=open('/etc/ldap.secret').read()
	if bindpw[-1] == '\n':
		bindpw=bindpw[0:-1]
	lo=access(host=baseConfig['ldap/master'], base=baseConfig['ldap/base'], binddn='cn=admin,'+baseConfig['ldap/base'], bindpw=bindpw, start_tls=start_tls, decode_ignorelist=decode_ignorelist)
	return lo

def getBackupConnection(start_tls=2, decode_ignorelist=[]):
	baseConfig=univention_baseconfig.baseConfig()
	baseConfig.load()
	bindpw=open('/etc/ldap-backup.secret').read()
	if bindpw[-1] == '\n':
		bindpw=bindpw[0:-1]
	try:
		lo=access(host=baseConfig['ldap/master'], base=baseConfig['ldap/base'], binddn='cn=backup,'+baseConfig['ldap/base'], bindpw=bindpw, start_tls=start_tls, decode_ignorelist=decode_ignorelist)
	except ldap.SERVER_DOWN:
		if baseConfig['ldap/backup']:
			backup=string.split(baseConfig['ldap/backup'],' ')[0]
			lo=access(host=backup, base=baseConfig['ldap/base'], binddn='cn=backup,'+baseConfig['ldap/base'], bindpw=bindpw, start_tls=start_tls, decode_ignorelist=decode_ignorelist)
		else:
			raise ldap.SERVER_DOWN
	return lo

def getMachineConnection(start_tls=2, decode_ignorelist=[]):
	baseConfig=univention_baseconfig.baseConfig()
	baseConfig.load()
	bindpw=open('/etc/machine.secret').read()
	if bindpw[-1] == '\n':
		bindpw=bindpw[0:-1]
	lo=access(host=baseConfig['ldap/master'], base=baseConfig['ldap/base'], binddn=baseConfig['ldap/hostdn'], bindpw=bindpw, start_tls=start_tls, decode_ignorelist=decode_ignorelist)
	return lo

class access:

	def __init__(self, host='localhost', port=389, base='', binddn='', bindpw='', start_tls=2, ca_certfile=None, decode_ignorelist=[]):
		"""start_tls = 0 (no); 1 (try); 2 (must)"""
		self.host = host
		self.port = port
		self.base = base
		self.binddn = binddn
		self.bindpw = bindpw
		self.start_tls = start_tls
		self.ca_certfile = ca_certfile
		if not decode_ignorelist or decode_ignorelist == []:
			baseConfig = univention_baseconfig.baseConfig()
			baseConfig.load()
			self.decode_ignorelist = baseConfig.get('ldap/binaryattributes', 'krb5Key,userCertificate;binary').split(',')
		else:
			self.decode_ignorelist = decode_ignorelist

		if not ca_certfile:
			self.__open()
		else:
			self.__smart_open()
			pass

	def __encode_pwd(self, pwd):
		if isinstance( pwd, unicode ):
			return str( pwd )
		else:
			return pwd

	def bind(self, binddn, bindpw):

		self.binddn=binddn
		self.bindpw=bindpw
		univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, 'bind binddn=%s' % self.binddn)
		self.lo.simple_bind_s(self.binddn, self.__encode_pwd(self.bindpw))

	def __smart_open(self):
		_d=univention.debug.function('uldap.__smart_open host=%s port=%d base=%s' % (self.host, self.port, self.base))

		univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, 'establishing new connection')

		ldap.set_option( ldap.OPT_X_TLS_CACERTFILE, self.ca_certfile )
		self.lo=ldap.ldapobject.SmartLDAPObject(uri="ldap://"+str(self.host)+":"+str(self.port), start_tls=self.start_tls, tls_cacertfile=self.ca_certfile)
		self.lo.simple_bind_s(self.binddn, self.__encode_pwd(self.bindpw))

	def __open(self):
		_d=univention.debug.function('uldap.__open host=%s port=%d base=%s' % (self.host, self.port, self.base))

		univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, 'establishing new connection')
		self.lo=ldap.initialize("ldap://"+str(self.host)+":"+str(self.port))

		if self.start_tls == 1:
			try:
				self.lo.start_tls_s()
			except:
				univention.debug.debug(univention.debug.LDAP, univention.debug.WARN, 'Could not start TLS')
		elif self.start_tls == 2:
			self.lo.start_tls_s()

		if self.binddn:
			univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, 'bind binddn=%s' % self.binddn)
			self.lo.simple_bind_s(self.binddn, self.__encode_pwd(self.bindpw))

	def __encode( self, value ):
		if value == None:
			return value
		if isinstance( value, types.UnicodeType ):
			return str( value )

		if isinstance( value, ( types.ListType, types.TupleType ) ):
			ls = []
			for i in value:
				ls.append( self.__encode( i ) )
			return ls
		if isinstance( value, types.DictType ):
			dict = {}
			for k in value.keys():
				dict[ k ] = encode( value[ k ] )
			return dict
		else:
			return value

	def __recode_attribute( self, attr, val ):
		if attr in self.decode_ignorelist:
			return val
		return self.__encode( val )

	def __recode_entry(self, entry ):
		if type(entry) == types.TupleType and len(entry) == 3:
			return ( entry[ 0 ], entry[ 1 ], self.__recode_attribute( entry[ 1 ], entry[ 2 ] ) )
		elif type(entry) == types.TupleType and len(entry) == 2:
			return ( entry[ 0 ], self.__recode_attribute( entry[ 0 ], entry[ 1 ] ) )
		elif isinstance( entry, ( types.ListType, types.TupleType ) ):
			new=[]
			for i in entry:
				new.append( self.__recode_entry( i ) )
			return new
		elif type( entry ) == types.DictType:
			new = {}
			for attr, val in entry.items():
				new[ attr ]=self.__recode_attribute( attr, val )
			return new
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

	def get(self, dn, attr=[], required=0):
		'''returns ldap object'''

		if dn:
			try:
				result=self.lo.search_s( dn, ldap.SCOPE_BASE,
										 '(objectClass=*)',attr )
			except ldap.NO_SUCH_OBJECT:
				result={}
			if result:
				return self.__decode_entry( result[0][1] )
		if required:
			raise ldap.NO_SUCH_OBJECT, {'desc': 'no object'}
		return {}

	def getAttr(self, dn, attr, required=0):
		'''return attribute of ldap object'''

		_d=univention.debug.function('uldap.getAttr %s %s' % (dn, attr))
		if dn:
			try:
				result=self.lo.search_s( dn, ldap.SCOPE_BASE,
										'(objectClass=*)', [ attr ] )
			except ldap.NO_SUCH_OBJECT:
				result={}
			if result and result[0][1].has_key(attr):
				return result[0][1][attr]
		if required:
			raise ldap.NO_SUCH_OBJECT, {'desc': 'no object'}
		return []

	def search(self, filter='(objectClass=*)', base='', scope='sub', attr=[], unique=0, required=0, timeout=-1, sizelimit=0, serverctrls=None):
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
		return res

	def searchDn(self, filter='(objectClass=*)', base='', scope='sub', unique=0, required=0, timeout=-1, sizelimit=0, serverctrls=None):
		_d=univention.debug.function('uldap.searchDn filter=%s base=%s scope=%s unique=%d required=%d' % (filter, base, scope, unique, required))
		return map(lambda(x): x[0], self.search(filter, base, scope, ['dn'], unique, required, timeout, sizelimit, serverctrls))

	def getPolicies(self, dn, policies=[], attrs={}, result={}, fixedattrs={}):
		_d=univention.debug.function('uldap.getPolicies dn=%s policies=%s attrs=%s result=%s fixedattrs=%s' % (dn, policies, attrs, result, fixedattrs))
		if not dn:
			return {}
		# get current dn
		if attrs and attrs.has_key('univentionPolicyReference'):
			policies=attrs['univentionPolicyReference']
		elif not policies and not attrs:
			policies=self.getAttr(dn, 'univentionPolicyReference')

		parent_dn=self.parentDn(dn)
		if parent_dn:
			result=self.getPolicies(parent_dn, result=result, fixedattrs=fixedattrs)

		for pdn in policies:
			pattrs=self.get(pdn)
			ptype=None
			if pattrs:
				for oc in pattrs['objectClass']:
					if oc == 'top' or oc == 'univentionPolicy':
						continue
					ptype=oc
					break

				if not ptype:
					continue
				if not result.has_key(ptype):
					result[ptype]={}
				if not fixedattrs.has_key(ptype):
					fixedattrs[ptype]={}

				for key, value in pattrs.items():
					if key in ['requiredObjectClasses', 'prohibitedObjectClasses', 'fixedAttributes', 'emptyAttributes', 'objectClass', 'cn']:
						continue
					if not fixedattrs[ptype].has_key(key):
						univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, "getPolicies: %s sets: %s=%s" % (pdn, key, value))
						result[ptype][key]={}
						result[ptype][key]['policy']=pdn
						result[ptype][key]['value']=value
						if key in pattrs.get('emptyAttributes', []):
							result[ptype][key]['value']=[]
						if key in pattrs.get('fixedAttributes', []):
							result[ptype][key]['fixed']=1
						else:
							result[ptype][key]['fixed']=0
				for key in pattrs.get('fixedAttributes', []):
					if not fixedattrs[ptype].has_key(key):
						fixedattrs[ptype][key]=pdn
						if not result[ptype].has_key(key):
							result[ptype][key]={}
							result[ptype][key]['policy']=pdn
							result[ptype][key]['value']=[]
							result[ptype][key]['fixed']=1
				for key in pattrs.get('emptyAttributes', []):
					if not result[ptype].has_key(key):
						result[ptype][key]={}
						result[ptype][key]['policy']=pdn
						result[ptype][key]['value']=[]
					elif not (result[ptype][key].has_key('fixed') and result[ptype][key]['fixed']):
						result[ptype][key]['value']=[]

		univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, "getPolicies: result: %s" % result)
		return result

	def add(self, dn, al):

		univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, 'uldap.add dn=%s' % dn)
		nal={}
		for i in al:
			v=None
			if len(i) == 3 and i[2]:
				v=i[2]
			elif len(i) == 2 and i[1]:
				v=i[1]
			if not v:
				continue
			if not nal.has_key(i[0]):
				nal[i[0]]=[]
			if not type(v) == types.ListType:
				v=[v]
			templist=nal[i[0]]
			_extend_uniq(templist, v)
			nal[i[0]]=templist
		nal=self.__encode_entry(nal.items())
		self.lo.add_s(dn, nal)

	def modify(self, dn, changes, atomic=0):

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
				if key == 'homePostalAddress':
					op=ldap.MOD_REPLACE
					homePostalAddress=self.getAttr(dn, 'homePostalAddress')
					for i in range(0,len(oldvalue)):
						if oldvalue[i] in homePostalAddress:
							homePostalAddress.remove(oldvalue[i])
					val=homePostalAddress
				elif key == 'pager':
					op=ldap.MOD_REPLACE
					postalAddress=self.getAttr(dn, 'pager')
					for i in range(0,len(oldvalue)):
						if oldvalue[i] in postalAddress:
							postalAddress.remove(oldvalue[i])
					val=postalAddress
				elif key == 'mobile':
					op=ldap.MOD_REPLACE
					mobileTelephoneNumber=self.getAttr(dn, 'mobile')
					for i in range(0,len(oldvalue)):
						if oldvalue[i] in mobileTelephoneNumber:
							mobileTelephoneNumber.remove(oldvalue[i])
					val=mobileTelephoneNumber
				elif key == 'pagerTelephoneNumber':
					op=ldap.MOD_REPLACE
					pagerTelephoneNumber=self.getAttr(dn, 'pagerTelephoneNumber')
					for i in range(0,len(oldvalue)):
						if oldvalue[i] in pagerTelephoneNumber:
							pagerTelephoneNumber.remove(oldvalue[i])
					val=pagerTelephoneNumber
				elif key == "jpegPhoto":
					val=None
				else:
					val=oldvalue
			else:
				continue
			ml.append((op, key, val))

		ml=self.__encode_entry(ml)
		if rename:
			univention.debug.debug(univention.debug.LDAP, univention.debug.WARN, 'rename %s' % rename)
			self.lo.rename_s(dn, rename, None, delold=0)
			dn=rename+dn[dn.find(','):]
		if ml:
			self.lo.modify_s(dn, ml)
		return dn

	def rename(self, dn, newdn):
		univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, 'uldap.rename %s -> %s' % (dn,newdn))
		oldrdn = dn[:dn.find(',')]
		oldsdn = dn[dn.find(',')+1:]
		newrdn = newdn[:newdn.find(',')]
		newsdn = newdn[newdn.find(',')+1:]

		if not newsdn.lower() == oldsdn.lower():
			univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, 'uldap.rename: move %s to %s in %s' % (dn, newrdn, newsdn))
			self.lo.rename_s(dn, newrdn, newsdn)
		else:
			univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, 'uldap.rename: modrdn %s to %s' % (dn, newrdn))
			self.lo.rename_s(dn, newrdn)

	def delete(self, dn):

		univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, 'uldap.delete %s' % dn)
		if dn:
			univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, 'delete')
			self.lo.delete_s(dn)

	def parentDn(self, dn):
		return parentDn(dn, self.base)

	def hasChilds(self, dn):
		# try operational attributes
		attrs=self.lo.search_s(dn, ldap.SCOPE_BASE, '(objectClass=*)', ['hasSubordinates'])
		if attrs.has_key('hasSubordinates'):
			if attrs['hasSubordinates'][0]=='TRUE':
				return 1
			elif attrs['hasSubordinates'][0]=='FALSE':
				return 0
		# do onelevel search
		old_sizelimit=ldap.get_option(ldap.OPT_SIZELIMIT)
		ldap.set_option(ldap.OPT_SIZELIMIT, 1)
		self.lo.search_s(dn, ldap.SCOPE_ONELEVEL, '(objectClass=*)', [''])
		ldap.set_option(ldap.OPT_SIZELIMIT, old_sizelimit)

	def explodeDn(self, dn, notypes=0):
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

	def needed_objectclasses(self, entry):

		dont_remove=['organizationalPerson', 'univentionPerson']

		schema_attrs = ldap.schema.SCHEMA_ATTRS

		ldap.set_option(ldap.OPT_DEBUG_LEVEL,0)

		ldap._trace_level = 0

		subschemasubentry_dn,schema = ldap.schema.urlfetch('ldap://%s:%s/cn=subschema',self.host,self.port)

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
								if (res[0][1].has_key(j) or j in dont_remove) and not se_orig.names[i] in needed_oc:
									needed_oc.append(se_orig.names[i])

		return needed_oc
