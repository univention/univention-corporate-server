#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
"""
|UCS| release version.
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
		# type: (Union[Tuple[int, int, int], List[int], str, UCS_Version]) -> None
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
		if isinstance(version, (tuple, list)) and len(version) == 3:
			self.major, self.minor, self.patchlevel = map(int, version)
		elif isinstance(version, str):
			self.set(version)
		elif isinstance(version, UCS_Version):
			self.major, self.minor, self.patchlevel = version.major, version.minor, version.patchlevel
		else:
			raise TypeError("not a tuple, list or string")

	def __cmp__(self, right):
		# type: (UCS_Version) -> int
		"""
		Compare to UCS versions.

		:returns: 0 if the versions are equal, -1 if the `left` is less than the `right` and 1 of the `left` is greater than the `right`.

		>>> UCS_Version((1, 1, 0)) < UCS_Version((1, 2, 0))
		True
		>>> UCS_Version((1, 10, 0)) < UCS_Version((1, 2, 0))
		False
		"""
		# major version differ
		if self.major < right.major:
			return -1
		if self.major > right.major:
			return 1
		# major is equal, check minor
		if self.minor < right.minor:
			return -1
		if self.minor > right.minor:
			return 1
		# minor is equal, check patchlevel
		if self.patchlevel < right.patchlevel:
			return -1
		if self.patchlevel > right.patchlevel:
			return 1

		return 0

	def set(self, version):
		# type: (str) -> None
		"""
		Parse string and set version.

		:param str version: A |UCS| release version string.
		:raises ValueError: if the string is not a valid |UCS| release version string.
		"""
		match = UCS_Version._regexp.match(version)
		if not match:
			raise ValueError('string does not match UCS version pattern')
		self.major, self.minor, self.patchlevel = map(int, match.groups())

	def __getitem__(self, k):
		# type: (str) -> int
		"""
		Dual natured dictionary: retrieve value from attribute.
		"""
		return self.__dict__[k]

	def __str__(self):
		# type: () -> str
		"""
		Return full version string.

		>>> str(UCS_Version((1,2,3)))
		'1.2-3'
		"""
		return UCS_Version.FULLFORMAT % self

	def __hash__(self):
		# type: () -> int
		return hash((self.major, self.minor, self.patchlevel))

	def __eq__(self, other):
		return (self.major, self.minor, self.patchlevel) == (other.major, other.minor, other.patchlevel)

	def __repr__(self):
		# type: () -> str
		"""
		Return canonical string representation.

		>>> UCS_Version((1,2,3))
		UCS_Version((1,2,3))
		"""
		return 'UCS_Version((%d,%d,%r))' % (self.major, self.minor, self.patchlevel)
