#!/usr/bin/python3
#
# SPDX-FileCopyrightText: 2008-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""|UCS| release version."""

import re
import sys
from typing import Self


class UCS_Version:
    """Version object consisting of major-, minor-number and patch-level"""

    FORMAT = '%(major)d.%(minor)d'
    FULLFORMAT = '%(major)d.%(minor)d-%(patchlevel)d'
    # regular expression matching a UCS version X.Y-Z
    _regexp = re.compile(r'(?P<major>[0-9]+)\.(?P<minor>[0-9]+)-(?P<patch>[0-9]+)')
    _format = re.compile(r'%([%afimp])')

    def __init__(self, version: tuple[int, int, int] | list[int] | str | Self) -> None:
        """
        :param version: must a :py:class:`str` matching the pattern `X.Y-Z` or a triple with major, minor and patchlevel.
        :type version: list(int) or tuple(int) or str or UCS_Version
        :raises TypeError: if the version cannot be parsed.

        >>> v = UCS_Version((2,3,1))
        >>> UCS_Version([2,3,1]) == v
        True
        >>> UCS_Version("2.3-1") == v
        True
        >>> UCS_Version(v) == v
        True
        """
        if isinstance(version, tuple | list):
            self.mmp = map(int, version)  # type: ignore
        elif isinstance(version, str):
            self.set(version)
        elif isinstance(version, UCS_Version):
            self.mmp = version.mmp
        else:
            raise TypeError("not a tuple, list or string")

    @property
    def mm(self) -> tuple[int, int]:
        """2-tuple (major, minor) version"""
        return (self.major, self.minor)

    @property
    def mmp(self) -> tuple[int, int, int]:
        """3-tuple (major, minor, patch-level) version"""
        return (self.major, self.minor, self.patchlevel)

    @mmp.setter
    def mmp(self, mmp: list[int] | tuple[int, int, int]) -> None:
        (self.major, self.minor, self.patchlevel) = mmp

    def __lt__(self, other: Self) -> bool:
        """
        Compare to UCS versions.

        :returns: 0 if the versions are equal, -1 if the `left` is less than the `right` and 1 of the `left` is greater than the `right`.

        >>> UCS_Version((1, 1, 0)) < UCS_Version((1, 2, 0))
        True
        >>> UCS_Version((1, 10, 0)) < UCS_Version((1, 2, 0))
        False
        >>> UCS_Version((1, 2, 3)) < UCS_Version((1, 2, 3))
        False
        """
        return self.mmp < other.mmp if isinstance(other, UCS_Version) else NotImplemented

    def __le__(self, other: Self) -> bool:
        """
        >>> UCS_Version((1, 2, 3)) <= UCS_Version((1, 2, 3))
        True
        >>> UCS_Version((1, 2, 3)) <= UCS_Version((1, 0, 0))
        False
        """
        return self.mmp <= other.mmp if isinstance(other, UCS_Version) else NotImplemented

    def __eq__(self, other: object) -> bool:
        """
        >>> UCS_Version((1, 0, 0)) == UCS_Version((1, 0, 0))
        True
        >>> UCS_Version((1, 0, 0)) == UCS_Version((2, 0, 0))
        False
        """
        return isinstance(other, UCS_Version) and self.mmp == other.mmp

    def __ne__(self, other: object) -> bool:
        """
        >>> UCS_Version((1, 0, 0)) != UCS_Version((1, 0, 0))
        False
        >>> UCS_Version((1, 0, 0)) != UCS_Version((2, 0, 0))
        True
        """
        return not isinstance(other, UCS_Version) or self.mmp != other.mmp

    def __ge__(self, other: Self) -> bool:
        """
        >>> UCS_Version((1, 2, 3)) >= UCS_Version((1, 2, 3))
        True
        >>> UCS_Version((1, 0, 0)) >= UCS_Version((1, 2, 3))
        False
        """
        return self.mmp >= other.mmp if isinstance(other, UCS_Version) else NotImplemented

    def __gt__(self, other: Self) -> bool:
        """
        >>> UCS_Version((1, 2, 3)) > UCS_Version((1, 2, 3))
        False
        >>> UCS_Version((1, 2, 3)) > UCS_Version((1, 0, 0))
        True
        """
        return self.mmp > other.mmp if isinstance(other, UCS_Version) else NotImplemented

    def set(self, version: str) -> None:
        """
        Parse string and set version.

        :param str version: A |UCS| release version string.
        :raises ValueError: if the string is not a valid |UCS| release version string.
        """
        match = UCS_Version._regexp.match(version)
        if not match:
            raise ValueError('string %s does not match UCS version pattern' % version)
        self.mmp = map(int, match.groups())  # type: ignore

    def __getitem__(self, k: str) -> int:
        """Dual natured dictionary: retrieve value from attribute."""
        return self.__dict__[k]

    def __str__(self) -> str:
        """
        Return full version string.

        >>> str(UCS_Version((1,2,3)))
        '1.2-3'
        """
        return self.FULLFORMAT % self

    def __hash__(self) -> int:
        return hash(self.mmp)

    def __repr__(self) -> str:
        """
        Return canonical string representation.

        >>> UCS_Version((1,2,3))
        UCS_Version((1,2,3))
        """
        return 'UCS_Version((%d,%d,%r))' % self.mmp

    def __format__(self, fmt: str) -> str:
        """
        Support Format String Syntax:

        >>> "{0:%f}".format(UCS_Version((1, 2, 3))
        "1.2-3"

        The follwong format codes are supported:

        * `%a`: The major version, e.g. `1`.
        * `%f`: The full version, e.g. `1.2-3`.
        * `%i`: The minor version, e.g. `2`.
        * `%m`: The major and minor version, e.g. `1.2`.
        * `%p`: The patch-level version, e.g. `3`.
        * `%%`: A literal `'%'` character.
        """
        if not isinstance(fmt, str):  # pragma: no cover
            raise TypeError("must be str, not %s" % type(fmt).__name__)
        if fmt:
            val = {
                "%": "%",
                "a": str(self.major),
                "i": str(self.minor),
                "p": str(self.patchlevel),
                "m": self.FORMAT % self,
                "f": str(self),
            }
            return self._format.sub(lambda m: val[m.group(1)], fmt)
        return str(self)


if __name__ == '__main__':  # pragma: no cover
    import doctest
    sys.exit(doctest.testmod()[0])
