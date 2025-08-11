# SPDX-FileCopyrightText: 2004-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""|UDM| allocators to allocate and lock resources for |LDAP| object creation."""

from __future__ import annotations

from logging import getLogger
from typing import TYPE_CHECKING, overload

import ldap
from ldap.filter import filter_format

import univention.admin.localization
import univention.admin.locking
import univention.admin.uexceptions
from univention.admin._ucr import configRegistry


if TYPE_CHECKING:
    from collections.abc import Sequence


try:
    from typing import Literal
    _TypesUidGid = Literal["uidNumber", "gidNumber"]
    _Types = Literal["uidNumber", "gidNumber", "uid", "gid", "sid", "domainSid", "mailPrimaryAddress", "mailAlternativeAddress", "aRecord", "mac", "groupName", "cn-uid-position", "univentionObjectIdentifier"]
    _Scopes = Literal["base", "one", "sub", "domain"]
except ImportError:
    pass


log = getLogger('ADMIN')
translation = univention.admin.localization.translation('univention/admin')
_ = translation.translate

_type2attr: dict[_Types, str] = {
    'uidNumber': 'uidNumber',
    'gidNumber': 'gidNumber',
    'uid': 'uid',
    'gid': 'gid',
    'sid': 'sambaSID',
    'domainSid': 'sambaSID',
    'mailPrimaryAddress': 'mailPrimaryAddress',
    'mailAlternativeAddress': 'mailAlternativeAddress',
    'aRecord': 'aRecord',
    'mac': 'macAddress',
    'groupName': 'cn',
    'cn-uid-position': 'cn',  # ['cn', 'uid', 'ou'],
    'univentionObjectIdentifier': 'univentionObjectIdentifier',
}
_type2scope: dict[_Types, _Scopes] = {
    'uidNumber': 'base',
    'gidNumber': 'base',
    'uid': 'domain',
    'gid': 'domain',
    'sid': 'base',
    'domainSid': 'base',
    'mailPrimaryAddress': 'domain',
    'mailAlternativeAddress': 'domain',
    'aRecord': 'domain',
    'mac': 'domain',
    'groupName': 'domain',
    'cn-uid-position': 'one',
    'univentionObjectIdentifier': 'domain',
}


def requestUserSid(
    lo: univention.admin.uldap.access,
    position: univention.admin.uldap.position,
    uid_s: str,
) -> str:
    uid = int(uid_s)
    algorithmical_rid_base = 1000
    rid = str(uid * 2 + algorithmical_rid_base)

    searchResult = lo.authz_connection.search(filter='objectClass=sambaDomain', attr=['sambaSID'])
    domainsid = searchResult[0][1]['sambaSID'][0].decode('ASCII')
    sid = domainsid + '-' + rid

    log.debug('ALLOCATE: request user sid. SID = %s-%s', domainsid, rid)

    return request(lo, position, 'sid', sid)


def requestGroupSid(
    lo: univention.admin.uldap.access,
    position: univention.admin.uldap.position,
    gid_s: str,
    generateDomainLocalSid: bool = False,
) -> str:
    gid = int(gid_s)
    algorithmical_rid_base = 1000
    rid = str(gid * 2 + algorithmical_rid_base + 1)

    if generateDomainLocalSid:
        sid = 'S-1-5-32-' + rid
    else:
        searchResult = lo.authz_connection.search(filter='objectClass=sambaDomain', attr=['sambaSID'])
        domainsid = searchResult[0][1]['sambaSID'][0].decode('ASCII')
        sid = domainsid + '-' + rid

    return request(lo, position, 'sid', sid)


def acquireRange(
    lo: univention.admin.uldap.access,
    position: univention.admin.uldap.position,
    atype: _Types,
    attr: str,
    ranges: Sequence[dict[str, int]],
    scope: _Scopes = 'base',
) -> str:
    log.debug('ALLOCATE: Start allocation for type = %r', atype)
    start_id = lo.authz_connection.getAttr('cn=%s,cn=temporary,cn=univention,%s' % (ldap.dn.escape_dn_chars(atype), position.getBase()), 'univentionLastUsedValue')

    log.debug('ALLOCATE: Start ID = %r', start_id)

    if not start_id:
        startID = ranges[0]['first']
        log.debug('ALLOCATE: Set Start ID to first %r', startID)
    else:
        startID = int(start_id[0])

    for _range in ranges:
        if startID < _range['first']:
            startID = _range['first']
        last = _range['last'] + 1
        other = None

        while startID < last:
            startID += 1
            log.debug('ALLOCATE: Set Start ID %r', startID)
            try:
                if other:
                    # exception occurred while locking other, so atype was successfully locked and must be released
                    univention.admin.locking.unlock(lo, position, atype, str(startID - 1).encode('utf-8'), scope=scope)
                    other = None
                log.debug('ALLOCATE: Lock ID %r for %r', startID, atype)
                univention.admin.locking.lock(lo, position, atype, str(startID).encode('utf-8'), scope=scope)
                if atype in ('uidNumber', 'gidNumber'):
                    # reserve the same ID for both
                    other = 'uidNumber' if atype == 'gidNumber' else 'gidNumber'
                    log.debug('ALLOCATE: Lock ID %r for %r', startID, other)
                    univention.admin.locking.lock(lo, position, other, str(startID).encode('utf-8'), scope=scope)
            except univention.admin.uexceptions.noLock:
                log.debug('ALLOCATE: Cannot Lock ID %r', startID)
                continue
            except univention.admin.uexceptions.objectExists:
                log.debug('ALLOCATE: Cannot Lock existing ID %r', startID)
                continue

            if atype in ('uidNumber', 'gidNumber'):
                _filter = filter_format('(|(uidNumber=%s)(gidNumber=%s))', (str(startID), str(startID)))
            else:
                _filter = '(%s=%d)' % (attr, startID)
            log.debug('ALLOCATE: searchfor %r', _filter)
            if lo.authz_connection.searchDn(base=position.getBase(), filter=_filter):
                log.debug('ALLOCATE: Already used ID %r', startID)
                univention.admin.locking.unlock(lo, position, atype, str(startID).encode('utf-8'), scope=scope)
                if other:
                    univention.admin.locking.unlock(lo, position, other, str(startID).encode('utf-8'), scope=scope)
                    other = None
                continue

            log.debug('ALLOCATE: Return ID %r', startID)
            if other:
                univention.admin.locking.unlock(lo, position, other, str(startID).encode('utf-8'), scope=scope)
            return str(startID)

    raise univention.admin.uexceptions.noLock(_('The attribute %r could not get locked.') % (atype,))


def acquireUnique(
    lo: univention.admin.uldap.access,
    position: univention.admin.uldap.position,
    type: _Types,
    value: str,
    attr: str,
    scope: _Scopes = 'base',
) -> str:
    log.debug('LOCK acquireUnique scope = %s', scope)
    searchBase = position.getDomain() if scope == "domain" else position.getBase()

    if type == "aRecord":  # uniqueness is only relevant among hosts (one or more dns entries having the same aRecord as a host are allowed)
        univention.admin.locking.lock(lo, position, type, value.encode('utf-8'), scope=scope)
        if not lo.authz_connection.searchDn(base=searchBase, filter=filter_format('(&(objectClass=univentionHost)(%s=%s))', (attr, value))):
            return value
    elif type in ['groupName', 'uid'] and configRegistry.is_true('directory/manager/user_group/uniqueness', True):
        univention.admin.locking.lock(lo, position, type, value.encode('utf-8'), scope=scope)
        if not lo.authz_connection.searchDn(base=searchBase, filter=filter_format('(|(&(cn=%s)(|(objectClass=univentionGroup)(objectClass=sambaGroupMapping)(objectClass=posixGroup)))(uid=%s))', (value, value))):
            log.debug('ALLOCATE return %s', value)
            return value
    elif type == "groupName":  # search filter is more complex then in general case
        univention.admin.locking.lock(lo, position, type, value.encode('utf-8'), scope=scope)
        if not lo.authz_connection.searchDn(base=searchBase, filter=filter_format('(&(%s=%s)(|(objectClass=univentionGroup)(objectClass=sambaGroupMapping)(objectClass=posixGroup)))', (attr, value))):
            log.debug('ALLOCATE return %s', value)
            return value
    elif type == 'cn-uid-position':
        base = lo.parentDn(value)
        attr, value, __ = ldap.dn.str2dn(value)[0][0]
        try:
            attrs = {'cn': ['uid'], 'uid': ['cn', 'ou'], 'ou': ['uid']}[attr]
        except KeyError:
            return value

        assert base is not None
        if all(ldap.dn.str2dn(x)[0][0][0] not in attrs for x in lo.authz_connection.searchDn(base=base, filter='(|%s)' % ''.join(filter_format('(%s=%s)', (attr, value)) for attr in attrs), scope=scope)):
            return value
        raise univention.admin.uexceptions.alreadyUsedInSubtree('name=%r position=%r' % (value, base))
    elif type in ('mailPrimaryAddress', 'mailAlternativeAddress') and configRegistry.is_true('directory/manager/mail-address/uniqueness'):
        log.debug('LOCK univention.admin.locking.lock scope = %s', scope)
        univention.admin.locking.lock(lo, position, 'mailPrimaryAddress', value.encode('utf-8'), scope=scope)
        other = 'mailPrimaryAddress' if type == 'mailAlternativeAddress' else 'mailAlternativeAddress'
        if not lo.authz_connection.searchDn(base=searchBase, filter=filter_format('(|(%s=%s)(%s=%s))', (attr, value, other, value))):
            log.debug('ALLOCATE return %s', value)
            return value
    elif type == 'mailAlternativeAddress':
        return value  # lock for mailAlternativeAddress exists only if above UCR variable is enabled
    else:
        log.debug('LOCK univention.admin.locking.lock scope = %s', scope)
        univention.admin.locking.lock(lo, position, type, value.encode('utf-8'), scope=scope)
        if not lo.authz_connection.searchDn(base=searchBase, filter=filter_format('%s=%s', (attr, value))):
            log.debug('ALLOCATE return %s', value)
            return value

    raise univention.admin.uexceptions.noLock(_('The attribute %r could not get locked.') % (type,))


@overload
def request(
    lo: univention.admin.uldap.access,
    position: univention.admin.uldap.position,
    type: _TypesUidGid,
    value: str | None = None,
) -> str:
    pass


@overload
def request(
    lo: univention.admin.uldap.access,
    position: univention.admin.uldap.position,
    type: _Types,
    value: str,
) -> str:
    pass


def request(
    lo: univention.admin.uldap.access,
    position: univention.admin.uldap.position,
    type: _Types,
    value: str | None = None,
) -> str:
    if type in ('uidNumber', 'gidNumber'):
        return acquireRange(lo, position, type, _type2attr[type], [{'first': 1000, 'last': 55000}, {'first': 65536, 'last': 1000000}], scope=_type2scope[type])
    assert value is not None
    return acquireUnique(lo, position, type, value, _type2attr[type], scope=_type2scope[type])


def confirm(
    lo: univention.admin.uldap.access,
    position: univention.admin.uldap.position,
    type: _Types,
    value: str,
    updateLastUsedValue: bool = True,
) -> None:
    if type in ('uidNumber', 'gidNumber') and updateLastUsedValue:
        lo.authz_connection.modify('cn=%s,cn=temporary,cn=univention,%s' % (ldap.dn.escape_dn_chars(type), position.getBase()), [('univentionLastUsedValue', b'1', value.encode('utf-8'))])
    elif type == 'cn-uid-position':
        return
    univention.admin.locking.unlock(lo, position, type, value.encode('utf-8'), _type2scope[type])


def release(
    lo: univention.admin.uldap.access,
    position: univention.admin.uldap.position,
    type: _Types,
    value: str,
) -> None:
    univention.admin.locking.unlock(lo, position, type, value.encode('utf-8'), _type2scope[type])
