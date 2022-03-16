#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright 2020-2022 Univention GmbH
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
#

import pytest


class TestUCR(object):
	def __init__(self):
		self.items = {}

	def get(self, key, default=None):
		return self.items.get(key, default)

	def get_int(self, key, default=None):
		val = self.get(key)
		try:
			return int(val)
		except (TypeError, ValueError):
			return default

	def __contains__(self, key):
		return key in self.items

	def __getitem__(self, key):
		# raises KeyError... lets see how this ends
		return self.items[key]

	def __delitem__(self, key):
		del self.items[key]

	def __setitem__(self, key, value):
		self.items[key] = value

	def keys(self):
		return self.items.keys()

	def is_false(self, key=None, default=False, value=None):  # noqa F811
		if value is None:
			value = self.get(key)  # type: ignore
			if value is None:
				return default
		return value.lower() in ('no', 'false', '0', 'disable', 'disabled', 'off')

	def is_true(self, key=None, default=False, value=None):  # noqa F811
		if value is None:
			value = self.get(key)  # type: ignore
			if value is None:
				return default
		return value.lower() in ('yes', 'true', '1', 'enable', 'enabled', 'on')

	def load(self):
		pass


@pytest.fixture
def ucr2():
	return TestUCR()
