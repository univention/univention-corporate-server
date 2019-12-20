# -*- coding: utf-8 -*-
#
# Univention Python
#  LDAP access
#
# Copyright 2002-2019 Univention GmbH
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

import re
from functools import wraps

import six
import ldap
import ldap.schema
import ldap.sasl
from ldapurl import LDAPUrl
from ldapurl import isLDAPUrl

import univention.debug
from univention.config_registry import ConfigRegistry
try:
	from typing import Any, Dict, List, Optional, Set, Tuple, Union  # noqa
except ImportError:
	pass


def parentDn(dn, base=''):
	# type: (str, str) -> Optional[str]
	"""
	Return the parent container of a distinguished name.

	:param str dn: The distinguished name.
	:param str base: distinguished name where to stop.
	:return: The parent distinguished name or None.
	:rtype: str or None
	"""
	_d = univention.debug.function('uldap.parentDn dn=%s base=%s' % (dn, base))  # noqa F841
	if dn.lower() == base.lower():
		return None
	dn = ldap.dn.str2dn(dn)
	return ldap.dn.dn2str(dn[1:])


def explodeDn(dn, notypes=0):
	# type: (str, int) -> List[str]
	"""
	Break up a DN into its component parts.

	:param str dn: The distinguished name.
	:param int notypes: Return only the component's attribute values if True. Also the attribute types if False.
	:return: A list of relative distinguished names.
	:rtype: list[str]
	"""
	return ldap.dn.explode_dn(dn, notypes)


def getRootDnConnection(start_tls=2, decode_ignorelist=[], reconnect=True):
	# type: (int, List[str], bool) -> access
	"""
	Open a LDAP connection to the local LDAP server with the LDAP root account.

	:param int start_tls: Negotiate TLS with server. If `2` is given, the command will require the operation to be successful.
	:param decode_ignorelist: List of LDAP attribute names which shall be handled as binary attributes.
	:type decode_ignorelist: list[str]
	:param bool reconnect: Automatically reconect if the connection fails.
	:return: A LDAP access object.
	:rtype: univention.uldap.access
	"""
	ucr = ConfigRegistry()
	ucr.load()
	port = int(ucr.get('slapd/port', '7389').split(',')[0])
	host = ucr['hostname'] + '.' + ucr['domainname']
	if ucr.get('ldap/server/type', 'dummy') == 'master':
		bindpw = open('/etc/ldap.secret').read().rstrip('\n')
		binddn = 'cn=admin,{0}'.format(ucr['ldap/base'])
	else:
		bindpw = open('/etc/ldap/rootpw.conf').read().rstrip('\n').replace('rootpw "', '', 1)[:-1]
		binddn = 'cn=update,{0}'.format(ucr['ldap/base'])
	return access(host=host, port=port, base=ucr['ldap/base'], binddn=binddn, bindpw=bindpw, start_tls=start_tls, decode_ignorelist=decode_ignorelist, reconnect=reconnect)


def getAdminConnection(start_tls=2, decode_ignorelist=[], reconnect=True):
	# type: (int, List[str], bool) -> access
	"""
	Open a LDAP connection to the Master LDAP server using the admin credentials.

	:param int start_tls: Negotiate TLS with server. If `2` is given, the command will require the operation to be successful.
	:param decode_ignorelist: List of LDAP attribute names which shall be handled as binary attributes.
	:type decode_ignorelist: list[str]
	:param bool reconnect: Automatically reconect if the connection fails.
	:return: A LDAP access object.
	:rtype: univention.uldap.access
	"""
	ucr = ConfigRegistry()
	ucr.load()
	bindpw = open('/etc/ldap.secret').read().rstrip('\n')
	port = int(ucr.get('ldap/master/port', '7389'))
	return access(host=ucr['ldap/master'], port=port, base=ucr['ldap/base'], binddn='cn=admin,' + ucr['ldap/base'], bindpw=bindpw, start_tls=start_tls, decode_ignorelist=decode_ignorelist, reconnect=reconnect)


def getBackupConnection(start_tls=2, decode_ignorelist=[], reconnect=True):
	# type: (int, List[str], bool) -> access
	"""
	Open a LDAP connection to a Backup LDAP server using the admin credentials.

	:param int start_tls: Negotiate TLS with server. If `2` is given, the command will require the operation to be successful.
	:param decode_ignorelist: List of LDAP attribute names which shall be handled as binary attributes.
	:type decode_ignorelist: list[str]
	:param bool reconnect: Automatically reconect if the connection fails.
	:return: A LDAP access object.
	:rtype: univention.uldap.access
	"""
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
	# type: (int, List[str], bool, str, bool) -> access
	"""
	Open a LDAP connection using the machine credentials.

	:param int start_tls: Negotiate TLS with server. If `2` is given, the command will require the operation to be successful.
	:param decode_ignorelist: List of LDAP attribute names which shall be handled as binary attributes.
	:type decode_ignorelist: list[str]
	:param bool ldap_master: Open a connection to the Master if True, to the preferred LDAP server otherwise.
	:param str secret_file: The name of a file containing the password credentials.
	:param bool reconnect: Automatically reconect if the connection fails.
	:return: A LDAP access object.
	:rtype: univention.uldap.access
	"""
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


def _fix_reconnect_handling(func):
	# Bug #47926: python ldap does not reconnect on ldap.UNAVAILABLE
	# We need this until https://github.com/python-ldap/python-ldap/pull/267 is fixed
	@wraps(func)
	def _decorated(self, *args, **kwargs):
		if not self.reconnect:
			return func(self, *args, **kwargs)

		try:
			return func(self, *args, **kwargs)
		except ldap.INSUFFICIENT_ACCESS:
			if self.whoami():  # the connection is still bound and valid
				raise
			self._reconnect()
			return func(self, *args, **kwargs)
		except (ldap.UNAVAILABLE, ldap.CONNECT_ERROR, ldap.TIMEOUT):  # ldap.TIMELIMIT_EXCEEDED ?
			self._reconnect()
			return func(self, *args, **kwargs)

	return _decorated


class access(object):
	"""
	The low-level class to access a LDAP server.

	:param str host: host name of the LDAP server.
	:param int port: TCP port of the LDAP server. Defaults to 7389 or 7636.
	:param str base: LDAP base distinguished name.
	:param str binddn: Distinguished name for simple authentication.
	:param str bindpw: Password for simple authentication.
	:param int start_tls: 0=no, 1=try StartTLS, 2=require StartTLS.
	:param str ca_certfile: File name to CA certificate.
	:param decode_ignorelist: List of LDAP attribute names which shall be handled as binary attributes.
	:param use_ldaps bool: Connect to SSL port.
	:param uri str: LDAP connection string.
	:param follow_referral bool: Follow referrals and return result from other servers instead of returning the referral itself.
	:param reconnect bool: Automatically re-establish connection to LDAP server if connection breaks.
	"""

	def __init__(self, host='localhost', port=None, base='', binddn='', bindpw='', start_tls=2, ca_certfile=None, decode_ignorelist=[], use_ldaps=False, uri=None, follow_referral=False, reconnect=True):
		# type: (str, int, str, Optional[str], str, int, str, List, bool, str, bool, bool) -> None
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
		if six.PY3:
			return pwd
		if isinstance(pwd, unicode):  # noqa: F821
			return str(pwd)
		else:
			return pwd

	@_fix_reconnect_handling
	def bind(self, binddn, bindpw):
		# type: (str, str) -> None
		"""
		Do simple LDAP bind using DN and password.

		:param str binddn: The distinguished name of the account.
		:param str bindpw: The user password for simple authentication.
		"""
		self.binddn = binddn
		self.bindpw = bindpw
		univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, 'bind binddn=%s' % self.binddn)
		self.lo.simple_bind_s(self.binddn, self.__encode_pwd(self.bindpw))

	@_fix_reconnect_handling
	def bind_saml(self, bindpw):
		# type: (str) -> None
		"""
		Do LDAP bind using SAML message.

		:param str bindpw: The SAML authentication cookie.
		"""
		self.binddn = None
		self.bindpw = bindpw
		saml = ldap.sasl.sasl({
			ldap.sasl.CB_AUTHNAME: None,
			ldap.sasl.CB_PASS: bindpw,
		}, 'SAML')
		self.lo.sasl_interactive_bind_s('', saml)
		self.binddn = self.whoami()
		univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, 'SAML bind binddn=%s' % self.binddn)

	def unbind(self):
		# type: () -> None
		"""
		Unauthenticate.
		"""
		self.lo.unbind_s()

	def whoami(self):
		# type: () -> str
		"""
		Return the distinguished name of the authenticated user.

		:returns: The distinguished name.
		:rtype: str
		"""
		dn = self.lo.whoami_s()
		return re.sub(u'^dn:', u'', dn)

	def _reconnect(self):
		# type: () -> None
		"""Reconnect."""
		self.lo.reconnect(self.lo._uri, retry_max=self.lo._retry_max, retry_delay=self.lo._retry_delay)

	def __open(self, ca_certfile):
		# type: (Optional[str]) -> None
		_d = univention.debug.function('uldap.__open host=%s port=%d base=%s' % (self.host, self.port, self.base))  # noqa F841

		if self.reconnect:
			univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, 'establishing new connection with retry_max=%d' % self. client_connection_attempt)
			try:
				self.lo = ldap.ldapobject.ReconnectLDAPObject(self.uri, trace_stack_limit=None, retry_max=self.client_connection_attempt, retry_delay=1, bytes_mode=False)
			except TypeError:  # TODO: remove in the future, backwards compatibility for old python-ldap
				self.lo = ldap.ldapobject.ReconnectLDAPObject(self.uri, trace_stack_limit=None, retry_max=self.client_connection_attempt, retry_delay=1)
		else:
			univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, 'establishing new connection')
			try:
				self.lo = ldap.initialize(self.uri, trace_stack_limit=None, bytes_mode=False)
			except TypeError:  # TODO: remove in the future, backwards compatibility for old python-ldap
				self.lo = ldap.initialize(self.uri, trace_stack_limit=None)

		if ca_certfile:
			self.lo.set_option(ldap.OPT_X_TLS_CACERTFILE, ca_certfile)

		if self.protocol.lower() != 'ldaps':
			if self.start_tls == 1:
				try:
					self.__starttls()
				except:
					univention.debug.debug(univention.debug.LDAP, univention.debug.WARN, 'Could not start TLS')
			elif self.start_tls == 2:
				self.__starttls()

		if self.binddn and not self.uri.startswith('ldapi://'):
			self.bind(self.binddn, self.bindpw)

		# Override referral handling
		if self.follow_referral:
			self.lo.set_option(ldap.OPT_REFERRALS, 0)

		self.__schema = None
		self.__reconnects_done = 0

	@_fix_reconnect_handling
	def __starttls(self):
		self.lo.start_tls_s()

	def __encode(self, value):
		if six.PY3:
			return value
		if value is None:
			return value
		elif six.PY2 and isinstance(value, unicode):  # noqa: F821
			return str(value)
		elif isinstance(value, (list, tuple)):
			return map(self.__encode, value)
		else:
			return value

	def __recode_attribute(self, attr, val):
		if six.PY3:
			return val
		if attr in self.decode_ignorelist:
			return val
		return self.__encode(val)

	def __recode_entry(self, entry):
		if six.PY3:
			return entry
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

	@_fix_reconnect_handling
	def get(self, dn, attr=[], required=False):
		# type: (str, List[str], bool) -> Dict[str, List[str]]
		"""
		Return multiple attributes of a single LDAP object.

		:param str dn: The distinguished name of the object to lookup.
		:param attr: The list of attributes to fetch.
		:type attr: list[str]
		:param bool required: Raise an exception instead of returning an empty dictionary.
		:returns: A dictionary mapping the requested attributes to a list of their values.
		:rtype: dict[str, list[str]]
		:raises ldap.NO_SUCH_OBJECT: If the LDAP object is not accessible.
		"""
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

	@_fix_reconnect_handling
	def getAttr(self, dn, attr, required=False):
		# type: (str, str, bool) -> List[str]
		"""
		Return a single attribute of a single LDAP object.

		:param str dn: The distinguished name of the object to lookup.
		:param str attr: The attribute to fetch.
		:param bool required: Raise an exception instead of returning an empty dictionary.
		:returns: A list of values.
		:rtype: list[str]
		:raises ldap.NO_SUCH_OBJECT: If the LDAP object is not accessible.

		.. warning:: the attribute name is currently case sensitive and must be given as in the LDAP schema

		.. warning:: when `required=True` it raises `ldap.NO_SUCH_OBJECT` even if the object exists but the attribute is not set
		"""
		_d = univention.debug.function('uldap.getAttr %s %s' % (dn, attr))  # noqa F841
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

	@_fix_reconnect_handling
	def search(self, filter='(objectClass=*)', base='', scope='sub', attr=[], unique=False, required=False, timeout=-1, sizelimit=0, serverctrls=None, response=None):
		# type: (str, str, str, List[str], bool, bool, int, int, Optional[List[ldap.controls.LDAPControl]], Optional[Dict]) -> List[Tuple[str, Dict[str, List[str]]]]
		"""
		Perform LDAP search and return values.

		:param str filter: LDAP search filter.
		:param str base: the starting point for the search.
		:param str scope: Specify the scope of the search to be one of `base`, `base+one`, `one`, `sub`, or `domain` to specify a base object, base plus one-level, one-level, subtree, or children search.
		:param attr: The list of attributes to fetch.
		:type attr: list[str]
		:param bool unique: Raise an exception if more than one object matches.
		:param bool required: Raise an exception instead of returning an empty dictionary.
		:param int timeout: wait at most timeout seconds for a search to complete. `-1` for no limit.
		:param int sizelimit: retrieve at most sizelimit entries for a search. `0` for no limit.
		:param serverctrls: a list of :py:class:`ldap.controls.LDAPControl` instances sent to the server along with the LDAP request.
		:type serverctrls: list[ldap.controls.LDAPControl]
		:param dict response: An optional dictionary to receive the server controls of the result.
		:returns: A list of 2-tuples (dn, values) for each LDAP object, where values is a dictionary mapping attribute names to a list of values.
		:rtype: list[tuple[str, dict[str, list[str]]]]
		:raises ldap.NO_SUCH_OBJECT: Indicates the target object cannot be found.
		:raises ldap.INAPPROPRIATE_MATCHING: Indicates that the matching rule specified in the search filter does not match a rule defined for the attribute's syntax.
		"""
		univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, 'uldap.search filter=%s base=%s scope=%s attr=%s unique=%d required=%d timeout=%d sizelimit=%d' % (
			filter, base, scope, attr, unique, required, timeout, sizelimit))

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

	def searchDn(self, filter='(objectClass=*)', base='', scope='sub', unique=False, required=False, timeout=-1, sizelimit=0, serverctrls=None, response=None):
		# type: (str, str, str, bool, bool, int, int, Optional[List[ldap.controls.LDAPControl]]) -> List[str]
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
		:raises ldap.NO_SUCH_OBJECT: Indicates the target object cannot be found.
		:raises ldap.INAPPROPRIATE_MATCHING: Indicates that the matching rule specified in the search filter does not match a rule defined for the attribute's syntax.
		"""
		_d = univention.debug.function('uldap.searchDn filter=%s base=%s scope=%s unique=%d required=%d' % (filter, base, scope, unique, required))  # noqa F841
		return [x[0] for x in self.search(filter, base, scope, ['dn'], unique, required, timeout, sizelimit, serverctrls, response)]

	@_fix_reconnect_handling
	def getPolicies(self, dn, policies=None, attrs=None, result=None, fixedattrs=None):
		# type: (str, List[str], Dict[str, List[Any]], Any, Any) -> Dict[str, Dict[str, Any]]
		"""
		Return |UCS| policies for |LDAP| entry.

		:param str dn: The distinguished name of the |LDAP| entry.
		:param list policies: List of policy object classes...
		:param dict attrs: |LDAP| attributes. If not given, the data is fetched from LDAP.
		:param result: UNUSED!
		:param fixedattrs: UNUSED!
		:returns: A mapping of policy names to
		"""
		if attrs is None:
			attrs = {}
		if policies is None:
			policies = []
		_d = univention.debug.function('uldap.getPolicies dn=%s policies=%s attrs=%s' % (  # noqa F841
			dn, policies, attrs))
		if not dn and not policies:  # if policies is set apply a fictionally referenced list of policies
			return {}

		# get current dn
		if attrs and 'objectClass' in attrs and 'univentionPolicyReference' in attrs:
			oattrs = attrs
		else:
			oattrs = self.get(dn, ['univentionPolicyReference', 'objectClass'])
		if attrs and 'univentionPolicyReference' in attrs:
			policies = [x.decode('utf-8') for x in attrs['univentionPolicyReference']]
		elif not policies and not attrs:
			policies = [x.decode('utf-8') for x in oattrs.get('univentionPolicyReference', [])]

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
				policies = [x.decode('utf-8') for x in parent.get('univentionPolicyReference', [])]

		univention.debug.debug(
			univention.debug.LDAP, univention.debug.INFO,
			"getPolicies: result: %s" % result)
		return result

	def _merge_policy(self, policy_dn, obj_dn, object_classes, result):
		# type: (str, str, Set[str], Dict[str, Dict[str, Any]]) -> None
		"""
		Merge policies into result.

		:param policy_dn str: Distinguished name of the policy object.
		:param obj_dn: Distinguished name of the LDAP object.
		:param object_classes set: the set of object classes of the LDAP object.
		:param result list: A mapping, into which the policy is merged.
		"""
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
		for key in list(empty) + list(pattrs.keys()) + list(fixed):
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

	@_fix_reconnect_handling
	def get_schema(self):
		# type: () -> ldap.schema.subentry.SubSchema
		"""
		Retrieve |LDAP| schema information from |LDAP| server.

		:returns: The |LDAP| schema.
		:rtype: ldap.schema.subentry.SubSchema
		"""
		if self.reconnect and self.lo._reconnects_done > self.__reconnects_done:
			# the schema might differ after reconnecting (e.g. slapd restart)
			self.__schema = None
			self.__reconnects_done = self.lo._reconnects_done
		if not self.__schema:
			self.__schema = ldap.schema.SubSchema(self.lo.read_subschemasubentry_s(self.lo.search_subschemasubentry_s()), 0)
		return self.__schema

	@_fix_reconnect_handling
	def add(self, dn, al, serverctrls=None, response=None):
		# type: (str, List[Tuple], Optional[List[ldap.controls.LDAPControl]], Optional[dict]) -> None
		"""
		Add LDAP entry at distinguished name and attributes in add_list=(attribute-name, old-values. new-values) or (attribute-name, new-values).

		:param str dn: The distinguished name of the object to add.
		:param al: The add-list of 2-tuples (attribute-name, new-values).
		:param serverctrls: a list of ldap.controls.LDAPControl instances sent to the server along with the LDAP request
		:type serverctrls: list[ldap.controls.LDAPControl]
		:param dict response: An optional dictionary to receive the server controls of the result.
		"""
		if not serverctrls:
			serverctrls = []

		univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, 'uldap.add dn=%s' % dn)
		nal = {}  # type: Dict[str, Any]
		for i in al:
			key, val = i[0], i[-1]
			if not val:
				continue
			if isinstance(val, (bytes, six.text_type)):
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

	@_fix_reconnect_handling
	def modify(self, dn, changes, serverctrls=None, response=None):
		# type: (str, List[Tuple[str, Any, Any]], Optional[List[ldap.controls.LDAPControl]], Optional[dict]) -> str
		"""
		Modify LDAP entry DN with attributes in changes=(attribute-name, old-values, new-values).

		:param str dn: The distinguished name of the object to modify.
		:param changes: The modify-list of 3-tuples (attribute-name, old-values, new-values).
		:param serverctrls: a list of ldap.controls.LDAPControl instances sent to the server along with the LDAP request
		:type serverctrls: list[ldap.controls.LDAPControl]
		:param dict response: An optional dictionary to receive the server controls of the result.
		:returns: The distinguished name.
		:rtype: str
		"""
		univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, 'uldap.modify %s' % dn)

		if not serverctrls:
			serverctrls = []

		ml = []
		for key, oldvalue, newvalue in changes:
			if oldvalue and newvalue:
				if oldvalue == newvalue or (not isinstance(oldvalue, (bytes, six.text_type)) and not isinstance(newvalue, (bytes, six.text_type)) and set(oldvalue) == set(newvalue)):
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
				if key in ['preferredDeliveryMethod', 'jpegPhoto', 'univentionPortalBackground', 'univentionPortalLogo', 'univentionPortalEntryIcon', 'univentionUMCIcon']:
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
		new_vals = dict((key.lower(), val if isinstance(val, (bytes, six.text_type)) else val[0]) for op, key, val in ml if val and op not in (ldap.MOD_DELETE,))
		new_rdn = ldap.dn.dn2str([[(x, new_vals.get(x.lower(), dn_vals[x.lower()]), ldap.AVA_STRING) for x in [y[0] for y in rdn]]])
		rdn = ldap.dn.dn2str([rdn])
		if rdn != new_rdn:
			return ldap.dn.dn2str([ldap.dn.str2dn(new_rdn)[0]] + ldap.dn.str2dn(dn)[1:]), new_rdn
		return dn, rdn

	@_fix_reconnect_handling
	def modify_s(self, dn, ml):
		# type: (str, List[Tuple[str, Optional[List[str]], List[str]]]) -> None
		"""
		Redirect `modify_s` directly to :py:attr:`lo`.

		:param str dn: The distinguished name of the object to modify.
		:param ml: The modify-list of 3-tuples (attribute-name, old-values, new-values).
		"""
		try:
			self.lo.modify_ext_s(dn, ml)
		except ldap.REFERRAL as exc:
			if not self.follow_referral:
				raise
			lo_ref = self._handle_referral(exc)
			lo_ref.modify_ext_s(dn, ml)

	@_fix_reconnect_handling
	def modify_ext_s(self, dn, ml, serverctrls=None, response=None):
		# type: (str, List[Tuple[str, Any, Any]], Optional[List[ldap.controls.LDAPControl]], Optional[dict]) -> None
		"""
		Redirect `modify_ext_s` directly to :py:attr:`lo`.

		:param str dn: The distinguished name of the object to modify.
		:param ml: The modify-list of 3-tuples (attribute-name, old-values, new-values).
		:param serverctrls: a list of ldap.controls.LDAPControl instances sent to the server along with the LDAP request
		:type serverctrls: list[ldap.controls.LDAPControl]
		:param dict response: An optional dictionary to receive the server controls of the result.
		"""
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
		# type: (str, str, Optional[List[ldap.controls.LDAPControl]], Optional[dict]) -> None
		"""
		Rename a LDAP object.

		:param str dn: The old distinguished name of the object to rename.
		:param str newdn: The new distinguished name of the object to rename.
		:param serverctrls: a list of ldap.controls.LDAPControl instances sent to the server along with the LDAP request
		:type serverctrls: list[ldap.controls.LDAPControl]
		:param dict response: An optional dictionary to receive the server controls of the result.
		"""
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

	@_fix_reconnect_handling
	def rename_ext_s(self, dn, newrdn, newsuperior=None, serverctrls=None, response=None):
		# type: (str, str, Optional[str], Optional[List[ldap.controls.LDAPControl]], Optional[dict]) -> None
		"""
		Redirect `rename_ext_s` directly to :py:attr:`lo`.

		:param str dn: The old distinguished name of the object to rename.
		:param str newdn: The new distinguished name of the object to rename.
		:param str newsuperior: The distinguished name of the new container.
		:param serverctrls: a list of ldap.controls.LDAPControl instances sent to the server along with the LDAP request
		:type serverctrls: list[ldap.controls.LDAPControl]
		:param dict response: An optional dictionary to receive the server controls of the result.
		"""
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

	@_fix_reconnect_handling
	def delete(self, dn):
		# type: (str) -> None
		"""
		Delete a LDAP object.

		:param str dn: The distinguished name of the object to remove.
		"""
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
		# type: (str) -> Optional[str]
		"""
		Return the parent container of a distinguished name.

		:param str dn: The distinguished name.
		:return: The parent distinguished name or None if the LDAP base is reached.
		:rtype: str or None
		"""
		return parentDn(dn, self.base)

	def explodeDn(self, dn, notypes=False):
		# type: (str, Union[bool, int]) -> List[str]
		"""
		Break up a DN into its component parts.

		:param str dn: The distinguished name.
		:param bool notypes: Return only the component's attribute values if True. Also the attribute types if False.
		:return: A list of relative distinguished names.
		:rtype: list[str]
		"""
		return explodeDn(dn, notypes)

	@classmethod
	def compare_dn(cls, a, b):
		# type: (str, str) -> bool
		r"""Test DNs are same

		:param str a: The first distinguished name.
		:param str b: A second distinguished name.
		:returns: True if the DNs are the same, False otherwise.
		:rtype: bool

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
		"""
		Return state for pickling.
		"""
		_d = univention.debug.function('uldap.__getstate__')  # noqa F841
		odict = self.__dict__.copy()
		del odict['lo']
		return odict

	def __setstate__(self, dict):
		"""
		Set state for pickling.
		"""
		_d = univention.debug.function('uldap.__setstate__')  # noqa F841
		self.__dict__.update(dict)
		self.__open(self.ca_certfile)

	def _handle_referral(self, exception):
		# type: (ldap.REFERRAL) -> ldap.ldapobject.ReconnectLDAPObject
		"""
		Follow LDAP rederral.

		:param exception ldap.REFERRAL: The LDAP referral exception.
		:returns: LDAP connection object for the referred LDAP server.
		:rtype: ldap.ldapobject.ReconnectLDAPObject
		"""
		univention.debug.debug(univention.debug.LDAP, univention.debug.INFO, 'Following LDAP referral')
		exc = exception.args[0]
		info = exc.get('info')
		ldap_url = info[info.find('ldap'):]
		if isLDAPUrl(ldap_url):
			conn_str = LDAPUrl(ldap_url).initializeUrl()

			# FIXME?: this upgrades a access(reconnect=False) connection to a reconnect=True connection
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
