# -*- coding: utf-8 -*-
"""
|UDM| samba related code
"""
# Copyright 2004-2019 Univention GmbH
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

import string
import six


class acctFlags:

	def __init__(self, flagstring=None, flags=None, fallbackflags=None):
		if flags is not None:
			self.__flags = flags
			return
		if not flagstring or not isinstance(flagstring, six.string_types) or len(flagstring) != 13:
			if fallbackflags is not None:
				self.__flags = fallbackflags
				return
			flagstring = "[U          ]"
		flags = {}
		flagstring = flagstring[1:-1]
		for letter in flagstring:
			if letter not in string.whitespace:
				flags[letter] = 1
		self.__flags = flags

	def __setitem__(self, key, value):
		self.__flags[key] = value

	def __getitem__(self, key):
		return self.__flags[key]

	def decode(self):
		flagstring = "["
		for flag, set in self.__flags.items():
			if set:
				flagstring = flagstring + flag
		while len(flagstring) < 12:
			flagstring += " "
		flagstring += "]"
		return flagstring

	def set(self, flag):
		self[flag] = 1
		return self.decode()

	def unset(self, flag):
		self[flag] = 0
		return self.decode()
