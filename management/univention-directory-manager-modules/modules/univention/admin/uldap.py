# -*- coding: utf-8 -*-
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2004-2024 Univention GmbH
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

"""|UDM| wrapper around :py:mod:`univention.uldap` that replaces exceptions."""

from __future__ import absolute_import

import time
from logging import getLogger
from typing import Any, Callable  # noqa: F401

import ldap

import univention.admin.license
import univention.uldap
from univention.admin import localization
from univention.admin._ucr import configRegistry


udm_log = getLogger('ADMIN')
log = getLogger('LDAP')

translation = localization.translation('univention/admin')
_ = translation.translate

explodeDn = univention.uldap.explodeDn


class DN(object):
    """A |LDAP| Distinguished Name."""

    def __init__(self, dn):
        # type: (str) -> None
        self.dn = dn
        try:
            self._dn = ldap.dn.str2dn(self.dn)
        except ldap.DECODING_ERROR:
            raise ValueError('Malformed DN syntax: %r' % (self.dn,))

    def __str__(self):
        return ldap.dn.dn2str(self._dn)

    def __unicode__(self):  # noqa: PLW3201
        return unicode(str(self))  # noqa: F821

    def __repr__(self):
        return '<%s %r>' % (type(self).__name__, str(self))

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
        >>> DN.values(DN.set(['cn=foo', 'cn=bar']) - DN.set(['cn = foo'])) == {'cn=bar'}
        True
        """
        return set(map(str, values))


def getBaseDN(host='localhost', port=None, uri=None):
    # type: (str, int | None, str | None) -> str
    """
    Return the naming context of the LDAP server.

    :param str host: The hostname of the LDAP server.
    :param int port: The TCP port number of the LDAP server.
    :param str uri: A complete LDAP URI.
    :returns: The distinguished name of the LDAP root.
    """
    if not uri:
        if not port:
            port = int(configRegistry.get('ldap/server/port', 7389))
        uri = "ldap://%s:%s" % (host, port)
    try:
        lo = ldap.ldapobject.ReconnectLDAPObject(uri, trace_stack_limit=None)
        result = lo.search_s('', ldap.SCOPE_BASE, 'objectClass=*', ['NamingContexts'])
        return result[0][1]['namingContexts'][0].decode('utf-8')
    except ldap.SERVER_DOWN:
        time.sleep(60)
    lo = ldap.ldapobject.ReconnectLDAPObject(uri, trace_stack_limit=None)
    result = lo.search_s('', ldap.SCOPE_BASE, 'objectClass=*', ['NamingContexts'])
    return result[0][1]['namingContexts'][0].decode('utf-8')


def getAdminConnection(start_tls=None, decode_ignorelist=None):
    # type: (int | None, None) -> tuple[univention.admin.uldap.access, univention.admin.uldap.position]
    """
    Open a LDAP connection using the admin credentials.

    :param int start_tls: Negotiate TLS with server. If `2` is given, the command will require the operation to be successful.
    :return: A 2-tuple (LDAP-access, LDAP-position)
    """
    lo = univention.uldap.getAdminConnection(start_tls)
    pos = position(lo.base)
    return access(lo=lo), pos


def getMachineConnection(start_tls=None, decode_ignorelist=None, ldap_master=True):
    # type: (int | None, None, bool) -> tuple[univention.admin.uldap.access, univention.admin.uldap.position]
    """
    Open a LDAP connection using the machine credentials.

    :param int start_tls: Negotiate TLS with server. If `2` is given, the command will require the operation to be successful.
    :param bool ldap_master: Open a connection to the Primary if True, to the preferred LDAP server otherwise.
    :return: A 2-tuple (LDAP-access, LDAP-position)
    """
    lo = univention.uldap.getMachineConnection(start_tls, ldap_master=ldap_master)
    pos = position(lo.base)
    return access(lo=lo), pos


def _err2str(err):
    # type: (Exception) -> str
    """
    Convert exception arguments to string.

    :param Exception err: An exception instance.
    :returns: A concatenated string formatted from the exception
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


class domain(object):
    """A |UDM| domain name."""

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
        # type: () -> str | None
        """
        Return the name of the Kerberos realms.

        :returns: The name of the Kerberos realm.
        """
        if 'krb5RealmName' not in self.domain:
            return None
        return self.domain['krb5RealmName'][0].decode('ASCII')


class position(object):
    """
    The position of a |LDAP| container.
    Supports relative distinguished names.
    """

    def __init__(self, base, loginDomain=u''):
        # type: (str, str) -> None
        """
        :param str base: The base distinguished name.
        :param str loginDomain: The login domain name.
        """
        if not base:
            raise univention.admin.uexceptions.insufficientInformation(_("There was no LDAP base specified."))

        self.__loginDomain = loginDomain or base
        self.__base = base
        self.__pos = u""
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
        self.__indomain = any(y[0] == 'dc' for x in ldap.dn.str2dn(self.__pos) for y in x)

    def getDn(self):
        # type: () -> str
        """
        Return the distinguished name.

        :returns: The absolute DN.
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
        """
        return ldap.dn.explode_rdn(self.getDn())[0]

    def getBase(self):
        # type: () -> str
        """
        Return the LDAP base DN.

        :returns: The distinguished name of the LDAP base.
        """
        return self.__base

    def isBase(self):
        # type: () -> bool
        """
        Check if the position equals the LDAP base DN.

        :returns: True if the position equals the base DN, False otherwise.
        """
        return access.compare_dn(self.getDn(), self.getBase())

    def getDomain(self):
        # type: () -> str
        """
        Return the distinguished name of the domain part of the position.

        :returns: The distinguished name.
        """
        if not self.__indomain or self.getDn() == self.getBase():
            return self.getBase()
        dn = []
        for part in ldap.dn.str2dn(self.getDn())[::-1]:
            if not any(y[0] == 'dc' for y in part):
                break
            dn.append(part)
        return ldap.dn.dn2str(dn[::-1])

    def getDomainConfigBase(self):
        # type: () -> str
        """
        Return the distinguished name of the configuration container.

        :returns: The distinguished name.
        """
        return u'cn=univention,' + self.getDomain()

    def isDomain(self):
        # type: () -> bool
        """
        Check if the position equals the domain DN.

        :returns: True if the position equals the domain DN, False otherwise.
        """
        return self.getDn() == self.getDomain()

    def getLoginDomain(self):
        # type: () -> str
        """
        Return the login domain name.

        :returns: The login domain name.
        """
        return self.__loginDomain

    def switchToParent(self):
        # type: () -> bool
        """
        Switch position to parent container.

        :returns: False if already at the Base, True otherwise.
        """
        if self.isBase():
            return False
        self.__setPosition(ldap.dn.dn2str(ldap.dn.str2dn(self.__pos)[1:]))
        return True


class access(object):
    """A |UDM| class to access a |LDAP| server."""

    @property
    def binddn(self):
        # type: () -> str | None
        """
        Return the distinguished name of the account.

        :returns: The distinguished name of the account (or `None` with |SAML|).
        """
        return self.lo.binddn

    @property
    def bindpw(self):
        # type: () -> str
        """
        Return the user password or credentials.

        :returns: The user password or credentials.
        """
        return self.lo.bindpw

    @property
    def host(self):
        # type: () -> str
        """
        Return the host name of the LDAP server.

        :returns: the host name of the LDAP server.
        """
        return self.lo.host

    @property
    def port(self):
        # type: () -> int
        """
        Return the TCP port number of the LDAP server.

        :returns: the TCP port number of the LDAP server.
        """
        return self.lo.port

    @property
    def base(self):
        # type: () -> str
        """
        Return the LDAP base of the LDAP server.

        :returns: the LDAP base of the LDAP server.
        """
        return self.lo.base

    @property
    def start_tls(self):
        # type: () -> int
        return self.lo.start_tls

    def __init__(
        self,
        host='localhost',  # type: str
        port=None,  # type: int | None
        base=u'',  # type: str
        binddn=u'',  # type: str
        bindpw=u'',  # type: str
        start_tls=None,  # type: int | None
        lo=None,  # type: univention.uldap.access | None
        follow_referral=False,  # type: bool
        uri=None,  # type: str | None
    ):  # type: (...) -> None
        """
        :param host: The hostname of the |LDAP| server.
        :param port: The |TCP| port number of the |LDAP| server.
        :param base: The base distinguished name.
        :param binddn: The distinguished name of the account.
        :param bindpw: The user password for simple authentication.
        :param start_tls: Negotiate |TLS| with server. If `2` is given, the command will require the operation to be successful.
        :param lo: |LDAP| connection.
        :param follow_referral: Follow |LDAP| referrals.
        :param uri: LDAP connection string.
        """
        if lo:
            self.lo = lo
        else:
            if not port:
                port = int(configRegistry.get('ldap/server/port', 7389))
            try:
                self.lo = univention.uldap.access(host, port, base, binddn, bindpw, start_tls, uri=uri, follow_referral=follow_referral)
            except ldap.INVALID_CREDENTIALS:
                raise univention.admin.uexceptions.authFail(_("Authentication failed"))
            except ldap.UNWILLING_TO_PERFORM:
                raise univention.admin.uexceptions.authFail(_("Authentication failed"))
        self.require_license = False
        self.allow_modify = True
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

    def bind_oauthbearer(self, authzid, bindpw):
        # type: (str | None, str) -> None
        """
        Do LDAP bind using OAuth 2.0 Access Token.

        :param str authzid: Authorization Identifier
        :param str bindpw: The Access Token (as JWT)
        """
        try:
            return self.lo.bind_oauthbearer(authzid, bindpw)
        except (ldap.INVALID_CREDENTIALS, ldap.UNWILLING_TO_PERFORM) as exc:
            log.debug('OAUTHBEARER authentication failed: %r', exc)
            raise univention.admin.uexceptions.authFail(_("Authentication failed"))
        self.__require_licence()

    def __require_licence(self):
        # type: () -> None
        if self.require_license:
            res = univention.admin.license.init_select(self.lo, 'admin')

            assert univention.admin.license._license
            self.licensetypes = univention.admin.license._license.types

            if res == 1:
                self.allow_modify = False
                raise univention.admin.uexceptions.licenseClients()
            elif res == 2:
                self.allow_modify = False
                raise univention.admin.uexceptions.licenseAccounts()
            elif res == 3:
                self.allow_modify = False
                raise univention.admin.uexceptions.licenseDesktops()
            elif res == 4:
                self.allow_modify = False
                raise univention.admin.uexceptions.licenseGroupware()
            elif res == 5:
                # Free for personal use edition
                raise univention.admin.uexceptions.freeForPersonalUse()
            # License Version 2:
            elif res == 6:
                self.allow_modify = False
                raise univention.admin.uexceptions.licenseUsers()
            elif res == 7:
                self.allow_modify = False
                raise univention.admin.uexceptions.licenseServers()
            elif res == 8:
                self.allow_modify = False
                raise univention.admin.uexceptions.licenseManagedClients()
            elif res == 9:
                self.allow_modify = False
                raise univention.admin.uexceptions.licenseCorporateClients()
            elif res == 10:
                self.allow_modify = False
                raise univention.admin.uexceptions.licenseDVSUsers()
            elif res == 11:
                self.allow_modify = False
                raise univention.admin.uexceptions.licenseDVSClients()

    def unbind(self):
        # type: () -> None
        """Unauthenticate."""
        self.lo.unbind()

    def whoami(self):
        # type: () -> str
        """
        Return the distinguished name of the authenticated user.

        :returns: The distinguished name.
        """
        return self.lo.whoami()

    def requireLicense(self, require=True):
        # type: (bool) -> None
        """
        Enable or disable the UCS licence check.

        :param bool require: `True` to require a valid licence.
        """
        self.require_license = require

    def _validateLicense(self):
        # type: () -> None
        """Check if the UCS licence is valid."""
        if self.require_license:
            univention.admin.license.select('admin')

    def get_schema(self):
        # type: () -> ldap.schema.subentry.SubSchema
        """
        Retrieve |LDAP| schema information from |LDAP| server.

        :returns: The |LDAP| schema.
        """
        return self.lo.get_schema()

    @classmethod
    def compare_dn(cls, a, b):
        # type: (str, str) -> bool
        """
        Compare two distinguished names for equality.

        :param str a: The first distinguished name.
        :param str b: A second distinguished name.
        :returns: True if the DNs are the same, False otherwise.
        """
        return univention.uldap.access.compare_dn(a, b)

    def get(self, dn, attr=[], required=False, exceptions=False):
        # type: (str, list[str], bool, bool) -> dict[str, list[bytes]]
        """
        Return multiple attributes of a single LDAP object.

        :param str dn: The distinguished name of the object to lookup.
        :param attr: The list of attributes to fetch.
        :param bool required: Raise an exception instead of returning an empty dictionary.
        :param bool exceptions: Ignore.
        :returns: A dictionary mapping the requested attributes to a list of their values.
        :raises ldap.NO_SUCH_OBJECT: If the LDAP object is not accessible.
        """
        return self.lo.get(dn, attr, required)

    def getAttr(self, dn, attr, required=False, exceptions=False):
        # type: (str, str, bool, bool) -> list[bytes]
        """
        Return a single attribute of a single LDAP object.

        :param str dn: The distinguished name of the object to lookup.
        :param str attr: The attribute to fetch.
        :param bool required: Raise an exception instead of returning an empty dictionary.
        :param bool exceptions: Ignore.
        :returns: A list of values.
        :raises ldap.NO_SUCH_OBJECT: If the LDAP object is not accessible.
        """
        return self.lo.getAttr(dn, attr, required)

    def search(self, filter=u'(objectClass=*)', base=u'', scope=u'sub', attr=[], unique=False, required=False, timeout=-1, sizelimit=0, serverctrls=None, response=None):
        # type: (str, str, str, list[str], bool, bool, int, int, list[ldap.controls.LDAPControl] | None, dict[str, ldap.controls.LDAPControl] | None) -> list[tuple[str, dict[str, list[bytes]]]]
        """
        Perform LDAP search and return values.

        :param str filter: LDAP search filter.
        :param str base: the starting point for the search.
        :param str scope: Specify the scope of the search to be one of `base`, `base+one`, `one`, `sub`, or `domain` to specify a base object, base plus one-level, one-level, subtree, or children search.
        :param attr: The list of attributes to fetch.
        :param bool unique: Raise an exception if more than one object matches.
        :param bool required: Raise an exception instead of returning an empty dictionary.
        :param int timeout: wait at most `timeout` seconds for a search to complete. `-1` for no limit.
        :param int sizelimit: retrieve at most `sizelimit` entries for a search. `0` for no limit.
        :param serverctrls: a list of ldap.controls.LDAPControl instances sent to the server along with the LDAP request
        :param dict response: An optional dictionary to receive the server controls of the result.
        :returns: A list of 2-tuples (dn, values) for each LDAP object, where values is a dictionary mapping attribute names to a list of values.
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

    def searchDn(self, filter=u'(objectClass=*)', base=u'', scope=u'sub', unique=False, required=False, timeout=-1, sizelimit=0, serverctrls=None, response=None):
        # type: (str, str, str, bool, bool, int, int, list[ldap.controls.LDAPControl] | None, dict[str, ldap.controls.LDAPControl] | None) -> list[str]
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
        :param dict response: An optional dictionary to receive the server controls of the result.
        :returns: A list of distinguished names.
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
        # type: (str, list[str] | None, dict[str, list[Any]] | None, Any, Any) -> dict[str, dict[str, Any]]
        """
        Return |UCS| policies for |LDAP| entry.

        :param str dn: The distinguished name of the |LDAP| entry.
        :param list policies: List of policy object classes...
        :param dict attrs: |LDAP| attributes. If not given, the data is fetched from LDAP.
        :param result: UNUSED!
        :param fixedattrs: UNUSED!
        :returns: A mapping of policy names to
        """
        udm_log.debug('getPolicies modules dn %s result', dn)
        return self.lo.getPolicies(dn, policies, attrs, result, fixedattrs)

    def add(self, dn, al, exceptions=False, serverctrls=None, response=None, ignore_license=False):
        # type: (str, list[tuple[str, Any]], bool, list[ldap.controls.LDAPControl] | None, dict | None, bool) -> None
        """
        Add LDAP entry at distinguished name and attributes in add_list=(attribute-name, old-values. new-values) or (attribute-name, new-values).

        :param str dn: The distinguished name of the object to add.
        :param al: The add-list of 2-tuples (attribute-name, new-values).
        :param bool exceptions: Raise the low level exception instead of the wrapping UDM exceptions.
        :param serverctrls: a list of ldap.controls.LDAPControl instances sent to the server along with the LDAP request
        :param bool ignore_license: Ignore license check if True.
        :param dict response: An optional dictionary to receive the server controls of the result.
        :raises univention.admin.uexceptions.licenseDisableModify: if the UCS licence prohibits any modificcation
        :raises univention.admin.uexceptions.objectExists: if the LDAP object already exists.
        :raises univention.admin.uexceptions.permissionDenied: if the user does not have the required permissions.
        :raises univention.admin.uexceptions.ldapError: if the syntax of the DN is invalid.
        :raises univention.admin.uexceptions.ldapError: on any other LDAP error.
        """
        self._validateLicense()
        if not self.allow_modify and not ignore_license:
            udm_log.error('add dn: %s', dn)
            raise univention.admin.uexceptions.licenseDisableModify()
        log.debug('add dn=%s al=%s', dn, al)
        if exceptions:
            return self.lo.add(dn, al, serverctrls=serverctrls, response=response)
        try:
            return self.lo.add(dn, al, serverctrls=serverctrls, response=response)
        except ldap.ALREADY_EXISTS as msg:
            log.debug('add dn=%s err=%s', dn, msg)
            raise univention.admin.uexceptions.objectExists(dn)
        except ldap.INSUFFICIENT_ACCESS as msg:
            log.debug('add dn=%s err=%s', dn, msg)
            raise univention.admin.uexceptions.permissionDenied()
        except ldap.INVALID_DN_SYNTAX as msg:
            raise univention.admin.uexceptions.ldapError('%s: %s' % (_err2str(msg), dn), original_exception=msg)
        except ldap.LDAPError as msg:
            log.debug('add dn=%s err=%s', dn, msg)
            raise univention.admin.uexceptions.ldapError(_err2str(msg), original_exception=msg)

    def modify(self, dn, changes, exceptions=False, ignore_license=False, serverctrls=None, response=None, rename_callback=None):
        # type: (str, list[tuple[str, Any, Any]], bool, int, list[ldap.controls.LDAPControl] | None, dict | None, Callable | None) -> str
        """
        Modify LDAP entry DN with attributes in changes=(attribute-name, old-values, new-values).

        :param str dn: The distinguished name of the object to modify.
        :param changes: The modify-list of 3-tuples (attribute-name, old-values, new-values).
        :param bool exceptions: Raise the low level exception instead of the wrapping UDM exceptions.
        :param bool ignore_license: Ignore license check if True.
        :param serverctrls: a list of ldap.controls.LDAPControl instances sent to the server along with the LDAP request
        :param dict response: An optional dictionary to receive the server controls of the result.
        :returns: The distinguished name.
        """
        self._validateLicense()
        if not self.allow_modify and not ignore_license:
            udm_log.error('modify dn: %s', dn)
            raise univention.admin.uexceptions.licenseDisableModify()
        log.debug('mod dn=%s ml=%s', dn, changes)
        if exceptions:
            return self.lo.modify(dn, changes, serverctrls=serverctrls, response=response, rename_callback=rename_callback)
        try:
            return self.lo.modify(dn, changes, serverctrls=serverctrls, response=response, rename_callback=rename_callback)
        except ldap.NO_SUCH_OBJECT as msg:
            log.debug('mod dn=%s err=%s', dn, msg)
            raise univention.admin.uexceptions.noObject(dn)
        except ldap.INSUFFICIENT_ACCESS as msg:
            log.debug('mod dn=%s err=%s', dn, msg)
            raise univention.admin.uexceptions.permissionDenied()
        except ldap.INVALID_DN_SYNTAX as msg:
            raise univention.admin.uexceptions.ldapError('%s: %s' % (_err2str(msg), dn), original_exception=msg)
        except ldap.LDAPError as msg:
            log.debug('mod dn=%s err=%s', dn, msg)
            raise univention.admin.uexceptions.ldapError(_err2str(msg), original_exception=msg)

    def rename(self, dn, newdn, move_childs=0, ignore_license=False, serverctrls=None, response=None):
        # type: (str, str, int, bool, list[ldap.controls.LDAPControl] | None, dict | None) -> None
        """
        Rename a LDAP object.

        :param dn: The old distinguished name of the object to rename.
        :param newdn: The new distinguished name of the object to rename.
        :param move_childs: Also rename the sub children. Must be `0` always as `1` is not implemented.
        :param ignore_license: Ignore license check if True.
        :param serverctrls: a list of ldap.controls.LDAPControl instances sent to the server along with the LDAP request
        :param response: An optional dictionary to receive the server controls of the result.
        """
        if move_childs != 0:
            raise univention.admin.uexceptions.noObject(_("Moving children is not supported."))
        self._validateLicense()
        if not self.allow_modify and not ignore_license:
            udm_log.warning('move dn: %s', dn)
            raise univention.admin.uexceptions.licenseDisableModify()
        log.debug('ren dn=%s newdn=%s', dn, newdn)
        try:
            return self.lo.rename(dn, newdn, serverctrls=serverctrls, response=response)
        except ldap.NO_SUCH_OBJECT as msg:
            log.debug('ren dn=%s err=%s', dn, msg)
            raise univention.admin.uexceptions.noObject(dn)
        except ldap.INSUFFICIENT_ACCESS as msg:
            log.debug('ren dn=%s err=%s', dn, msg)
            raise univention.admin.uexceptions.permissionDenied()
        except ldap.INVALID_DN_SYNTAX as msg:
            raise univention.admin.uexceptions.ldapError('%s: %s' % (_err2str(msg), dn), original_exception=msg)
        except ldap.LDAPError as msg:
            log.debug('ren dn=%s err=%s', dn, msg)
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
            except ldap.INSUFFICIENT_ACCESS:
                raise univention.admin.uexceptions.permissionDenied()
        log.debug('del dn=%s', dn)
        try:
            return self.lo.delete(dn)
        except ldap.NO_SUCH_OBJECT as msg:
            log.debug('del dn=%s err=%s', dn, msg)
            raise univention.admin.uexceptions.noObject(dn)
        except ldap.INSUFFICIENT_ACCESS as msg:
            log.debug('del dn=%s err=%s', dn, msg)
            raise univention.admin.uexceptions.permissionDenied()
        except ldap.INVALID_DN_SYNTAX as msg:
            raise univention.admin.uexceptions.ldapError('%s: %s' % (_err2str(msg), dn), original_exception=msg)
        except ldap.LDAPError as msg:
            log.debug('del dn=%s err=%s', dn, msg)
            raise univention.admin.uexceptions.ldapError(_err2str(msg), original_exception=msg)

    def parentDn(self, dn):
        # type: (str) -> str | None
        """
        Return the parent container of a distinguished name.

        :param str dn: The distinguished name.
        :return: The parent distinguished name or None if the LDAP base is reached.
        """
        return self.lo.parentDn(dn)

    def explodeDn(self, dn, notypes=False):
        # type: (str, bool) -> list[str]
        """
        Break up a DN into its component parts.

        :param str dn: The distinguished name.
        :param bool notypes: Return only the component's attribute values if True. Also the attribute types if False.
        :return: A list of relative distinguished names.
        """
        return self.lo.explodeDn(dn, notypes)
