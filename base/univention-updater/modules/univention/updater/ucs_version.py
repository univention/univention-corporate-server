#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
"""
Univention Updater: UCS Release version
"""
# Copyright 2008-2019 Univention GmbH
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


class UCS_Version(object):
    """
    Version object consisting of major-, minor-number and patch-level
    """

    FORMAT = '%(major)d.%(minor)d'
    FULLFORMAT = '%(major)d.%(minor)d-%(patchlevel)d'
    # regular expression matching a UCS version X.Y-Z
    _regexp = re.compile('(?P<major>[0-9]+)\.(?P<minor>[0-9]+)-(?P<patch>[0-9]+)')

    def __init__(self, version):
        """
        :param version: must a :py:class:`str` matching the pattern `X.Y-Z` or a triple with major, minor and patchlevel.
        :type version: list(int) or tuple(int) or str or UCS_Version
        :raises TypeError: if the version cannot be parsed.

        >>> v = UCS_Version((2,3,1))
        >>> UCS_Version([2,3,1]) == v
        True
        >>> UCS_Version("2.3-1") == v
        True
        >>> UCS_Version(u"2.3-1") == v
        True
        >>> UCS_Version(v) == v
        True
        """
        if isinstance(version, basestring):
            self.set(version)
        elif isinstance(version, UCS_Version):
            self.mmp = version.mmp
        elif isinstance(version, (tuple, list)):
            self.mmp = map(int, version)
        else:
            raise TypeError("not a tuple, list or string")

    @property
    def mm(self):
        """
        2-tuple (major, minor) version
        """
        return (self.major, self.minor)

    @property
    def mmp(self):
        """
        3-tuple (major, minor, patch-level) version
        """
        return (self.major, self.minor, self.patchlevel)

    @mmp.setter
    def mmp(self, mmp):
        (self.major, self.minor, self.patchlevel) = mmp

    def __cmp__(self, right):
        """
        Compare to UCS versions. The method returns 0 if the versions
        are equal, <0 if the left is less than the right and >0 of the
        left is greater than the right.

        >>> UCS_Version((1, 1, 0)) < UCS_Version((1, 2, 0))
        True
        >>> UCS_Version((1, 10, 0)) < UCS_Version((1, 2, 0))
        False
        """
        return cmp(self.mmp, right.mmp)

    def set(self, version):
        """
        Parse string and set version.

        :param str version: A |UCS| release version string.
        :raises ValueError: if the string is not a valid |UCS| release version string.
        """
        match = UCS_Version._regexp.match(version)
        if not match:
            raise ValueError('string does not match UCS version pattern')
        self.mmp = map(int, match.groups())

    def __getitem__(self, k):
        """
        Dual natured dictionary: retrieve value from attribute.
        """
        return self.__dict__[k]

    def __str__(self):
        """
        Return full version string.

        >>> str(UCS_Version((1,2,3)))
        '1.2-3'
        """
        return UCS_Version.FULLFORMAT % self

    def __hash__(self):
        return hash(self.mmp)

    def __eq__(self, other):
        return self.mmp == other.mmp

    def __repr__(self):
        """
        Return canonical string representation.

        >>> UCS_Version((1,2,3))
        UCS_Version((1,2,3))
        """
        return 'UCS_Version((%d,%d,%r))' % self.mmp


if __name__ == '__main__':
    import doctest
    exit(doctest.testmod()[0])
