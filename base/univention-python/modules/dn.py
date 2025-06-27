# SPDX-FileCopyrightText: 2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
"""A convenient wrapper to easily work with LDAP Distinguished Names (DNs)"""

from __future__ import annotations

from typing import Any, Self

import ldap.dn


class DN:
    """A |LDAP| Distinguished Name."""

    _CASE_INSENSITIVE_ATTRIBUTES = {'cn', 'uid', 'dc', 'ou', 'c', 'l', 'o'}

    __slots__ = ('_dn', '_hash', '_str', 'dn')

    def __init__(self, dn: str) -> None:
        self.dn = dn
        self._hash = None
        self._str = None
        try:
            self._dn = ldap.dn.str2dn(self.dn)
        except ldap.DECODING_ERROR:
            raise ValueError('Malformed DN syntax: %r' % (self.dn,))

    @property
    def parent(self) -> Self | None:
        """
        >>> DN('foo=1,bar=2').parent == DN('bar=2')
        True
        """
        if len(self._dn) > 1:
            return self[1:]

    def endswith(self, other: str | Self):
        """
        >>> DN('foo=1,bar=2').endswith('bar=2')
        True
        >>> DN('foo=1,bar=2').endswith('foo=1')
        False
        """
        if not isinstance(other, DN):
            other = self.__class__(other)
        return self[-len(other):] == other

    def startswith(self, other: str | Self):
        """
        >>> DN('foo=1,bar=2').startswith('foo=1')
        True
        >>> DN('foo=1,bar=2').startswith('bar=2')
        False
        """
        if not isinstance(other, DN):
            other = self.__class__(other)
        return self[:len(other)] == other

    def __str__(self) -> str:
        # compute string only once since the object is static
        if self._str is None:
            self._str = ldap.dn.dn2str(self._dn)
        return self._str

    def __repr__(self) -> str:
        return '<%s %r>' % (type(self).__name__, str(self))

    def __len__(self) -> int:
        """Return length of DN components"""
        return len(self._dn)

    def __getitem__(self, key: str | slice) -> Any:
        if isinstance(key, slice):
            return self.__class__(ldap.dn.dn2str(self._dn[key]))
        return self.__class__(ldap.dn.dn2str([self._dn[key]]))

    def __eq__(self, other: Self) -> bool:
        """
        >>> DN('foo=1') == DN('foo=1')
        True
        >>> DN('foo=1') == DN('foo=2')
        False
        >>> DN('Foo=1') == DN('foo=1')
        True
        >>> DN('Foo=1') == DN('foo=2')
        False
        >>> DN('uid=Administrator') == DN('uid=administrator')
        True
        >>> DN('univentionAppID=Foo') == DN('univentionAppID=foo')
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

    def __ne__(self, other: Self) -> bool:
        return not self == other

    def __hash__(self) -> str:
        # compute hash only once - object is static
        if self._hash is None:
            self._hash = hash(tuple(
                tuple(sorted(
                    (attr.lower(), val.lower() if attr.lower() in self._CASE_INSENSITIVE_ATTRIBUTES else val, ava)
                    for attr, val, ava in rdn
                )) for rdn in self._dn
            ))
        return self._hash

    @classmethod
    def set(cls, values: list[str]) -> set[Self]:
        """
        Returns a unique set of DNs.

        >>> len(DN.set(['CN=computers,dc=foo', 'cn=computers,dc=foo', 'cn = computers,dc=foo', 'CN=Computers,dc=foo']))
        1
        """
        return set(map(cls, values))

    @classmethod
    def values(cls, dns: list[Self]) -> set[str]:
        """
        Return a unique set of DN strings from DNs.

        >>> DN.values(DN.set(['cn=foo', 'cn=bar']) - DN.set(['cn = foo'])) == {'cn=bar'}
        True
        """
        return set(map(str, dns))


if __name__ == '__main__':
    import doctest
    doctest.testmod()
