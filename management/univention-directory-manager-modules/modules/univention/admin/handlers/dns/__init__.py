# -*- coding: utf-8 -*-
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2017-2024 Univention GmbH
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

"""|UDM| module for |DNS| records"""

from typing import Any  # noqa: F401

import six
from ldap.dn import str2dn

import univention.admin.filter as udm_filter
import univention.admin.handlers as udm_handlers
import univention.admin.uldap


__path__ = __import__('pkgutil').extend_path(__path__, __name__)  # type: ignore

ARPA_IP4 = '.in-addr.arpa'
ARPA_IP6 = '.ip6.arpa'


def is_dns(attr):  # type: (udm_handlers._Attributes) -> bool
    """Are the given LDAP attributes a DNS entry?"""
    return b'dNSZone' in attr.get('objectClass', [])


def is_zone(attr):  # type: (udm_handlers._Attributes) -> bool
    """Are the given LDAP attributes a DNS zone entry?"""
    return bool(attr.get("sOARecord"))


def is_reverse_zone(attr):  # type: (udm_handlers._Attributes) -> bool
    """Are the given LDAP attributes a DNS entry in a forward zone?"""
    return attr["zoneName"][0].decode("ASCII").endswith((ARPA_IP4, ARPA_IP6))


def is_forward_zone(attr):  # type: (udm_handlers._Attributes) -> bool
    """Are the given LDAP attributes a DNS entry in a reverse zone?"""
    return not is_reverse_zone(attr)


def has_any(attr, *attrs):  # type: (udm_handlers._Attributes, *str) -> bool
    """Are any of the named LDAP attributes present?"""
    return any(attr.get(a) for a in attrs)


def is_not_handled_by_other_module_than(attr, module):  # type: (udm_handlers._Attributes, str) -> bool
    """Are the given LDAP attributes handled by the specified UDM module?"""
    mod = module.encode('ASCII')
    return mod in attr.get('univentionObjectType', [mod])


class DNSBase(udm_handlers.simpleLdap):

    def __init__(
        self,
        co,  # type: None
        lo,  # type: univention.admin.uldap.access
        position,  # type: univention.admin.uldap.position | None
        dn=u'',  # type: str
        superordinate=None,  # type: udm_handlers.simpleLdap | None
        attributes=None,  # type: udm_handlers._Attributes | None
        update_zone=True,  # type: bool
    ):  # type: (...) -> None
        self.update_zone = update_zone
        univention.admin.handlers.simpleLdap.__init__(self, co, lo, position, dn, superordinate, attributes=attributes)

    def _updateZone(self):
        # type: () -> None
        if self.update_zone:
            assert self.superordinate is not None
            self.superordinate.open()
            self.superordinate.modify()

    def _ldap_post_create(self):
        # type: () -> None
        super(DNSBase, self)._ldap_post_create()
        self._updateZone()

    def _ldap_post_modify(self):
        # type: () -> None
        super(DNSBase, self)._ldap_post_modify()
        if self.hasChanged(self.descriptions.keys()):
            self._updateZone()

    def _ldap_post_remove(self):
        # type: () -> None
        super(DNSBase, self)._ldap_post_remove()
        self._updateZone()

    @staticmethod
    def _zone(superordinate):
        # type: (udm_handlers.simpleLdap) -> str
        """Extract DNS zone name from DN of superordinate."""
        dn = superordinate.dn
        for rdn in str2dn(dn):
            for k, v, _t in rdn:
                if k.lower() == "zonename":
                    return v
        raise ValueError(dn)

    def _ldap_addlist(self):
        # type: () -> list[tuple[str, Any]]
        assert self.superordinate is not None
        zone = self._zone(self.superordinate)
        return super(DNSBase, self)._ldap_addlist() + [("zoneName", zone.encode("ASCII"))]

    @classmethod
    def lookup_filter_superordinate(cls, filter, superordinate):
        # type: (udm_filter.conjunction, udm_handlers.simpleLdap) -> udm_filter.conjunction
        filter.expressions.append(udm_filter.expression('zoneName', cls._zone(superordinate), escape=True))
        return filter


# UNUSED:
def makeContactPerson(obj, arg):
    # type: (udm_handlers.simpleLdap, object) -> str
    """Create contact Email-address for domain."""
    domain = obj.position.getDomain()
    return 'root@%s.' % (domain.replace('dc=', '').replace(',', '.'),)


def unescapeSOAemail(email):
    # type: (str) -> str
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


def escapeSOAemail(email):
    # type: (str) -> str
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


def stripDot(old, encoding=()):
    # type: (list[str] | str | None, tuple[str, ...]) -> str | None
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
    return old[:-1].encode(*encoding) if isinstance(old, (bytes, six.text_type)) and old.endswith('.') else old.encode(*encoding)
