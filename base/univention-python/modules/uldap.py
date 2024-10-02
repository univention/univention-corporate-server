#
# Univention Python
#  LDAP access
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2002-2024 Univention GmbH
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

import logging
import random
import re
from collections.abc import Callable
from functools import wraps
from typing import Any

import ldap
import ldap.sasl
import ldap.schema
from ldap.controls.readentry import PostReadControl, PreReadControl
from ldapurl import LDAPUrl, isLDAPUrl

import univention.logging
from univention.config_registry import ucr


log = logging.getLogger('LDAP')


def parentDn(dn: str, base: str = '') -> str | None:
    """
    Return the parent container of a distinguished name.

    :param str dn: The distinguished name.
    :param str base: distinguished name where to stop.
    :return: The parent distinguished name or None.
    :rtype: str or None
    """
    if dn.lower() == base.lower():
        return None
    dn = ldap.dn.str2dn(dn)
    return ldap.dn.dn2str(dn[1:])


def explodeDn(dn: str, notypes: int = 0) -> list[str]:
    """
    Break up a DN into its component parts.

    :param str dn: The distinguished name.
    :param int notypes: Return only the component's attribute values if True. Also the attribute types if False.
    :return: A list of relative distinguished names.
    :rtype: list[str]
    """
    return ldap.dn.explode_dn(dn, notypes)


def getRootDnConnection(start_tls: int | None = None, decode_ignorelist: None = None, reconnect: bool = True) -> 'access':
    """
    Open a LDAP connection to the local LDAP server with the LDAP root account.

    :param int start_tls: Negotiate TLS with server. If `2` is given, the command will require the operation to be successful.
    :param bool reconnect: Automatically reconect if the connection fails.
    :return: A LDAP access object.
    :rtype: univention.uldap.access
    """
    port = int(ucr.get('slapd/port', '7389').split(',')[0])
    host = ucr['hostname'] + '.' + ucr['domainname']
    if ucr.get('ldap/server/type', 'dummy') == 'master':
        bindpw = open('/etc/ldap.secret').read().rstrip('\n')
        binddn = 'cn=admin,{}'.format(ucr['ldap/base'])
    else:
        bindpw = open('/etc/ldap/rootpw.conf').read().rstrip('\n').replace('rootpw "', '', 1)[:-1]
        binddn = 'cn=update,{}'.format(ucr['ldap/base'])
    return access(host=host, port=port, base=ucr['ldap/base'], binddn=binddn, bindpw=bindpw, start_tls=start_tls, reconnect=reconnect)


def getAdminConnection(start_tls: int | None = None, decode_ignorelist: None = None, reconnect: bool = True) -> 'access':
    """
    Open a LDAP connection to the Primary Directory Node LDAP server using the admin credentials.

    :param int start_tls: Negotiate TLS with server. If `2` is given, the command will require the operation to be successful.
    :param bool reconnect: Automatically reconect if the connection fails.
    :return: A LDAP access object.
    :rtype: univention.uldap.access
    """
    bindpw = open('/etc/ldap.secret').read().rstrip('\n')
    port = int(ucr.get('ldap/master/port', '7389'))
    return access(host=ucr['ldap/master'], port=port, base=ucr['ldap/base'], binddn='cn=admin,' + ucr['ldap/base'], bindpw=bindpw, start_tls=start_tls, reconnect=reconnect)


def getBackupConnection(start_tls: int | None = None, decode_ignorelist: None = None, reconnect: bool = True) -> 'access':
    """
    Open a LDAP connection to a Backup Directory Node LDAP server using the admin credentials.

    :param int start_tls: Negotiate TLS with server. If `2` is given, the command will require the operation to be successful.
    :param bool reconnect: Automatically reconect if the connection fails.
    :return: A LDAP access object.
    :rtype: univention.uldap.access
    """
    bindpw = open('/etc/ldap-backup.secret').read().rstrip('\n')
    port = int(ucr.get('ldap/master/port', '7389'))
    try:
        return access(host=ucr['ldap/master'], port=port, base=ucr['ldap/base'], binddn='cn=backup,' + ucr['ldap/base'], bindpw=bindpw, start_tls=start_tls, reconnect=reconnect)
    except ldap.SERVER_DOWN:
        if not ucr['ldap/backup']:
            raise
        backup = ucr['ldap/backup'].split(' ')[0]
        return access(host=backup, port=port, base=ucr['ldap/base'], binddn='cn=backup,' + ucr['ldap/base'], bindpw=bindpw, start_tls=start_tls, reconnect=reconnect)


def getMachineConnection(start_tls: int | None = None, decode_ignorelist: None = None, ldap_master: bool = True, secret_file: str = "/etc/machine.secret", reconnect: bool = True, random_server: bool = False) -> 'access':
    """
    Open a LDAP connection using the machine credentials.

    :param int start_tls: Negotiate TLS with server. If `2` is given, the command will require the operation to be successful.
    :param bool ldap_master: Open a connection to the Master if True, to the preferred LDAP server otherwise.
    :param str secret_file: The name of a file containing the password credentials.
    :param bool reconnect: Automatically reconnect if the connection fails.
    :param bool random_server: Choose a random LDAP server from ldap/server/name and ldap/server/addition.
    :return: A LDAP access object.
    :rtype: univention.uldap.access
    """
    bindpw = open(secret_file).read().rstrip('\n')

    if ldap_master:
        # Connect to Primary Directory Node
        port = int(ucr.get('ldap/master/port', '7389'))
        return access(host=ucr['ldap/master'], port=port, base=ucr['ldap/base'], binddn=ucr['ldap/hostdn'], bindpw=bindpw, start_tls=start_tls, reconnect=reconnect)
    else:
        # Connect to ldap/server/name
        port = int(ucr.get('ldap/server/port', '7389'))
        servers = [ucr.get('ldap/server/name')]
        additional_servers = ucr.get('ldap/server/addition', '').split()
        if random_server:
            if ucr.get('server/role') in ('memberserver',) and random_server:
                # shuffle all servers on Managed Nodes if random_server==True
                servers += additional_servers
                random.shuffle(servers)
            else:
                # shuffle only additional server
                random.shuffle(additional_servers)
                servers += additional_servers
        else:
            servers += additional_servers
        for server in servers:
            try:
                return access(host=server, port=port, base=ucr['ldap/base'], binddn=ucr['ldap/hostdn'], bindpw=bindpw, start_tls=start_tls, reconnect=reconnect)
            # LDAP server down, try next server
            except ldap.SERVER_DOWN as oexc:
                exc = oexc
        raise exc


def _fix_reconnect_handling(func):
    # Bug #47926: Python LDAP does not reconnect on ldap.UNAVAILABLE
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


class access:
    """
    The low-level class to access a LDAP server.

    :param str host: host name of the LDAP server.
    :param int port: TCP port of the LDAP server. Defaults to 7389 or 7636.
    :param str base: LDAP base distinguished name.
    :param str binddn: Distinguished name for simple authentication.
    :param str bindpw: Password for simple authentication.
    :param int start_tls: 0=no, 1=try StartTLS, 2=require StartTLS.
    :param str ca_certfile: File name to CA certificate.
    :param decode_ignorelist: obsolete
    :param bool use_ldaps: Connect to SSL port.
    :param str uri: LDAP connection string.
    :param bool follow_referral: Follow referrals and return result from other servers instead of returning the referral itself.
    :param bool reconnect: Automatically re-establish connection to LDAP server if connection breaks.
    """

    def __init__(self, host: str = 'localhost', port: int | None = None, base: str = '', binddn: str | None = '', bindpw: str = '', start_tls: int | None = None, ca_certfile: str | None = None, decode_ignorelist: None = None, use_ldaps: bool = False, uri: str | None = None, follow_referral: bool = False, reconnect: bool = True) -> None:
        self.host = host
        self.base = base
        self.binddn = binddn
        self.bindpw = bindpw
        self.start_tls = start_tls
        self.ca_certfile = ca_certfile
        self.reconnect = reconnect

        self.port = int(port) if port else None

        if self.start_tls is None:
            self.start_tls = ucr.get_int('directory/manager/starttls', 2)

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

        # python-ldap does not cache the credentials, so we override the
        # referral handling if follow_referral is set to true
        #  https://forge.univention.org/bugzilla/show_bug.cgi?id=9139
        self.follow_referral = follow_referral

        try:
            client_retry_count = int(ucr.get('ldap/client/retry/count', 10))
        except ValueError:
            log.error("Unable to read ldap/client/retry/count, please reset to an integer value")
            client_retry_count = 10

        self.client_connection_attempt = client_retry_count + 1

        self.__open(ca_certfile)

    @_fix_reconnect_handling
    def bind(self, binddn: str, bindpw: str) -> None:
        """
        Do simple LDAP bind using DN and password.

        :param str binddn: The distinguished name of the account.
        :param str bindpw: The user password for simple authentication.
        """
        self.binddn = binddn
        self.bindpw = bindpw
        log.debug('bind binddn=%s', self.binddn)
        self.lo.simple_bind_s(self.binddn, self.bindpw)

    @_fix_reconnect_handling
    def bind_saml(self, bindpw: str) -> None:
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
        log.debug('SAML bind binddn=%s', self.binddn)

    @_fix_reconnect_handling
    def bind_oauthbearer(self, authzid: str | None, bindpw: str) -> None:
        """
        Do LDAP bind using OAuth 2.0 Access Token.

        :param str authzid: Authorization Identifier
        :param str bindpw: The Access Token (as JWT)

        OAUTHBEARER follows RFC 7628.
        Currently sending an optional authzid which could be used for SASL Proxy Authorization in the future
        (https://www.openldap.org/doc/admin26/sasl.html#SASL%20Proxy%20Authorization).
        """
        self.binddn = None
        self.bindpw = bindpw
        oauth = ldap.sasl.sasl({
            ldap.sasl.CB_AUTHNAME: authzid,
            ldap.sasl.CB_PASS: bindpw,
        }, 'OAUTHBEARER')
        self.lo.sasl_interactive_bind_s('', oauth)
        self.binddn = self.whoami()
        log.debug('OAUTHBEARER bind binddn=%r', self.binddn)

    def unbind(self) -> None:
        """Unauthenticate."""
        self.lo.unbind_s()

    def whoami(self) -> str:
        """
        Return the distinguished name of the authenticated user.

        :returns: The distinguished name.
        :rtype: str
        """
        dn = self.lo.whoami_s()
        return re.sub('^dn:', '', dn)

    def _reconnect(self) -> None:
        """Reconnect."""
        self.lo.reconnect(self.lo._uri, retry_max=self.lo._retry_max, retry_delay=self.lo._retry_delay)

    def __open(self, ca_certfile: str | None) -> None:

        if self.reconnect:
            log.debug('establishing new connection with retry_max=%d', self.client_connection_attempt)
            self.lo = ldap.ldapobject.ReconnectLDAPObject(self.uri, trace_stack_limit=None, retry_max=self.client_connection_attempt, retry_delay=1)
        else:
            log.debug('establishing new connection')
            self.lo = ldap.initialize(self.uri, trace_stack_limit=None)

        if ca_certfile:
            self.lo.set_option(ldap.OPT_X_TLS_CACERTFILE, ca_certfile)
            self.lo.set_option(ldap.OPT_X_TLS_NEWCTX, 0)

        if self.protocol.lower() != 'ldaps':
            if self.start_tls == 1:
                try:
                    self.__starttls()
                except Exception:
                    log.warning('Could not start TLS')
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

    @_fix_reconnect_handling
    def get(self, dn: str, attr: list[str] = [], required: bool = False) -> dict[str, list[bytes]]:
        """
        Return multiple attributes of a single LDAP object.

        :param str dn: The distinguished name of the object to lookup.
        :param attr: The list of attributes to fetch.
        :type attr: list[str]
        :param bool required: Raise an exception instead of returning an empty dictionary.
        :returns: A dictionary mapping the requested attributes to a list of their values.
        :rtype: dict[str, list[bytes]]
        :raises ldap.NO_SUCH_OBJECT: If the LDAP object is not accessible.
        """
        if dn:
            try:
                result = self.lo.search_s(dn, ldap.SCOPE_BASE, '(objectClass=*)', attr)
                return result[0][1]
            except (ldap.NO_SUCH_OBJECT, LookupError):
                pass
        if required:
            raise ldap.NO_SUCH_OBJECT({'desc': 'no object'})
        return {}

    @_fix_reconnect_handling
    def getAttr(self, dn: str, attr: str, required: bool = False) -> list[bytes]:
        """
        Return a single attribute of a single LDAP object.

        :param str dn: The distinguished name of the object to lookup.
        :param str attr: The attribute to fetch.
        :param bool required: Raise an exception instead of returning an empty dictionary.
        :returns: A list of values.
        :rtype: list[bytes]
        :raises ldap.NO_SUCH_OBJECT: If the LDAP object is not accessible.

        .. warning:: the attribute name is currently case sensitive and must be given as in the LDAP schema

        .. warning:: when `required=True` it raises `ldap.NO_SUCH_OBJECT` even if the object exists but the attribute is not set
        """
        if dn:
            try:
                result = self.lo.search_s(dn, ldap.SCOPE_BASE, '(objectClass=*)', [attr])
                return result[0][1][attr]
            except (ldap.NO_SUCH_OBJECT, LookupError):
                pass
        if required:
            raise ldap.NO_SUCH_OBJECT({'desc': 'no object'})
        return []

    @_fix_reconnect_handling
    def search(self, filter: str = '(objectClass=*)', base: str = '', scope: str = 'sub', attr: list[str] = [], unique: bool = False, required: bool = False, timeout: int = -1, sizelimit: int = 0, serverctrls: list[ldap.controls.LDAPControl] | None = None, response: dict[str, ldap.controls.LDAPControl] | None = None) -> list[tuple[str, dict[str, list[bytes]]]]:
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
        :rtype: list[tuple[str, dict[str, list[bytes]]]]
        :raises ldap.NO_SUCH_OBJECT: Indicates the target object cannot be found.
        :raises ldap.INAPPROPRIATE_MATCHING: Indicates that the matching rule specified in the search filter does not match a rule defined for the attribute's syntax.
        """
        log.debug('uldap.search filter=%s base=%s scope=%s attr=%s unique=%d required=%d timeout=%d sizelimit=%d', filter, base, scope, attr, unique, required, timeout, sizelimit)

        if not base:
            base = self.base

        if scope == 'base+one':
            res = self.lo.search_ext_s(base, ldap.SCOPE_BASE, filter, attr, serverctrls=serverctrls, clientctrls=None, timeout=timeout, sizelimit=sizelimit) + \
                self.__search(base, ldap.SCOPE_ONELEVEL, filter, attr, serverctrls=serverctrls, clientctrls=None, timeout=timeout, sizelimit=sizelimit, response=response)
        else:
            if scope in {'sub', 'domain'}:
                ldap_scope = ldap.SCOPE_SUBTREE
            elif scope == 'one':
                ldap_scope = ldap.SCOPE_ONELEVEL
            else:
                ldap_scope = ldap.SCOPE_BASE
            res = self.__search(base, ldap_scope, filter, attr, serverctrls=serverctrls, clientctrls=None, timeout=timeout, sizelimit=sizelimit, response=response)

        if unique and len(res) > 1:
            raise ldap.INAPPROPRIATE_MATCHING({'desc': 'more than one object'})
        if required and len(res) < 1:
            raise ldap.NO_SUCH_OBJECT({'desc': 'no object'})
        return res

    def __search(self, *args, **kwargs):
        response = kwargs.pop('response', None)
        if isinstance(response, dict) and kwargs.get('serverctrls'):
            _rtype, res, _rmsgid, resp_ctrls = self.lo.result3(self.lo.search_ext(*args, **kwargs))
            response['ctrls'] = resp_ctrls
            return res
        else:
            return self.lo.search_ext_s(*args, **kwargs)

    def searchDn(self, filter: str = '(objectClass=*)', base: str = '', scope: str = 'sub', unique: bool = False, required: bool = False, timeout: int = -1, sizelimit: int = 0, serverctrls: list[ldap.controls.LDAPControl] | None = None, response: dict[str, ldap.controls.LDAPControl] | None = None) -> list[str]:
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
        return [x[0] for x in self.search(filter, base, scope, ['dn'], unique, required, timeout, sizelimit, serverctrls, response)]

    @_fix_reconnect_handling
    def getPolicies(self, dn: str, policies: list[str] | None = None, attrs: dict[str, list[Any]] | None = None, result: Any = None, fixedattrs: Any = None) -> dict[str, dict[str, Any]]:
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
        if not dn and not policies:  # if policies is set apply a fictionally referenced list of policies
            return {}

        # get current dn
        if 'objectClass' in attrs and 'univentionPolicyReference' in attrs:
            oattrs = attrs
        else:
            oattrs = self.get(dn, ['univentionPolicyReference', 'objectClass'])

        if 'univentionPolicyReference' in attrs:
            policies = [x.decode('utf-8') for x in attrs['univentionPolicyReference']]
        elif not policies and not attrs:
            policies = [x.decode('utf-8') for x in oattrs.get('univentionPolicyReference', [])]

        object_classes = {oc.lower() for oc in oattrs.get('objectClass', [])}

        merged: dict[str, dict[str, Any]] = {}
        if dn:
            obj_dn = dn
            while True:
                for policy_dn in policies or []:
                    self._merge_policy(policy_dn, obj_dn, object_classes, merged)
                dn = self.parentDn(dn) or ''
                if not dn:
                    break
                try:
                    parent = self.get(dn, attr=['univentionPolicyReference'], required=True)
                except ldap.NO_SUCH_OBJECT:
                    break
                policies = [x.decode('utf-8') for x in parent.get('univentionPolicyReference', [])]

        univention.debug.debug(
            univention.debug.LDAP, univention.debug.ALL,
            "getPolicies: result: %s" % merged)
        return merged

    def _merge_policy(self, policy_dn: str, obj_dn: str, object_classes: set[bytes], result: dict[str, dict[str, Any]]) -> None:
        """
        Merge policies into result.

        :param str policy_dn: Distinguished name of the policy object.
        :param obj_dn: Distinguished name of the LDAP object.
        :param set object_classes: the set of object classes of the LDAP object.
        :param list result: A mapping, into which the policy is merged.
        """
        pattrs = self.get(policy_dn)
        if not pattrs:
            return

        try:
            classes = set(pattrs['objectClass']) - {b'top', b'univentionPolicy', b'univentionObject'}
            ptype = classes.pop().decode('utf-8')
        except KeyError:
            return

        if pattrs.get('ldapFilter'):
            try:
                self.search(pattrs['ldapFilter'][0].decode('utf-8'), base=obj_dn, scope='base', unique=True, required=True)
            except ldap.NO_SUCH_OBJECT:
                return

        if not all(oc.lower() in object_classes for oc in pattrs.get('requiredObjectClasses', [])):
            return
        if any(oc.lower() in object_classes for oc in pattrs.get('prohibitedObjectClasses', [])):
            return

        fixed = {x.decode('utf-8') for x in pattrs.get('fixedAttributes', ())}
        empty = {x.decode('utf-8') for x in pattrs.get('emptyAttributes', ())}
        values = result.setdefault(ptype, {})
        SKIP = {'requiredObjectClasses', 'prohibitedObjectClasses', 'fixedAttributes', 'emptyAttributes', 'objectClass', 'cn', 'univentionObjectType', 'ldapFilter'}
        for key in (empty | set(pattrs) | fixed) - SKIP:
            if key not in values or key in fixed:
                value = [] if key in empty else pattrs.get(key, [])
                univention.debug.debug(
                    univention.debug.LDAP, univention.debug.ALL,
                    "getPolicies: %s sets: %s=%r" % (policy_dn, key, value))
                values[key] = {
                    'policy': policy_dn,
                    'value': value,
                    'fixed': key in fixed,
                }

    @_fix_reconnect_handling
    def get_schema(self) -> ldap.schema.subentry.SubSchema:
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
    def add(self, dn: str, al: list[tuple], serverctrls: list[ldap.controls.LDAPControl] | None = None, response: dict | None = None) -> None:
        """
        Add LDAP entry at distinguished name and attributes in add_list=(attribute-name, old-values. new-values) or (attribute-name, new-values).

        :param str dn: The distinguished name of the object to add.
        :param al: The add-list of 2-tuples (attribute-name, new-values).
        :param serverctrls: a list of ldap.controls.LDAPControl instances sent to the server along with the LDAP request
        :type serverctrls: list[ldap.controls.LDAPControl]
        :param dict response: An optional dictionary to receive the server controls of the result.
        """
        log.debug('uldap.add dn=%s', dn)

        if ucr.is_true('directory/manager/feature/prepostread', False):
            if serverctrls:
                for ctrl in serverctrls:
                    if isinstance(ctrl, PostReadControl):
                        log.info('uldap.add: overriding PostReadControl (%s)', ctrl.attrList)
                        ctrl.attrList = ['*', '+']
            else:
                serverctrls = [PostReadControl(True, ['*', '+'])]
        elif not serverctrls:
            serverctrls = []

        nal: dict[str, Any] = {}
        for i in al:
            key, val = i[0], i[-1]
            if not val:
                continue
            if isinstance(val, bytes | str):
                val = [val]
            vals = nal.setdefault(key, set())
            vals |= set(val)

        nal = [(k, list(v)) for k, v in nal.items()]

        try:
            _rtype, _rdata, _rmsgid, resp_ctrls = self.lo.add_ext_s(dn, nal, serverctrls=serverctrls)
        except ldap.REFERRAL as exc:
            if not self.follow_referral:
                raise
            lo_ref = self._handle_referral(exc)
            _rtype, _rdata, _rmsgid, resp_ctrls = lo_ref.add_ext_s(dn, nal, serverctrls=serverctrls)

        if serverctrls and isinstance(response, dict):
            response['ctrls'] = resp_ctrls

    @_fix_reconnect_handling
    def modify(self, dn: str, changes: list[tuple[str, Any, Any]], serverctrls: list[ldap.controls.LDAPControl] | None = None, response: dict | None = None, rename_callback: Callable | None = None) -> str:
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
        log.debug('uldap.modify %s', dn)

        if ucr.is_true('directory/manager/feature/prepostread', False):
            if serverctrls:
                for ctrl in serverctrls:
                    for ctrl_type in (PreReadControl, PostReadControl):
                        if isinstance(ctrl, ctrl_type):
                            log.info('uldap.modify: overriding %s (%s)', type(ctrl_type).__name__, ctrl.attrList)
                            ctrl.attrList = ['*', '+']
            else:
                serverctrls = [PreReadControl(True, ['*', '+']), PostReadControl(True, ['*', '+'])]
        elif not serverctrls:
            serverctrls = []

        ml = []
        for key, oldvalue, newvalue in changes:
            if oldvalue and newvalue:
                if oldvalue == newvalue or (not isinstance(oldvalue, bytes | str) and not isinstance(newvalue, bytes | str) and set(oldvalue) == set(newvalue)):
                    continue  # equal values
                op = ldap.MOD_REPLACE
                val = newvalue
            elif not oldvalue and newvalue:
                op = ldap.MOD_ADD
                val = newvalue
            elif oldvalue and not newvalue:
                op = ldap.MOD_DELETE
                val = oldvalue
                # These attributes don't have a matching rule:
                #   https://forge.univention.org/bugzilla/show_bug.cgi?id=15171
                #   https://forge.univention.org/bugzilla/show_bug.cgi?id=44019
                if key in ['preferredDeliveryMethod', 'jpegPhoto', 'univentionUMCIcon']:
                    val = None
            else:
                continue
            ml.append((op, key, val))

        # check if we need to rename the object
        new_dn, new_rdn = self.__get_new_dn(dn, ml)
        if not self.compare_dn(dn, new_dn):
            if rename_callback:
                rename_callback(dn, new_dn, ml)
            log.warning('rename %s', new_rdn)
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
        >>> get_dn('univentionAppID=foo,dc=bar', [(ldap.MOD_REPLACE, 'univentionAppID', 'föo')])[0] == u'univentionAppID=föo,dc=bar'
        True
        >>> get_dn('univentionAppID=foo,dc=bar', [(ldap.MOD_REPLACE, 'univentionAppID', 'bar')])[0]
        'univentionAppID=bar,dc=bar'
        """
        rdn = ldap.dn.str2dn(dn)[0]
        dn_vals = {x[0].lower(): x[1] for x in rdn}
        new_vals = {key.lower(): val if isinstance(val, bytes | str) else val[0] for op, key, val in ml if val and op not in (ldap.MOD_DELETE,)}
        new_rdn_ava = [(x, new_vals.get(x.lower(), dn_vals[x.lower()]), ldap.AVA_STRING) for x in [y[0] for y in rdn]]
        new_rdn_unicode = [(key, val.decode('UTF-8'), ava_type) if isinstance(val, bytes) else (key, val, ava_type) for key, val, ava_type in new_rdn_ava]
        new_rdn = ldap.dn.dn2str([new_rdn_unicode])
        rdn = ldap.dn.dn2str([rdn])
        if rdn != new_rdn:
            return ldap.dn.dn2str([ldap.dn.str2dn(new_rdn)[0]] + ldap.dn.str2dn(dn)[1:]), new_rdn
        return dn, rdn

    @_fix_reconnect_handling
    def modify_s(self, dn: str, ml: list[tuple[str, list[str] | None, list[str]]]) -> None:
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
    def modify_ext_s(self, dn: str, ml: list[tuple[str, Any, Any]], serverctrls: list[ldap.controls.LDAPControl] | None = None, response: dict | None = None) -> None:
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
            _rtype, _rdata, _rmsgid, resp_ctrls = self.lo.modify_ext_s(dn, ml, serverctrls=serverctrls)
        except ldap.REFERRAL as exc:
            if not self.follow_referral:
                raise
            lo_ref = self._handle_referral(exc)
            _rtype, _rdata, _rmsgid, resp_ctrls = lo_ref.modify_ext_s(dn, ml, serverctrls=serverctrls)

        if serverctrls and isinstance(response, dict):
            response['ctrls'] = resp_ctrls

    def rename(self, dn: str, newdn: str, serverctrls: list[ldap.controls.LDAPControl] | None = None, response: dict | None = None) -> None:
        """
        Rename a LDAP object.

        :param str dn: The old distinguished name of the object to rename.
        :param str newdn: The new distinguished name of the object to rename.
        :param serverctrls: a list of ldap.controls.LDAPControl instances sent to the server along with the LDAP request
        :type serverctrls: list[ldap.controls.LDAPControl]
        :param dict response: An optional dictionary to receive the server controls of the result.
        """
        log.debug('uldap.rename %s -> %s', dn, newdn)
        oldsdn = self.parentDn(dn)
        newrdn = ldap.dn.dn2str([ldap.dn.str2dn(newdn)[0]])
        newsdn = ldap.dn.dn2str(ldap.dn.str2dn(newdn)[1:])

        if ucr.is_true('directory/manager/feature/prepostread', False):
            if serverctrls:
                for ctrl in serverctrls:
                    for ctrl_type in (PreReadControl, PostReadControl):
                        if isinstance(ctrl, ctrl_type):
                            log.info('uldap.rename: overriding %s (%s)', type(ctrl_type).__name__, ctrl.attrList)
                            ctrl.attrList = ['*', '+']
            else:
                serverctrls = [PreReadControl(True, ['*', '+']), PostReadControl(True, ['*', '+'])]
        elif not serverctrls:
            serverctrls = []

        if oldsdn and newsdn.lower() == oldsdn.lower():
            log.debug('uldap.rename: modrdn %s to %s', dn, newrdn)
            self.rename_ext_s(dn, newrdn, serverctrls=serverctrls, response=response)
        else:
            log.debug('uldap.rename: move %s to %s in %s', dn, newrdn, newsdn)
            self.rename_ext_s(dn, newrdn, newsdn, serverctrls=serverctrls, response=response)

    @_fix_reconnect_handling
    def rename_ext_s(self, dn: str, newrdn: str, newsuperior: str | None = None, serverctrls: list[ldap.controls.LDAPControl] | None = None, response: dict | None = None) -> None:
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
            _rtype, _rdata, _rmsgid, resp_ctrls = self.lo.rename_s(dn, newrdn, newsuperior, serverctrls=serverctrls)
        except ldap.REFERRAL as exc:
            if not self.follow_referral:
                raise
            lo_ref = self._handle_referral(exc)
            _rtype, _rdata, _rmsgid, resp_ctrls = lo_ref.rename_s(dn, newrdn, newsuperior, serverctrls=serverctrls)

        if serverctrls and isinstance(response, dict):
            response['ctrls'] = resp_ctrls

    @_fix_reconnect_handling
    def delete(self, dn, serverctrls=None, response=None) -> None:
        """
        Delete a LDAP object.

        :param str dn: The distinguished name of the object to remove.
        :param serverctrls: a list of :py:class:`ldap.controls.LDAPControl` instances sent to the server along with the LDAP request.
        :type serverctrls: list[ldap.controls.LDAPControl]
        :param dict response: An optional dictionary to receive the server controls of the result.
        """
        log.debug('uldap.delete %s', dn)

        if ucr.is_true('directory/manager/feature/prepostread', False):
            if serverctrls:
                for ctrl in serverctrls:
                    if isinstance(ctrl, PreReadControl):
                        log.info('uldap.delete: overriding PreReadControl (%s)', ctrl.attrList)
                        ctrl.attrList = ['*', '+']
            else:
                serverctrls = [PreReadControl(True, ['*', '+'])]
        elif not serverctrls:
            serverctrls = []

        if dn:
            log.debug('delete')
            try:
                _rtype, _rdata, _rmsgid, resp_ctrls = self.lo.delete_ext_s(dn, serverctrls=serverctrls)
            except ldap.REFERRAL as exc:
                if not self.follow_referral:
                    raise
                lo_ref = self._handle_referral(exc)
                _rtype, _rdata, _rmsgid, resp_ctrls = lo_ref.delete_ext_s(dn, serverctrls=serverctrls)

        if serverctrls and isinstance(response, dict):
            response['ctrls'] = resp_ctrls

    def parentDn(self, dn: str) -> str | None:
        """
        Return the parent container of a distinguished name.

        :param str dn: The distinguished name.
        :return: The parent distinguished name or None if the LDAP base is reached.
        :rtype: str or None
        """
        return parentDn(dn, self.base)

    def explodeDn(self, dn: str, notypes: bool | int = False) -> list[str]:
        """
        Break up a DN into its component parts.

        :param str dn: The distinguished name.
        :param bool notypes: Return only the component's attribute values if True. Also the attribute types if False.
        :return: A list of relative distinguished names.
        :rtype: list[str]
        """
        return explodeDn(dn, notypes)

    @classmethod
    def compare_dn(cls, a: str, b: str) -> bool:
        r"""
        Test DNs are same

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
        """Return state for pickling."""
        odict = self.__dict__.copy()
        del odict['lo']
        return odict

    def __setstate__(self, dict):
        """Set state for pickling."""
        self.__dict__.update(dict)
        self.__open(self.ca_certfile)

    def _handle_referral(self, exception: ldap.REFERRAL) -> ldap.ldapobject.ReconnectLDAPObject:
        """
        Follow LDAP rederral.

        :param ldap.REFERRAL exception: The LDAP referral exception.
        :returns: LDAP connection object for the referred LDAP server.
        :rtype: ldap.ldapobject.ReconnectLDAPObject
        """
        log.debug('Following LDAP referral')
        exc = exception.args[0]
        info = exc.get('info')
        ldap_url = info[info.find('ldap'):]
        if isLDAPUrl(ldap_url):
            conn_str = LDAPUrl(ldap_url).initializeUrl()

            # FIXME?: this upgrades a access(reconnect=False) connection to a reconnect=True connection
            lo_ref = ldap.ldapobject.ReconnectLDAPObject(conn_str, trace_stack_limit=None)

            if self.ca_certfile:
                lo_ref.set_option(ldap.OPT_X_TLS_CACERTFILE, self.ca_certfile)
                lo_ref.set_option(ldap.OPT_X_TLS_NEWCTX, 0)

            if self.start_tls == 1:
                try:
                    lo_ref.start_tls_s()
                except Exception:
                    log.warning('Could not start TLS')
            elif self.start_tls == 2:
                lo_ref.start_tls_s()

            lo_ref.simple_bind_s(self.binddn, self.bindpw)
            return lo_ref

        else:
            raise ldap.CONNECT_ERROR('Bad referral "%s"' % (exc,))


if __name__ == '__main__':
    import doctest
    doctest.testmod()
