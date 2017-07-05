# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  wrapper around univention.uldap that replaces exceptions
#
# Copyright 2004-2017 Univention GmbH
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
import string
import time

import univention.uldap
from univention.admin import localization
import univention.config_registry
import univention.admin.license

translation = localization.translation('univention/admin')
_ = translation.translate

configRegistry = univention.config_registry.ConfigRegistry()
configRegistry.load()

explodeDn = univention.uldap.explodeDn


class DN(object):
	"""A LDAP Distinguished Name"""

	def __init__(self, dn):
		self.dn = dn
		try:
			self._dn = ldap.dn.str2dn(self.dn)
		except ldap.DECODING_ERROR:
			raise ValueError('Malformed DN syntax: %r' % (self.dn,))

	def __str__(self):
		return ldap.dn.dn2str(self._dn)

	def __unicode__(self):
		return unicode(str(self))

	def __repr__(self):
		return '<%s %r>' % (type(self).__name__, str(self),)

	def __eq__(self, other):
		"""
		>>> DN('foo=1') == DN('foo=1')
		True
		>>> DN('foo=1') == DN('foo=2')
		False
		>>> DN('Foo=1') == DN('foo=1')
		True
		>>> DN('Foo=1') == DN('foo=2')
		False
		>>> DN('foo=1,bar=2') == DN('foo=1,bar=2')
		True
		>>> DN('bar=2,foo=1') == DN('foo=1,bar=2')
		False
		>>> DN('foo=1+bar=2') == DN('foo=1+bar=2')
		True
		>>> DN('bar=2+foo=1') == DN('foo=1+bar=2')
		True
		>>> DN('bar=2+Foo=1') == DN('foo=1+Bar=2')
		True
		>>> DN(r'foo=%s31' % chr(92)) == DN(r'foo=1')
		True
		"""
		return hash(self) == hash(other)

	def __ne__(self, other):
		return not self == other

	def __hash__(self):
		# TODO: attributes which's values are case insensitive should be respected
		return hash(tuple([tuple(sorted((x.lower(), y, z) for x, y, z in rdn)) for rdn in self._dn]))

	@classmethod
	def set(cls, values):
		"""
			>>> len(DN.set(['CN=computers,dc=foo', 'cn=computers,dc=foo', 'cn = computers,dc=foo']))
			1
		"""
		return set(map(cls, values))

	@classmethod
	def values(cls, values):
		"""
			>>> DN.values(DN.set(['cn=foo', 'cn=bar']) - DN.set(['cn = foo']))
			set(['cn=bar'])
		"""
		return set(map(str, values))


def getBaseDN(host='localhost', port=None, uri=None):
	if not uri:
		if not port:
			port = int(configRegistry.get('ldap/server/port', 7389))
		uri = "ldap://%s:%s" % (host, port)
	try:
		lo = ldap.ldapobject.ReconnectLDAPObject(uri, trace_stack_limit=None)
		result = lo.search_s('', ldap.SCOPE_BASE, 'objectClass=*', ['NamingContexts'])
		return result[0][1]['namingContexts'][0]
	except ldap.SERVER_DOWN:
		time.sleep(60)
	lo = ldap.ldapobject.ReconnectLDAPObject(uri, trace_stack_limit=None)
	result = lo.search_s('', ldap.SCOPE_BASE, 'objectClass=*', ['NamingContexts'])
	return result[0][1]['namingContexts'][0]


def getAdminConnection(start_tls=2, decode_ignorelist=[]):
	lo = univention.uldap.getAdminConnection(start_tls, decode_ignorelist=decode_ignorelist)
	pos = position(lo.base)
	return access(lo=lo), pos


def getMachineConnection(start_tls=2, decode_ignorelist=[], ldap_master=True):
	lo = univention.uldap.getMachineConnection(start_tls, decode_ignorelist=decode_ignorelist, ldap_master=ldap_master)
	pos = position(lo.base)
	return access(lo=lo), pos


def _err2str(err):
	msgs = []
	for iarg in err.args:
		if isinstance(iarg, dict):
			msg = ': '.join([str(m) for m in (iarg.get('desc'), iarg.get('info')) if m])
		else:
			msg = str(iarg)
		if msg:
			msgs.append(msg)
	if not msgs:
		msgs.append(': '.join([str(type(err).__name__), str(err)]))
	return '. '.join(msgs)


class domain:

	def __init__(self, lo, position):
		self.lo = lo
		self.position = position
		self.domain = self.lo.get(self.position.getDomain(), attr=['sambaDomain', 'sambaSID', 'krb5RealmName'])

	def getKerberosRealm(self):
		return self.domain.get('krb5RealmName', [None])[0]


class position:

	def __init__(self, base, loginDomain=''):
		if not base:
			raise univention.admin.uexceptions.insufficientInformation(_("There was no LDAP base specified."))

		self.__loginDomain = loginDomain or base
		self.__base = base
		self.__pos = ""
		self.__indomain = False

	def setBase(self, base):
		self.__base = base

	def setLoginDomain(self, loginDomain):
		self.__loginDomain = loginDomain

	def __setPosition(self, pos):
		self.__pos = pos
		self.__indomain = any('dc' == y[0] for x in ldap.dn.str2dn(self.__pos) for y in x)

	def getDn(self):
		return ldap.dn.dn2str(ldap.dn.str2dn(self.__pos) + ldap.dn.str2dn(self.__base))

	def setDn(self, dn):
		# strip out the trailing base from the DN; store relative dn
		dn = ldap.dn.str2dn(dn)
		base = ldap.dn.str2dn(self.getBase())
		if dn[-len(base):] == base:
			dn = dn[:-len(base)]
		self.__setPosition(ldap.dn.dn2str(dn))

	def getRdn(self):
		return ldap.dn.explode_rdn(self.getDn())[0]

	def getBase(self):
		return self.__base

	def isBase(self):
		return access.compare_dn(self.getDn(), self.getBase())

	def getDomain(self):
		if not self.__indomain or self.getDn() == self.getBase():
			return self.getBase()
		dn = []
		for part in ldap.dn.str2dn(self.getDn())[::-1]:
			if not any('dc' == y[0] for y in part):
				break
			dn.append(part)
		return ldap.dn.dn2str(dn[::-1])

	def getDomainConfigBase(self):
		return 'cn=univention,' + self.getDomain()

	def isDomain(self):
		return self.getDn() == self.getDomain()

	def getLoginDomain(self):
		return self.__loginDomain

	def __getPositionInDomain(self):
		components = explodeDn(self.__pos, 0)
		components.reverse()
		poscomponents = []
		for i in components:
			mytype, ign = string.split(i, '=')
			if mytype != 'dc':
				poscomponents.append(i)
		poscomponents.reverse()
		positionindomain = string.join(poscomponents, ',')
		return positionindomain

	def switchToParent(self):
		if self.isBase():
			return False
		self.__setPosition(ldap.dn.dn2str(ldap.dn.str2dn(self.__pos)[1:]))
		return True

	def getPrintable(self, short=1, long=0, trailingslash=1):
		domaincomponents = explodeDn(self.getDomain(), 1)
		domain = string.join(domaincomponents, '.')
		indomaindn = self.__getPositionInDomain()
		if indomaindn:
			components = explodeDn(indomaindn, 1)
			components.reverse()
			if not short or long:
				printable = domain + ':/' + string.join(components, '/')
				if trailingslash:
					printable += '/'
			else:
				printable = ""
				for i in range(len(components)):
					printable += "&nbsp;&nbsp;"
				printable += components.pop()
		else:
			printable = domain
		return printable

	# new "version" of getPrintable, returns the tree-depth as int instead of html-blanks
	def getPrintable_depth(self, short=1, long=0, trailingslash=1):
		domaincomponents = explodeDn(self.getDomain(), 1)
		domain = string.join(domaincomponents, '.')
		indomaindn = self.__getPositionInDomain()
		depth = 0
		if indomaindn:
			components = explodeDn(indomaindn, 1)
			components.reverse()
			if not short or long:
				printable = domain + ':/' + string.join(components, '/')
				if trailingslash:
					printable += '/'
			else:
				printable = ""
				depth = len(components) * 2
				printable += components.pop()
		else:
			printable = domain
		return (printable, depth)


class access:

	@property
	def binddn(self):
		return self.lo.binddn

	@property
	def bindpw(self):
		return self.lo.bindpw

	@property
	def host(self):
		return self.lo.host

	@property
	def port(self):
		return self.lo.port

	@property
	def base(self):
		return self.lo.base

	@property
	def start_tls(self):
		return self.lo.start_tls

	def __init__(self, host='localhost', port=None, base='', binddn='', bindpw='', start_tls=2, lo=None, follow_referral=False):
		if lo:
			self.lo = lo
		else:
			if not port:
				port = int(configRegistry.get('ldap/server/port', 7389))
			try:
				self.lo = univention.uldap.access(host, port, base, binddn, bindpw, start_tls, follow_referral=follow_referral)
			except ldap.INVALID_CREDENTIALS:
				raise univention.admin.uexceptions.authFail(_("Authentication failed"))
			except ldap.UNWILLING_TO_PERFORM:
				raise univention.admin.uexceptions.authFail(_("Authentication failed"))
		self.require_license = 0
		self.allow_modify = 1
		self.licensetypes = ['UCS']

	def bind(self, binddn, bindpw):
		try:
			self.lo.bind(binddn, bindpw)
		except ldap.INVALID_CREDENTIALS:
			raise univention.admin.uexceptions.authFail(_("Authentication failed"))
		except ldap.UNWILLING_TO_PERFORM:
			raise univention.admin.uexceptions.authFail(_("Authentication failed"))
		self.__require_licence()

	def bind_saml(self, bindpw):
		try:
			return self.lo.bind_saml(bindpw)
		except (ldap.INVALID_CREDENTIALS, ldap.UNWILLING_TO_PERFORM):
			raise univention.admin.uexceptions.authFail(_("Authentication failed"))
		self.__require_licence()

	def __require_licence(self):
		if self.require_license:
			res = univention.admin.license.init_select(self.lo, 'admin')

			self.licensetypes = univention.admin.license._license.types

			if res == 1:
				self.allow_modify = 0
				raise univention.admin.uexceptions.licenseClients
			elif res == 2:
				self.allow_modify = 0
				raise univention.admin.uexceptions.licenseAccounts
			elif res == 3:
				self.allow_modify = 0
				raise univention.admin.uexceptions.licenseDesktops
			elif res == 4:
				self.allow_modify = 0
				raise univention.admin.uexceptions.licenseGroupware
			elif res == 5:
				# Free for personal use edition
				raise univention.admin.uexceptions.freeForPersonalUse
			# License Version 2:
			elif res == 6:
				self.allow_modify = 0
				raise univention.admin.uexceptions.licenseUsers
			elif res == 7:
				self.allow_modify = 0
				raise univention.admin.uexceptions.licenseServers
			elif res == 8:
				self.allow_modify = 0
				raise univention.admin.uexceptions.licenseManagedClients
			elif res == 9:
				self.allow_modify = 0
				raise univention.admin.uexceptions.licenseCorporateClients
			elif res == 10:
				self.allow_modify = 0
				raise univention.admin.uexceptions.licenseDVSUsers
			elif res == 11:
				self.allow_modify = 0
				raise univention.admin.uexceptions.licenseDVSClients

	def unbind(self):
		self.lo.unbind()

	def whoami(self):
		dn = self.lo.lo.whoami_s()
		return re.sub('^dn:', '', dn)

	def requireLicense(self, require=1):
		self.require_license = require

	def _validateLicense(self):
		if self.require_license:
			univention.admin.license.select('admin')

	def get_schema(self):
		if not hasattr(self.lo, 'get_schema'):  # introduced in UCS 4.1-2 erratum. can be removed in the future
			return ldap.schema.SubSchema(self.lo.lo.read_subschemasubentry_s(self.lo.lo.search_subschemasubentry_s()), 0)
		return self.lo.get_schema()

	@classmethod
	def compare_dn(cls, a, b):
		return univention.uldap.access.compare_dn(a, b)

	def get(self, dn, attr=[], required=False, exceptions=False):
		return self.lo.get(dn, attr, required)

	def getAttr(self, dn, attr, required=False, exceptions=False):
		return self.lo.getAttr(dn, attr, required)

	def search(self, filter='(objectClass=*)', base='', scope='sub', attr=[], unique=False, required=False, timeout=-1, sizelimit=0):
		try:
			return self.lo.search(filter, base, scope, attr, unique, required, timeout, sizelimit)
		except ldap.NO_SUCH_OBJECT as msg:
			raise univention.admin.uexceptions.noObject(_err2str(msg))
		except ldap.INAPPROPRIATE_MATCHING as msg:
			raise univention.admin.uexceptions.insufficientInformation(_err2str(msg))
		except (ldap.TIMEOUT, ldap.TIMELIMIT_EXCEEDED) as msg:
			raise univention.admin.uexceptions.ldapTimeout(_err2str(msg))
		except (ldap.SIZELIMIT_EXCEEDED, ldap.ADMINLIMIT_EXCEEDED) as msg:
			raise univention.admin.uexceptions.ldapSizelimitExceeded(_err2str(msg))
		except ldap.FILTER_ERROR as msg:
			raise univention.admin.uexceptions.ldapError('%s: %s' % (_err2str(msg), filter))
		except ldap.INVALID_DN_SYNTAX as msg:
			raise univention.admin.uexceptions.ldapError('%s: %s' % (_err2str(msg), base), original_exception=msg)
		except ldap.LDAPError as msg:
			raise univention.admin.uexceptions.ldapError(_err2str(msg), original_exception=msg)

	def searchDn(self, filter='(objectClass=*)', base='', scope='sub', unique=False, required=False, timeout=-1, sizelimit=0):
		try:
			return self.lo.searchDn(filter, base, scope, unique, required, timeout, sizelimit)
		except ldap.NO_SUCH_OBJECT as msg:
			raise univention.admin.uexceptions.noObject(_err2str(msg))
		except ldap.INAPPROPRIATE_MATCHING as msg:
			raise univention.admin.uexceptions.insufficientInformation(_err2str(msg))
		except (ldap.TIMEOUT, ldap.TIMELIMIT_EXCEEDED) as msg:
			raise univention.admin.uexceptions.ldapTimeout(_err2str(msg))
		except (ldap.SIZELIMIT_EXCEEDED, ldap.ADMINLIMIT_EXCEEDED) as msg:
			raise univention.admin.uexceptions.ldapSizelimitExceeded(_err2str(msg))
		except ldap.FILTER_ERROR as msg:
			raise univention.admin.uexceptions.ldapError('%s: %s' % (_err2str(msg), filter))
		except ldap.INVALID_DN_SYNTAX as msg:
			raise univention.admin.uexceptions.ldapError('%s: %s' % (_err2str(msg), base), original_exception=msg)
		except ldap.LDAPError as msg:
			raise univention.admin.uexceptions.ldapError(_err2str(msg), original_exception=msg)

	def getPolicies(self, dn, policies=None, attrs=None, result=None, fixedattrs=None):
		univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'getPolicies modules dn %s result' % dn)
		return self.lo.getPolicies(dn, policies, attrs, result, fixedattrs)

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
		except ldap.ALREADY_EXISTS as msg:
			univention.debug.debug(univention.debug.LDAP, univention.debug.ALL, 'add dn=%s err=%s' % (dn, msg))
			raise univention.admin.uexceptions.objectExists(dn)
		except ldap.INSUFFICIENT_ACCESS as msg:
			univention.debug.debug(univention.debug.LDAP, univention.debug.ALL, 'add dn=%s err=%s' % (dn, msg))
			raise univention.admin.uexceptions.permissionDenied
		except ldap.INVALID_DN_SYNTAX as msg:
			raise univention.admin.uexceptions.ldapError('%s: %s' % (_err2str(msg), dn), original_exception=msg)
		except ldap.LDAPError as msg:
			univention.debug.debug(univention.debug.LDAP, univention.debug.ALL, 'add dn=%s err=%s' % (dn, msg))
			raise univention.admin.uexceptions.ldapError(_err2str(msg), original_exception=msg)

	def modify(self, dn, changes, exceptions=False, ignore_license=0):
		self._validateLicense()
		if not self.allow_modify and not ignore_license:
			univention.debug.debug(univention.debug.ADMIN, univention.debug.ERROR, 'modify dn: %s' % dn)
			raise univention.admin.uexceptions.licenseDisableModify
			return []
		univention.debug.debug(univention.debug.LDAP, univention.debug.ALL, 'mod dn=%s ml=%s' % (dn, changes))
		if exceptions:
			return self.lo.modify(dn, changes)
		try:
			return self.lo.modify(dn, changes)
		except ldap.NO_SUCH_OBJECT as msg:
			univention.debug.debug(univention.debug.LDAP, univention.debug.ALL, 'mod dn=%s err=%s' % (dn, msg))
			raise univention.admin.uexceptions.noObject(dn)
		except ldap.INSUFFICIENT_ACCESS as msg:
			univention.debug.debug(univention.debug.LDAP, univention.debug.ALL, 'mod dn=%s err=%s' % (dn, msg))
			raise univention.admin.uexceptions.permissionDenied
		except ldap.INVALID_DN_SYNTAX as msg:
			raise univention.admin.uexceptions.ldapError('%s: %s' % (_err2str(msg), dn), original_exception=msg)
		except ldap.LDAPError as msg:
			univention.debug.debug(univention.debug.LDAP, univention.debug.ALL, 'mod dn=%s err=%s' % (dn, msg))
			raise univention.admin.uexceptions.ldapError(_err2str(msg), original_exception=msg)

	def rename(self, dn, newdn, move_childs=0, ignore_license=False):
		if not move_childs == 0:
			raise univention.admin.uexceptions.noObject(_("Moving children is not supported."))
		self._validateLicense()
		if not self.allow_modify and not ignore_license:
			univention.debug.debug(univention.debug.ADMIN, univention.debug.WARN, 'move dn: %s' % dn)
			raise univention.admin.uexceptions.licenseDisableModify
			return []
		univention.debug.debug(univention.debug.LDAP, univention.debug.ALL, 'ren dn=%s newdn=%s' % (dn, newdn))
		try:
			return self.lo.rename(dn, newdn)
		except ldap.NO_SUCH_OBJECT as msg:
			univention.debug.debug(univention.debug.LDAP, univention.debug.ALL, 'ren dn=%s err=%s' % (dn, msg))
			raise univention.admin.uexceptions.noObject(dn)
		except ldap.INSUFFICIENT_ACCESS as msg:
			univention.debug.debug(univention.debug.LDAP, univention.debug.ALL, 'ren dn=%s err=%s' % (dn, msg))
			raise univention.admin.uexceptions.permissionDenied
		except ldap.INVALID_DN_SYNTAX as msg:
			raise univention.admin.uexceptions.ldapError('%s: %s' % (_err2str(msg), dn), original_exception=msg)
		except ldap.LDAPError as msg:
			univention.debug.debug(univention.debug.LDAP, univention.debug.ALL, 'ren dn=%s err=%s' % (dn, msg))
			raise univention.admin.uexceptions.ldapError(_err2str(msg), original_exception=msg)

	def delete(self, dn, exceptions=False):
		self._validateLicense()
		if exceptions:
			try:
				return self.lo.delete(dn)
			except ldap.INSUFFICIENT_ACCESS as msg:
				raise univention.admin.uexceptions.permissionDenied
		univention.debug.debug(univention.debug.LDAP, univention.debug.ALL, 'del dn=%s' % (dn,))
		try:
			return self.lo.delete(dn)
		except ldap.NO_SUCH_OBJECT as msg:
			univention.debug.debug(univention.debug.LDAP, univention.debug.ALL, 'del dn=%s err=%s' % (dn, msg))
			raise univention.admin.uexceptions.noObject(dn)
		except ldap.INSUFFICIENT_ACCESS as msg:
			univention.debug.debug(univention.debug.LDAP, univention.debug.ALL, 'del dn=%s err=%s' % (dn, msg))
			raise univention.admin.uexceptions.permissionDenied
		except ldap.INVALID_DN_SYNTAX as msg:
			raise univention.admin.uexceptions.ldapError('%s: %s' % (_err2str(msg), dn), original_exception=msg)
		except ldap.LDAPError as msg:
			univention.debug.debug(univention.debug.LDAP, univention.debug.ALL, 'del dn=%s err=%s' % (dn, msg))
			raise univention.admin.uexceptions.ldapError(_err2str(msg), original_exception=msg)

	def parentDn(self, dn):
		return self.lo.parentDn(dn)

	def explodeDn(self, dn, notypes=0):
		return self.lo.explodeDn(dn, notypes)
