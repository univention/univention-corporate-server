# -*- coding: utf-8 -*-
"""
|UDM| wrapper around :py:mod:`univention.uldap` that replaces exceptions.
"""
# Copyright 2004-2019 Univention GmbH
#
# https://www.univention.de/
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
# <https://www.gnu.org/licenses/>.

from __future__ import absolute_import

import re
import ldap
import string
import time

import univention.debug as ud
import univention.uldap
from univention.admin import localization
import univention.config_registry
import univention.admin.license
try:
	from typing import Any, Dict, List, Optional, Tuple, Union  # noqa F401
except ImportError:
	pass

translation = localization.translation('univention/admin')
_ = translation.translate

configRegistry = univention.config_registry.ConfigRegistry()
configRegistry.load()

explodeDn = univention.uldap.explodeDn


class DN(object):
	"""
	A |LDAP| Distinguished Name.
	"""

	def __init__(self, dn):
		# type: (str) -> None
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
	# type: (str, Optional[int], Optional[str]) -> str
	"""
	Return the naming context of the LDAP server.

	:param str host: The hostname of the LDAP server.
	:param int port: The TCP port number of the LDAP server.
	:param str uri: A complete LDAP URI.
	:returns: The distinguished name of the LDAP root.
	:rtype: str
	"""
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
	# type: (int, List[str]) -> Tuple[univention.admin.uldap.access, univention.admin.uldap.position]
	"""
	Open a LDAP connection using the admin credentials.

	:param int start_tls: Negotiate TLS with server. If `2` is given, the command will require the operation to be successful.
	:param decode_ignorelist: List of LDAP attribute names which shall be handled as binary attributes.
	:type decode_ignorelist: list[str]
	:return: A 2-tuple (LDAP-access, LDAP-position)
	:rtype: tuple[univention.admin.uldap.access, univention.admin.uldap.position]
	"""
	lo = univention.uldap.getAdminConnection(start_tls, decode_ignorelist=decode_ignorelist)
	pos = position(lo.base)
	return access(lo=lo), pos


def getMachineConnection(start_tls=2, decode_ignorelist=[], ldap_master=True):
	# type: (int, List[str], bool) -> Tuple[univention.admin.uldap.access, univention.admin.uldap.position]
	"""
	Open a LDAP connection using the machine credentials.

	:param int start_tls: Negotiate TLS with server. If `2` is given, the command will require the operation to be successful.
	:param decode_ignorelist: List of LDAP attribute names which shall be handled as binary attributes.
	:type decode_ignorelist: list[str]
	:param bool ldap_master: Open a connection to the Master if True, to the preferred LDAP server otherwise.
	:return: A 2-tuple (LDAP-access, LDAP-position)
	:rtype: tuple[univention.admin.uldap.access, univention.admin.uldap.position]
	"""
	lo = univention.uldap.getMachineConnection(start_tls, decode_ignorelist=decode_ignorelist, ldap_master=ldap_master)
	pos = position(lo.base)
	return access(lo=lo), pos


def _err2str(err):
	# type: (Exception) -> str
	"""
	Convert exception arguments to string.

	:param Exception err: An exception instance.
	:returns: A concatenated string formatted from the exception
	:rtype: str
	"""
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
	"""
	A |UDM| domain name.
	"""

	def __init__(self, lo, position):
		# type: (univention.admin.uldap.access, univention.admin.uldap.position) -> None
		"""
		:param univention.admin.uldap.access lo: A LDAP connection object.
		:param univention.admin.uldap.position position: A UDM position specifying the LDAP base container.
		"""
		self.lo = lo
		self.position = position
		self.domain = self.lo.get(self.position.getDomain(), attr=['sambaDomain', 'sambaSID', 'krb5RealmName'])

	def getKerberosRealm(self):
		# type: () -> Optional[str]
		"""
		Return the name of the Kerberos realms.

		:returns: The name of the Kerberos realm.
		:rtype: str
		"""
		return self.domain.get('krb5RealmName', [None])[0]


class position:
	"""
	The position of a |LDAP| container.
	Supports relative distinguished names.
	"""

	def __init__(self, base, loginDomain=''):
		# type: (str, str) -> None
		"""
		:param str base: The base distinguished name.
		:param str loginDomain: The login domain name.
		"""
		if not base:
			raise univention.admin.uexceptions.insufficientInformation(_("There was no LDAP base specified."))

		self.__loginDomain = loginDomain or base
		self.__base = base
		self.__pos = ""
		self.__indomain = False

	def setBase(self, base):
		# type: (str) -> None
		"""
		Set a new base distinguished name.

		:param str base: The new base distinguished name.
		"""
		self.__base = base

	def setLoginDomain(self, loginDomain):
		# type: (str) -> None
		"""
		Set a new login domain name.

		:param str loginDomain: The new login domain name.
		"""
		self.__loginDomain = loginDomain

	def __setPosition(self, pos):
		# type: (str) -> None
		self.__pos = pos
		self.__indomain = any('dc' == y[0] for x in ldap.dn.str2dn(self.__pos) for y in x)

	def getDn(self):
		# type: () -> str
		"""
		Return the distinguished name.

		:returns: The absolute DN.
		:rtype: str
		"""
		return ldap.dn.dn2str(ldap.dn.str2dn(self.__pos) + ldap.dn.str2dn(self.__base))

	def setDn(self, dn):
		# type: (str) -> None
		"""
		Set a new distinguished name.

		:param str dn: The new distinguished name.
		"""
		# strip out the trailing base from the DN; store relative dn
		dn = ldap.dn.str2dn(dn)
		base = ldap.dn.str2dn(self.getBase())
		if dn[-len(base):] == base:
			dn = dn[:-len(base)]
		self.__setPosition(ldap.dn.dn2str(dn))

	def getRdn(self):
		# type: () -> str
		"""
		Return the distinguished name relative to the LDAP base.

		:returns: The relative DN.
		:rtype: str
		"""
		return ldap.dn.explode_rdn(self.getDn())[0]

	def getBase(self):
		# type: () -> str
		"""
		Return the LDAP base DN.

		:returns: The distinguished name of the LDAP base.
		:rtype: str
		"""
		return self.__base

	def isBase(self):
		# type: () -> bool
		"""
		Check if the position equals the LDAP base DN.

		:returns: True if the position equals the base DN, False otherwise.
		:rtype: bool
		"""
		return access.compare_dn(self.getDn(), self.getBase())

	def getDomain(self):
		# type: () -> str
		"""
		Return the distinguished name of the domain part of the position.

		:returns: The distinguished name.
		:rtype: str
		"""
		if not self.__indomain or self.getDn() == self.getBase():
			return self.getBase()
		dn = []
		for part in ldap.dn.str2dn(self.getDn())[::-1]:
			if not any('dc' == y[0] for y in part):
				break
			dn.append(part)
		return ldap.dn.dn2str(dn[::-1])

	def getDomainConfigBase(self):
		# type: () -> str
		"""
		Return the distinguished name of the configuration container.

		:returns: The distinguished name.
		:rtype: str
		"""
		return 'cn=univention,' + self.getDomain()

	def isDomain(self):
		# type: () -> bool
		"""
		Check if the position equals the domain DN.

		:returns: True if the position equals the domain DN, False otherwise.
		:rtype: bool
		"""
		return self.getDn() == self.getDomain()

	def getLoginDomain(self):
		# type: () -> str
		"""
		Return the login domain name.

		:returns: The login domain name.
		:rtype: str
		"""
		return self.__loginDomain

	def __getPositionInDomain(self):
		# type: () -> str
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
		# type: () -> bool
		"""
		Switch position to parent container.

		:returns: False if already at the Base, True otherwise.
		:rtype: bool
		"""
		if self.isBase():
			return False
		self.__setPosition(ldap.dn.dn2str(ldap.dn.str2dn(self.__pos)[1:]))
		return True

	def getPrintable(self, short=1, long=0, trailingslash=1):
		# type: (int, int, int) -> str
		"""
		Return printable path of position.

		:param int short: `0` to prefix path with domain.
		:param int long: `1` to prefix path with domain.
		:param int trailingslash: Append trailing slash.
		:returns: A string.
		:rtype: str

		.. deprecated:: 4.3
			Unused.
		"""
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

	def getPrintable_depth(self, short=1, long=0, trailingslash=1):
		# type: (int, int, int) -> Tuple[str, int]
		"""
		Return printable path of position.
		new "version" of :py:meth:`getPrintable`, returns the tree-depth as int instead of html-blanks

		:param int short: `0` to prefix path with domain.
		:param int long: `1` to prefix path with domain.
		:param int trailingslash: Append trailing slash.
		:returns: A 2-tuple (printable, depth)
		:rtype: tuple[str, int]

		.. deprecated:: 4.3
			Unused.
		"""
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
	"""
	A |UDM| class to access a |LDAP| server.
	"""

	@property
	def binddn(self):
		# type: () -> Optional[str]
		"""
		Return the distinguished name of the account.

		:returns: The distinguished name of the account (or `None` with |SAML|).
		:rtype: str
		"""
		return self.lo.binddn

	@property
	def bindpw(self):
		# type: () -> str
		"""
		Return the user password or credentials.

		:returns: The user password or credentials.
		:rtype: str
		"""
		return self.lo.bindpw

	@property
	def host(self):
		# type: () -> str
		"""
		Return the host name of the LDAP server.

		:returns: the host name of the LDAP server.
		:rtype: str
		"""
		return self.lo.host

	@property
	def port(self):
		# type: () -> int
		"""
		Return the TCP port number of the LDAP server.

		:returns: the TCP port number of the LDAP server.
		:rtype: int
		"""
		return self.lo.port

	@property
	def base(self):
		# type: () -> str
		"""
		Return the LDAP base of the LDAP server.

		:returns: the LDAP base of the LDAP server.
		:rtype: str
		"""
		return self.lo.base

	@property
	def start_tls(self):
		# type: () -> int
		return self.lo.start_tls

	def __init__(self, host='localhost', port=None, base='', binddn='', bindpw='', start_tls=2, lo=None, follow_referral=False):
		# type: (str, int, str, str, str, int, univention.uldap.access, bool) -> None
		"""
		:param str host: The hostname of the |LDAP| server.
		:param int port: The |TCP| port number of the |LDAP| server.
		:param str base: The base distinguished name.
		:param str binddn: The distinguished name of the account.
		:param str bindpw: The user password for simple authentication.
		:param int start_tls: Negotiate |TLS| with server. If `2` is given, the command will require the operation to be successful.
		:param univention.uldap.access lo: |LDAP| connection.
		:param:bool follow_referral: Follow |LDAP| referrals.
		"""
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
		# type: (str, str) -> None
		"""
		Do simple LDAP bind using DN and password.

		:param str binddn: The distinguished name of the account.
		:param str bindpw: The user password for simple authentication.
		"""
		try:
			self.lo.bind(binddn, bindpw)
		except ldap.INVALID_CREDENTIALS:
			raise univention.admin.uexceptions.authFail(_("Authentication failed"))
		except ldap.UNWILLING_TO_PERFORM:
			raise univention.admin.uexceptions.authFail(_("Authentication failed"))
		self.__require_licence()

	def bind_saml(self, bindpw):
		# type: (str) -> None
		"""
		Do LDAP bind using SAML message.

		:param str bindpw: The SAML authentication cookie.
		"""
		try:
			return self.lo.bind_saml(bindpw)
		except (ldap.INVALID_CREDENTIALS, ldap.UNWILLING_TO_PERFORM):
			raise univention.admin.uexceptions.authFail(_("Authentication failed"))
		self.__require_licence()

	def __require_licence(self):
		# type: () -> None
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
		# type: () -> None
		"""
		Unauthenticate.
		"""
		self.lo.unbind()

	def whoami(self):
		# type: () -> str
		"""
		Return the distinguished name of the authenticated user.

		:returns: The distinguished name.
		:rtype: str
		"""
		dn = self.lo.lo.whoami_s()
		return re.sub('^dn:', '', dn)

	def requireLicense(self, require=1):
		# type: (int) -> None
		"""
		Enable or disable the UCS licence check.

		:param int require: `1` to require a valid licence.
		"""
		self.require_license = require

	def _validateLicense(self):
		# type: () -> None
		"""
		Check if the UCS licence is valid.
		"""
		if self.require_license:
			univention.admin.license.select('admin')

	def get_schema(self):
		# type: () -> ldap.schema.subentry.SubSchema
		"""
		Retrieve |LDAP| schema information from |LDAP| server.

		:returns: The |LDAP| schema.
		:rtype: ldap.schema.subentry.SubSchema
		"""
		if not hasattr(self.lo, 'get_schema'):  # introduced in UCS 4.1-2 erratum. can be removed in the future
			return ldap.schema.SubSchema(self.lo.lo.read_subschemasubentry_s(self.lo.lo.search_subschemasubentry_s()), 0)
		return self.lo.get_schema()

	@classmethod
	def compare_dn(cls, a, b):
		# type: (str, str) -> bool
		"""
		Compare two distinguished names for equality.

		:param str a: The first distinguished name.
		:param str b: A second distinguished name.
		:returns: True if the DNs are the same, False otherwise.
		:rtype: bool
		"""
		return univention.uldap.access.compare_dn(a, b)

	def get(self, dn, attr=[], required=False, exceptions=False):
		# type: (str, List[str], bool, bool) -> Dict[str, List[str]]
		"""
		Return multiple attributes of a single LDAP object.

		:param str dn: The distinguished name of the object to lookup.
		:param attr: The list of attributes to fetch.
		:param bool required: Raise an exception instead of returning an empty dictionary.
		:param bool exceptions: Ignore.
		:returns: A dictionary mapping the requested attributes to a list of their values.
		:rtype: dict[str, list[str]]
		:raises ldap.NO_SUCH_OBJECT: If the LDAP object is not accessible.
		"""
		return self.lo.get(dn, attr, required)

	def getAttr(self, dn, attr, required=False, exceptions=False):
		# type: (str, str, bool, bool) -> List[str]
		"""
		Return a single attribute of a single LDAP object.

		:param str dn: The distinguished name of the object to lookup.
		:param str attr: The attribute to fetch.
		:param bool required: Raise an exception instead of returning an empty dictionary.
		:param bool exceptions: Ignore.
		:returns: A list of values.
		:rtype: list[str]
		:raises ldap.NO_SUCH_OBJECT: If the LDAP object is not accessible.
		"""
		return self.lo.getAttr(dn, attr, required)

	def search(self, filter='(objectClass=*)', base='', scope='sub', attr=[], unique=False, required=False, timeout=-1, sizelimit=0, serverctrls=None, response=None):
		# type: (str, str, str, List[str], bool, bool, int, int) -> List[Tuple[str, Dict[str, List[str]]]]
		"""
		Perform LDAP search and return values.

		:param str filter: LDAP search filter.
		:param str base: the starting point for the search.
		:param str scope: Specify the scope of the search to be one of `base`, `base+one`, `one`, `sub`, or `domain` to specify a base object, base plus one-level, one-level, subtree, or children search.
		:param attr: The list of attributes to fetch.
		:type attr: list[str]
		:param bool unique: Raise an exception if more than one object matches.
		:param bool required: Raise an exception instead of returning an empty dictionary.
		:param int timeout: wait at most `timeout` seconds for a search to complete. `-1` for no limit.
		:param int sizelimit: retrieve at most `sizelimit` entries for a search. `0` for no limit.
		:param serverctrls: a list of ldap.controls.LDAPControl instances sent to the server along with the LDAP request
		:type serverctrls: list[ldap.controls.LDAPControl]
		:param dict response: An optional dictionary to receive the server controls of the result.
		:returns: A list of 2-tuples (dn, values) for each LDAP object, where values is a dictionary mapping attribute names to a list of values.
		:rtype: list[tuple[str, dict[str, list[str]]]]
		:raises univention.admin.uexceptions.noObject: Indicates the target object cannot be found.
		:raises univention.admin.uexceptions.insufficientInformation: Indicates that the matching rule specified in the search filter does not match a rule defined for the attribute's syntax.
		:raises univention.admin.uexceptions.ldapTimeout: Indicates that the time limit of the LDAP client was exceeded while waiting for a result.
		:raises univention.admin.uexceptions.ldapSizelimitExceeded: Indicates that in a search operation, the size limit specified by the client or the server has been exceeded.
		:raises univention.admin.uexceptions.ldapError: Indicates that the search method was called with an invalid search filter.
		:raises univention.admin.uexceptions.ldapError: Indicates that the syntax of the DN is incorrect.
		:raises univention.admin.uexceptions.ldapError: on any other LDAP error.
		"""
		try:
			return self.lo.search(filter, base, scope, attr, unique, required, timeout, sizelimit, serverctrls=serverctrls, response=response)
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

	def searchDn(self, filter='(objectClass=*)', base='', scope='sub', unique=False, required=False, timeout=-1, sizelimit=0, serverctrls=None, response=None):
		# type: (str, str, str, bool, bool, int, int) -> List[str]
		"""
		Perform LDAP search and return distinguished names only.

		:param str filter: LDAP search filter.
		:param str base: the starting point for the search.
		:param str scope: Specify the scope of the search to be one of `base`, `base+one`, `one`, `sub`, or `domain` to specify a base object, base plus one-level, one-level, subtree, or children search.
		:param bool unique: Raise an exception if more than one object matches.
		:param bool required: Raise an exception instead of returning an empty dictionary.
		:param int timeout: wait at most timeout seconds for a search to complete. `-1` for no limit.
		:param int sizelimit: retrieve at most sizelimit entries for a search. `0` for no limit.
		:param serverctrls: a list of :py:class:`ldap.controls.LDAPControl` instances sent to the server along with the LDAP request.
		:type serverctrls: list[ldap.controls.LDAPControl]
		:param dict response: An optional dictionary to receive the server controls of the result.
		:returns: A list of distinguished names.
		:rtype: list[str]
		:raises univention.admin.uexceptions.noObject: Indicates the target object cannot be found.
		:raises univention.admin.uexceptions.insufficientInformation: Indicates that the matching rule specified in the search filter does not match a rule defined for the attribute's syntax.
		:raises univention.admin.uexceptions.ldapTimeout: Indicates that the time limit of the LDAP client was exceeded while waiting for a result.
		:raises univention.admin.uexceptions.ldapSizelimitExceeded: Indicates that in a search operation, the size limit specified by the client or the server has been exceeded.
		:raises univention.admin.uexceptions.ldapError: Indicates that the search method was called with an invalid search filter.
		:raises univention.admin.uexceptions.ldapError: Indicates that the syntax of the DN is incorrect.
		:raises univention.admin.uexceptions.ldapError: on any other LDAP error.
		"""
		try:
			return self.lo.searchDn(filter, base, scope, unique, required, timeout, sizelimit, serverctrls=serverctrls, response=response)
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
		# type: (str, Optional[List[str]], Optional[Dict[str, List[Any]]], Any, Any) -> Dict[str, Dict[str, Any]]
		"""
		Return |UCS| policies for |LDAP| entry.

		:param str dn: The distinguished name of the |LDAP| entry.
		:param list policies: List of policy object classes...
		:param dict attrs: |LDAP| attributes. If not given, the data is fetched from LDAP.
		:param result: UNUSED!
		:param fixedattrs: UNUSED!
		:returns: A mapping of policy names to
		"""
		ud.debug(ud.ADMIN, ud.INFO, 'getPolicies modules dn %s result' % dn)
		return self.lo.getPolicies(dn, policies, attrs, result, fixedattrs)

	def add(self, dn, al, exceptions=False, serverctrls=None, response=None):
		# type: (str, List[Tuple], bool, Optional[List[ldap.controls.LDAPControl]], Optional[Dict]) -> None
		"""
		Add LDAP entry at distinguished name and attributes in add_list=(attribute-name, old-values. new-values) or (attribute-name, new-values).

		:param str dn: The distinguished name of the object to add.
		:param al: The add-list of 2-tuples (attribute-name, new-values).
		:param bool exceptions: Raise the low level exception instead of the wrapping UDM exceptions.
		:param serverctrls: a list of ldap.controls.LDAPControl instances sent to the server along with the LDAP request
		:type serverctrls: list[ldap.controls.LDAPControl]
		:param dict response: An optional dictionary to receive the server controls of the result.
		:raises univention.admin.uexceptions.licenseDisableModify: if the UCS licence prohibits any modificcation
		:raises univention.admin.uexceptions.objectExists: if the LDAP object already exists.
		:raises univention.admin.uexceptions.permissionDenied: if the user does not have the required permissions.
		:raises univention.admin.uexceptions.ldapError: if the syntax of the DN is invalid.
		:raises univention.admin.uexceptions.ldapError: on any other LDAP error.
		"""
		self._validateLicense()
		if not self.allow_modify:
			ud.debug(ud.ADMIN, ud.ERROR, 'add dn: %s' % dn)
			raise univention.admin.uexceptions.licenseDisableModify
			return []
		ud.debug(ud.LDAP, ud.ALL, 'add dn=%s al=%s' % (dn, al))
		if exceptions:
			return self.lo.add(dn, al, serverctrls=serverctrls, response=response)
		try:
			return self.lo.add(dn, al, serverctrls=serverctrls, response=response)
		except ldap.ALREADY_EXISTS as msg:
			ud.debug(ud.LDAP, ud.ALL, 'add dn=%s err=%s' % (dn, msg))
			raise univention.admin.uexceptions.objectExists(dn)
		except ldap.INSUFFICIENT_ACCESS as msg:
			ud.debug(ud.LDAP, ud.ALL, 'add dn=%s err=%s' % (dn, msg))
			raise univention.admin.uexceptions.permissionDenied
		except ldap.INVALID_DN_SYNTAX as msg:
			raise univention.admin.uexceptions.ldapError('%s: %s' % (_err2str(msg), dn), original_exception=msg)
		except ldap.LDAPError as msg:
			ud.debug(ud.LDAP, ud.ALL, 'add dn=%s err=%s' % (dn, msg))
			raise univention.admin.uexceptions.ldapError(_err2str(msg), original_exception=msg)

	def modify(self, dn, changes, exceptions=False, ignore_license=0, serverctrls=None, response=None):
		# type: (str, List[Tuple[str, Any, Any]], bool, int, Optional[List[ldap.controls.LDAPControl]], Optional[Dict]) -> str
		"""
		Modify LDAP entry DN with attributes in changes=(attribute-name, old-values, new-values).

		:param str dn: The distinguished name of the object to modify.
		:param changes: The modify-list of 3-tuples (attribute-name, old-values, new-values).
		:param bool exceptions: Raise the low level exception instead of the wrapping UDM exceptions.
		:param bool ignore_license: Ignore license check if True.
		:param serverctrls: a list of ldap.controls.LDAPControl instances sent to the server along with the LDAP request
		:type serverctrls: list[ldap.controls.LDAPControl]
		:param dict response: An optional dictionary to receive the server controls of the result.
		:returns: The distinguished name.
		:rtype: str
		"""
		self._validateLicense()
		if not self.allow_modify and not ignore_license:
			ud.debug(ud.ADMIN, ud.ERROR, 'modify dn: %s' % dn)
			raise univention.admin.uexceptions.licenseDisableModify
			return []
		ud.debug(ud.LDAP, ud.ALL, 'mod dn=%s ml=%s' % (dn, changes))
		if exceptions:
			return self.lo.modify(dn, changes, serverctrls=serverctrls, response=response)
		try:
			return self.lo.modify(dn, changes, serverctrls=serverctrls, response=response)
		except ldap.NO_SUCH_OBJECT as msg:
			ud.debug(ud.LDAP, ud.ALL, 'mod dn=%s err=%s' % (dn, msg))
			raise univention.admin.uexceptions.noObject(dn)
		except ldap.INSUFFICIENT_ACCESS as msg:
			ud.debug(ud.LDAP, ud.ALL, 'mod dn=%s err=%s' % (dn, msg))
			raise univention.admin.uexceptions.permissionDenied
		except ldap.INVALID_DN_SYNTAX as msg:
			raise univention.admin.uexceptions.ldapError('%s: %s' % (_err2str(msg), dn), original_exception=msg)
		except ldap.LDAPError as msg:
			ud.debug(ud.LDAP, ud.ALL, 'mod dn=%s err=%s' % (dn, msg))
			raise univention.admin.uexceptions.ldapError(_err2str(msg), original_exception=msg)

	def rename(self, dn, newdn, move_childs=0, ignore_license=False, serverctrls=None, response=None):
		# type: (str, str, int, bool, Optional[List[ldap.controls.LDAPControl]], Optional[Dict]) -> None
		"""
		Rename a LDAP object.

		:param str dn: The old distinguished name of the object to rename.
		:param str newdn: The new distinguished name of the object to rename.
		:param int move_childs: Also rename the sub children. Must be `0` always as `1` is not implemented.
		:param bool ignore_license: Ignore license check if True.
		:param serverctrls: a list of ldap.controls.LDAPControl instances sent to the server along with the LDAP request
		:type serverctrls: list[ldap.controls.LDAPControl]
		:param dict response: An optional dictionary to receive the server controls of the result.
		"""
		if not move_childs == 0:
			raise univention.admin.uexceptions.noObject(_("Moving children is not supported."))
		self._validateLicense()
		if not self.allow_modify and not ignore_license:
			ud.debug(ud.ADMIN, ud.WARN, 'move dn: %s' % dn)
			raise univention.admin.uexceptions.licenseDisableModify
			return []
		ud.debug(ud.LDAP, ud.ALL, 'ren dn=%s newdn=%s' % (dn, newdn))
		try:
			return self.lo.rename(dn, newdn, serverctrls=serverctrls, response=response)
		except ldap.NO_SUCH_OBJECT as msg:
			ud.debug(ud.LDAP, ud.ALL, 'ren dn=%s err=%s' % (dn, msg))
			raise univention.admin.uexceptions.noObject(dn)
		except ldap.INSUFFICIENT_ACCESS as msg:
			ud.debug(ud.LDAP, ud.ALL, 'ren dn=%s err=%s' % (dn, msg))
			raise univention.admin.uexceptions.permissionDenied
		except ldap.INVALID_DN_SYNTAX as msg:
			raise univention.admin.uexceptions.ldapError('%s: %s' % (_err2str(msg), dn), original_exception=msg)
		except ldap.LDAPError as msg:
			ud.debug(ud.LDAP, ud.ALL, 'ren dn=%s err=%s' % (dn, msg))
			raise univention.admin.uexceptions.ldapError(_err2str(msg), original_exception=msg)

	def delete(self, dn, exceptions=False):
		# type: (str, bool) -> None
		"""
		Delete a LDAP object.

		:param str dn: The distinguished name of the object to remove.
		:param bool exceptions: Raise the low level exception instead of the wrapping UDM exceptions.
		:raises univention.admin.uexceptions.noObject: if the object does not exist.
		:raises univention.admin.uexceptions.permissionDenied: if the user does not have the required permissions.
		:raises univention.admin.uexceptions.ldapError: if the syntax of the DN is invalid.
		:raises univention.admin.uexceptions.ldapError: on any other LDAP error.
		"""
		self._validateLicense()
		if exceptions:
			try:
				return self.lo.delete(dn)
			except ldap.INSUFFICIENT_ACCESS as msg:
				raise univention.admin.uexceptions.permissionDenied
		ud.debug(ud.LDAP, ud.ALL, 'del dn=%s' % (dn,))
		try:
			return self.lo.delete(dn)
		except ldap.NO_SUCH_OBJECT as msg:
			ud.debug(ud.LDAP, ud.ALL, 'del dn=%s err=%s' % (dn, msg))
			raise univention.admin.uexceptions.noObject(dn)
		except ldap.INSUFFICIENT_ACCESS as msg:
			ud.debug(ud.LDAP, ud.ALL, 'del dn=%s err=%s' % (dn, msg))
			raise univention.admin.uexceptions.permissionDenied
		except ldap.INVALID_DN_SYNTAX as msg:
			raise univention.admin.uexceptions.ldapError('%s: %s' % (_err2str(msg), dn), original_exception=msg)
		except ldap.LDAPError as msg:
			ud.debug(ud.LDAP, ud.ALL, 'del dn=%s err=%s' % (dn, msg))
			raise univention.admin.uexceptions.ldapError(_err2str(msg), original_exception=msg)

	def parentDn(self, dn):
		# type: (str) -> Optional[str]
		"""
		Return the parent container of a distinguished name.

		:param str dn: The distinguished name.
		:return: The parent distinguished name or None if the LDAP base is reached.
		:rtype: str or None
		"""
		return self.lo.parentDn(dn)

	def explodeDn(self, dn, notypes=0):
		# type: (str, int) -> List[str]
		"""
		Break up a DN into its component parts.

		:param str dn: The distinguished name.
		:param int notypes: Return only the component's attribute values if True. Also the attribute types if False.
		:return: A list of relative distinguished names.
		:rtype: list[str]
		"""
		return self.lo.explodeDn(dn, notypes)
