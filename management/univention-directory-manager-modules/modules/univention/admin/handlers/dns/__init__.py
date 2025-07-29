#
# SPDX-FileCopyrightText: 2017-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""|UDM| module for |DNS| records"""

from __future__ import annotations

from typing import Any

from ldap.dn import str2dn

import univention.admin.filter as udm_filter
import univention.admin.handlers as udm_handlers
import univention.admin.uldap


__path__ = __import__('pkgutil').extend_path(__path__, __name__)  # type: ignore

ARPA_IP4 = '.in-addr.arpa'
ARPA_IP6 = '.ip6.arpa'


def is_dns(attr: udm_handlers._Attributes) -> bool:
    """Are the given LDAP attributes a DNS entry?"""
    return b'dNSZone' in attr.get('objectClass', [])


def is_zone(attr: udm_handlers._Attributes) -> bool:
    """Are the given LDAP attributes a DNS zone entry?"""
    return bool(attr.get("sOARecord"))


def is_reverse_zone(attr: udm_handlers._Attributes) -> bool:
    """Are the given LDAP attributes a DNS entry in a forward zone?"""
    return attr["zoneName"][0].decode("ASCII").endswith((ARPA_IP4, ARPA_IP6))


def is_forward_zone(attr: udm_handlers._Attributes) -> bool:
    """Are the given LDAP attributes a DNS entry in a reverse zone?"""
    return not is_reverse_zone(attr)


def has_any(attr: udm_handlers._Attributes, *attrs: str) -> bool:
    """Are any of the named LDAP attributes present?"""
    return any(attr.get(a) for a in attrs)


def is_not_handled_by_other_module_than(attr: udm_handlers._Attributes, module: str) -> bool:
    """Are the given LDAP attributes handled by the specified UDM module?"""
    mod = module.encode('ASCII')
    return mod in attr.get('univentionObjectType', [mod])


class DNSBase(udm_handlers.simpleLdap):
    """Base class for dns/* modules"""

    def __init__(
        self,
        co: None,
        lo: univention.admin.uldap.access,
        position: univention.admin.uldap.position | None,
        dn: str = '',
        superordinate: udm_handlers.simpleLdap | None = None,
        attributes: udm_handlers._Attributes | None = None,
        update_zone: bool = True,
    ) -> None:
        self.update_zone = update_zone
        univention.admin.handlers.simpleLdap.__init__(self, co, lo, position, dn, superordinate, attributes=attributes)

    def _updateZone(self) -> None:
        if self.update_zone:
            assert self.superordinate is not None
            self.superordinate.open()
            self.superordinate.modify()

    def _ldap_post_create(self) -> None:
        super()._ldap_post_create()
        self._updateZone()

    def _ldap_post_modify(self) -> None:
        super()._ldap_post_modify()
        if self.hasChanged(self.descriptions.keys()):
            self._updateZone()

    def _ldap_post_remove(self) -> None:
        super()._ldap_post_remove()
        self._updateZone()

    @staticmethod
    def _zone(superordinate: udm_handlers.simpleLdap) -> str:
        """Extract DNS zone name from DN of superordinate."""
        dn = superordinate.dn
        for rdn in str2dn(dn):
            for k, v, _t in rdn:
                if k.lower() == "zonename":
                    return v
        raise ValueError(dn)

    def _ldap_addlist(self) -> list[tuple[str, Any]]:
        assert self.superordinate is not None
        zone = self._zone(self.superordinate)
        return [*super()._ldap_addlist(), ('zoneName', zone.encode('ASCII'))]

    @classmethod
    def lookup_filter_superordinate(cls, filter: udm_filter.conjunction, superordinate: udm_handlers.simpleLdap) -> udm_filter.conjunction:
        filter.expressions.append(udm_filter.expression('zoneName', cls._zone(superordinate), escape=True))
        return filter


# UNUSED:
def makeContactPerson(obj: udm_handlers.simpleLdap, arg: object) -> str:
    """Create contact Email-address for domain."""
    domain = obj.position.getDomain()
    return 'root@%s.' % (domain.replace('dc=', '').replace(',', '.'),)


def unescapeSOAemail(email: str) -> str:
    r"""
    Un-escape Email-address from DNS SOA record.
    >>> unescapeSOAemail(r'first\.last.domain.tld')
    'first.last@domain.tld'
    """
    ret = ''
    i = 0
    while i < len(email):
        if email[i] == '\\':
            i += 1
            if i >= len(email):
                raise ValueError()
        elif email[i] == '.':
            i += 1
            if i >= len(email):
                raise ValueError()
            ret += '@'
            ret += email[i:]
            return ret
        ret += email[i]
        i += 1
    raise ValueError()


def escapeSOAemail(email: str) -> str:
    r"""
    Escape Email-address for DNS SOA record.
    >>> escapeSOAemail('first.last@domain.tld')
    'first\\.last.domain.tld'
    """
    SPECIAL_CHARACTERS = set('"(),.:;<>@[\\]')
    if '@' not in email:
        raise ValueError()
    (local, domain) = email.rsplit('@', 1)
    tmp = ''
    for c in local:
        if c in SPECIAL_CHARACTERS:
            tmp += '\\'
        tmp += c
    local = tmp
    return local + '.' + domain


def stripDot(old: list[str] | str | None, encoding: tuple[str, ...] = ()) -> str | None:
    """
    >>> stripDot(['example.com.', 'example.com'])
    ['example.com', 'example.com']
    >>> stripDot('example.com.')
    'example.com'
    >>> stripDot([])
    []
    >>> stripDot('')
    ''
    >>> stripDot(None)
    """
    if isinstance(old, list):
        return [stripDot(_, encoding) for _ in old]
    if old is None:
        return old
    return old[:-1].encode(*encoding) if isinstance(old, bytes | str) and old.endswith('.') else old.encode(*encoding)
