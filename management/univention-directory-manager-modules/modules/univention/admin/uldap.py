# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  wrapper around univention.uldap that replaces exceptions
#
# Copyright 2004-2011 Univention GmbH
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
import univention.uldap
import string
import univention.admin.localization
import univention.config_registry

try:
	import univention.admin.license
	GPLversion=False
except:
	GPLversion=True

translation=univention.admin.localization.translation('univention/admin')
_=translation.translate

configRegistry=univention.config_registry.ConfigRegistry()
configRegistry.load()

explodeDn=univention.uldap.explodeDn

def getBaseDN(host='localhost', port=None, uri=None):
	if not uri:
		if not port:
			port = int(configRegistry.get('ldap/server/port', 7389))
		uri = "ldap://%s:%s" % (host, port)
	l=ldap.initialize(uri)
	result=l.search_s('',ldap.SCOPE_BASE,'objectClass=*',['NamingContexts'])
	return result[0][1]['namingContexts'][0]

def getAdminConnection(start_tls=2,decode_ignorelist=[]):
	lo=univention.uldap.getAdminConnection(start_tls, decode_ignorelist=decode_ignorelist)
	pos=position(lo.base)
	return access(lo=lo), pos

def getMachineConnection(start_tls=2,decode_ignorelist=[], ldap_master = True):
	lo=univention.uldap.getMachineConnection(start_tls, decode_ignorelist=decode_ignorelist, ldap_master=ldap_master)
	pos=position(lo.base)
	return access(lo=lo), pos

def _err2str(err):
	msgs = []
	for iarg in err.args:
		if 'info' in iarg and 'desc' in iarg:
			msgs.append('%(desc)s: %(info)s' % iarg)
		elif 'desc' in iarg:
			msgs.append(str(iarg['desc']))
	return '. '.join(msgs)

class domain:
	def __init__(self, lo, position):
		self.lo=lo
		self.position=position
		self.domain=self.lo.get(self.position.getDomain(), attr=['sambaDomain', 'sambaSID', 'krb5RealmName'])
	def getKerberosRealm(self):
		if self.domain.has_key('krb5RealmName'):
			return self.domain['krb5RealmName'][0]

class position:
	def __init__(self, base, loginDomain=''):
		if not base:
			raise univention.admin.uexceptions.insufficientInformation, _( "There was no LDAP base specified." )

		if not loginDomain:
			self.__loginDomain=base
		else:
			self.__loginDomain=loginDomain

		self.__base=base
		self.__pos=""
		self.__indomain=0

	def setBase(self, base):
		self.__base=base

	def setLoginDomain(self, loginDomain):
		self.__loginDomain=loginDomain

	def __setPosition(self, pos):
		self.__pos=pos
		self.__indomain=0
		components=explodeDn(self.__pos,0)
		for i in components:
			mytype, ign = string.split(i,'=')
			if mytype=='dc':
				self.__indomain=1
				break
	def getDn(self):
		if self.__getPosition():
			dn=self.__pos+","+self.__base
		else:
			dn=self.__base
		return dn
	def setDn(self, dn):
		try:
			self.__indomain=0
			baselist=explodeDn(self.getBase())
			baselist.reverse()
			dnlist=explodeDn(dn)
			dnlist.reverse()
			baselist.reverse()
			for i in baselist:
				dnlist.remove(i)
			dnlist.reverse()
			self.__pos=string.join(dnlist, ',')
			components=explodeDn(self.__pos,0)
			for i in components:
				mytype, ign = string.split(i,'=')
				if mytype=='dc':
					self.__indomain=1
					break
		except ValueError:
			raise univention.admin.uexceptions.noObject, _("DN not found: %s.") % dn

	def getRdn(self):
		components=explodeDn(self.getDn(),0)
		return components.pop(0)

	def getBase(self):
		return self.__base

	def isBase(self):
		return self.getDn() == self.getBase()

	def getDomain(self):
		if not self.__indomain or self.getDn() == self.getBase():
			return self.getBase()
		components=explodeDn(self.getDn(),0)
		components.reverse()
		domaincomponents=[]
		for i in components:
			mytype, ign = string.split(i,'=')
			if mytype=='dc':
				domaincomponents.append(i)
			else:
				break
		domaincomponents.reverse()
		domain=string.join(domaincomponents,',')
		return domain

	def getDomainConfigBase(self):
		return 'cn=univention,'+self.getDomain()

	def isDomain(self):
		return self.getDn() == self.getDomain()

	def getLoginDomain(self):
		return self.__loginDomain

	def __getPosition(self):
		return self.__pos
	def __getPositionInDomain(self):
		components=explodeDn(self.__pos,0)
		components.reverse()
		poscomponents=[]
		for i in components:
			mytype, ign = string.split(i,'=')
			if mytype!='dc':
				poscomponents.append(i)
		poscomponents.reverse()
		positionindomain=string.join(poscomponents,',')
		return positionindomain

	def switchToParent(self):
		if self.isBase():
			return 0
		poscomponents=explodeDn(self.__pos,0)
		poscomponents.pop(0)
		self.__setPosition(string.join(poscomponents,','))
		return 1

	def getPrintable(self, short=1, long=0, trailingslash=1):
		domaincomponents=explodeDn(self.getDomain(),1)
		domain=string.join(domaincomponents, '.')
		indomaindn=self.__getPositionInDomain()
		if indomaindn:
			components=explodeDn(indomaindn,1)
			components.reverse()
			if not short or long:
				printable=domain+':/'+string.join(components, '/')
				if trailingslash:
					printable+='/'
			else:
				printable=""
				for i in range(len(components)):
					printable+="&nbsp;&nbsp;"
				printable+=components.pop()
		else:
			printable=domain
		return printable

	# new "version" of getPrintable, returns the tree-depth as int instead of html-blanks
	def getPrintable_depth(self, short=1, long=0, trailingslash=1):
		domaincomponents=explodeDn(self.getDomain(),1)
		domain=string.join(domaincomponents, '.')
		indomaindn=self.__getPositionInDomain()
		depth = 0
		if indomaindn:
			components=explodeDn(indomaindn,1)
			components.reverse()
			if not short or long:
				printable=domain+':/'+string.join(components, '/')
				if trailingslash:
					printable+='/'
			else:
				printable=""
				depth = len(components)*2
				printable+=components.pop()
		else:
			printable=domain
		return (printable,depth)


class access:

	def __init__(self, host='localhost', port=None, base='', binddn='', bindpw='', start_tls=2, lo=None):
		if lo:
			self.lo=lo
		else:
			if not port:
				port = int(configRegistry.get('ldap/server/port', 7389))
			try:
				self.lo=univention.uldap.access(host, port, base, binddn, bindpw, start_tls)
			except ldap.INVALID_CREDENTIALS,ex:
				raise univention.admin.uexceptions.authFail, _( "Authentication failed" )
			except ldap.UNWILLING_TO_PERFORM,ex:
				raise univention.admin.uexceptions.authFail, _( "Authentication failed" )
		self.host=self.lo.host
		self.port=self.lo.port
		self.base=self.lo.base
		self.binddn=self.lo.binddn
		self.bindpw=self.lo.bindpw
		self.start_tls=start_tls
		self.require_license=0
		self.allow_modify=1
		self.licensetypes = [ 'UCS' ]


	def bind(self, binddn, bindpw):
		try:
			self.lo.bind(binddn, bindpw)
		except ldap.INVALID_CREDENTIALS:
			raise univention.admin.uexceptions.authFail, _( "Authentication failed" )
		except ldap.UNWILLING_TO_PERFORM:
			raise univention.admin.uexceptions.authFail, _( "Authentication failed" )


		if self.require_license:
			if GPLversion:
				self.require_license = 0
				raise univention.admin.uexceptions.licenseGPLversion

			res=univention.admin.license.init_select(self.lo, 'admin')

			self.licensetypes = univention.admin.license._license.types

			if res == 1:
				self.allow_modify=0
				raise univention.admin.uexceptions.licenseClients
			elif res == 2:
				self.allow_modify=0
				raise univention.admin.uexceptions.licenseAccounts
			elif res == 3:
				self.allow_modify=0
				raise univention.admin.uexceptions.licenseDesktops
			elif res == 4:
				self.allow_modify=0
				raise univention.admin.uexceptions.licenseGroupware
			elif res == 5:
				# Free for personal use edition
				raise univention.admin.uexceptions.freeForPersonalUse

	def requireLicense(self, require=1):
		self.require_license=require

	def _validateLicense(self):
		if self.require_license and not GPLversion:
			univention.admin.license.select('admin')

	def get(self, dn, attr=[], required=0, exceptions=0):
		return self.lo.get(dn, attr, required)

	def getAttr(self, dn, attr, required=0, exceptions=0):
		return self.lo.getAttr(dn, attr, required)

	def search(self, filter='(objectClass=*)', base='', scope='sub', attr=[], unique=0, required=0, timeout=-1, sizelimit=0):
		try:
			return self.lo.search(filter, base, scope, attr, unique, required, timeout, sizelimit)
		except ldap.NO_SUCH_OBJECT, msg:
			raise univention.admin.uexceptions.noObject, _err2str(msg)
		except ldap.INAPPROPRIATE_MATCHING, msg:
			raise univention.admin.uexceptions.insufficientInformation, _err2str(msg)
		except ldap.LDAPError, msg:
			raise univention.admin.uexceptions.ldapError, _err2str(msg)

	def searchDn(self, filter='(objectClass=*)', base='', scope='sub', unique=0, required=0, timeout=-1, sizelimit=0):
		try:
			return self.lo.searchDn(filter, base, scope, unique, required, timeout, sizelimit)
		except ldap.NO_SUCH_OBJECT, msg:
			raise univention.admin.uexceptions.noObject, _err2str(msg)
		except ldap.INAPPROPRIATE_MATCHING, msg:
			raise univention.admin.uexceptions.insufficientInformation, _err2str(msg)
		except ldap.LDAPError, msg:
			# workaround for bug 14827 ==> msg tuple seems to be empty
			if not msg:
				univention.debug.debug(univention.debug.ADMIN, univention.debug.ERROR, 'uldap.searchDn: ldapError occured: msg=' % str(msg))
				raise univention.admin.uexceptions.ldapError, str(msg)
			raise univention.admin.uexceptions.ldapError, _err2str(msg)

	def getPolicies( self, dn, policies = None, attrs = None, result = None, fixedattrs = None ):
		univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'getPolicies modules dn %s result' % dn)
		return self.lo.getPolicies(dn, policies, attrs, result, fixedattrs )

	def add(self, dn, al, exceptions=False):
		self._validateLicense()
		if not self.allow_modify:
			univention.debug.debug(univention.debug.ADMIN, univention.debug.ERROR, 'add dn: %s' % dn)
			raise univention.admin.uexceptions.licenseDisableModify
			return []
		univention.debug.debug(univention.debug.LDAP, univention.debug.ALL, 'add dn=%s al=%s' % (dn, al))
		if exceptions:
			return self.lo.add(dn, al)
		try:
			return self.lo.add(dn, al)
		except ldap.ALREADY_EXISTS, msg:
			univention.debug.debug(univention.debug.LDAP, univention.debug.ALL, 'add dn=%s err=%s' % (dn, msg))
			raise univention.admin.uexceptions.objectExists, dn
		except ldap.INSUFFICIENT_ACCESS, msg:
			univention.debug.debug(univention.debug.LDAP, univention.debug.ALL, 'add dn=%s err=%s' % (dn, msg))
			raise univention.admin.uexceptions.permissionDenied
		except ldap.LDAPError, msg:
			univention.debug.debug(univention.debug.LDAP, univention.debug.ALL, 'add dn=%s err=%s' % (dn, msg))
			raise univention.admin.uexceptions.ldapError, _err2str(msg)

	def modify(self, dn, changes, exceptions=False, ignore_license=0):
		self._validateLicense()
		if not self.allow_modify and not ignore_license:
			univention.debug.debug(univention.debug.ADMIN, univention.debug.ERROR, 'modify dn: %s'%  dn)
			raise univention.admin.uexceptions.licenseDisableModify
			return []
		univention.debug.debug(univention.debug.LDAP, univention.debug.ALL, 'mod dn=%s ml=%s' % (dn, changes))
		if exceptions:
			return self.lo.modify(dn, changes)
		try:
			return self.lo.modify(dn, changes)
		except ldap.NO_SUCH_OBJECT, msg:
			univention.debug.debug(univention.debug.LDAP, univention.debug.ALL, 'mod dn=%s err=%s' % (dn, msg))
			raise univention.admin.uexceptions.noObject
		except ldap.INSUFFICIENT_ACCESS, msg:
			univention.debug.debug(univention.debug.LDAP, univention.debug.ALL, 'mod dn=%s err=%s' % (dn, msg))
			raise univention.admin.uexceptions.permissionDenied
		except ldap.LDAPError, msg:
			univention.debug.debug(univention.debug.LDAP, univention.debug.ALL, 'mod dn=%s err=%s' % (dn, msg))
			raise univention.admin.uexceptions.ldapError, _err2str(msg)

	def rename(self, dn, newdn, move_childs=0, ignore_license=False):
		if not move_childs == 0:
			raise univention.admin.uexceptions.noObject, _( "Moving childs is not supported." )
		self._validateLicense()
		if not self.allow_modify and not ignore_license:
			univention.debug.debug(univention.debug.ADMIN, univention.debug.WARN, 'move dn: %s'%  dn)
			raise univention.admin.uexceptions.licenseDisableModify
			return []
		univention.debug.debug(univention.debug.LDAP, univention.debug.ALL, 'ren dn=%s newdn=%s' % (dn, newdn))
		try:
			return self.lo.rename(dn, newdn)
		except ldap.NO_SUCH_OBJECT, msg:
			univention.debug.debug(univention.debug.LDAP, univention.debug.ALL, 'ren dn=%s err=%s' % (dn, msg))
			raise univention.admin.uexceptions.noObject
		except ldap.INSUFFICIENT_ACCESS, msg:
			univention.debug.debug(univention.debug.LDAP, univention.debug.ALL, 'ren dn=%s err=%s' % (dn, msg))
			raise univention.admin.uexceptions.permissionDenied
		except ldap.LDAPError, msg:
			univention.debug.debug(univention.debug.LDAP, univention.debug.ALL, 'ren dn=%s err=%s' % (dn, msg))
			raise univention.admin.uexceptions.ldapError, _err2str(msg)

	def delete(self, dn, exceptions=False):
		self._validateLicense()
		if exceptions:
			try:
				return self.lo.delete(dn)
			except ldap.INSUFFICIENT_ACCESS, msg:
				raise univention.admin.uexceptions.permissionDenied
		univention.debug.debug(univention.debug.LDAP, univention.debug.ALL, 'del dn=%s' % (dn,))
		try:
			return self.lo.delete(dn)
		except ldap.NO_SUCH_OBJECT, msg:
			univention.debug.debug(univention.debug.LDAP, univention.debug.ALL, 'del dn=%s err=%s' % (dn, msg))
			raise univention.admin.uexceptions.noObject
		except ldap.INSUFFICIENT_ACCESS, msg:
			univention.debug.debug(univention.debug.LDAP, univention.debug.ALL, 'del dn=%s err=%s' % (dn, msg))
			raise univention.admin.uexceptions.permissionDenied
		except ldap.LDAPError, msg:
			univention.debug.debug(univention.debug.LDAP, univention.debug.ALL, 'del dn=%s err=%s' % (dn, msg))
			raise univention.admin.uexceptions.ldapError, _err2str(msg)

	def parentDn(self, dn):
		return self.lo.parentDn(dn)

	def explodeDn(self, dn, notypes=0):
		return self.lo.explodeDn(dn, notypes)
