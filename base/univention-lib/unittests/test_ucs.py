#!/usr/bin/python2.7
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


import sys
from collections import Hashable

import pytest

from univention.unittests import import_module

use_installed = '--installed-lib' in sys.argv
ucs = import_module('ucs', 'python/', 'univention.lib.ucs', use_installed=use_installed)


def test_string():
	v = ucs.UCS_Version('5.0-11')
	assert v.major == 5
	assert v.minor == 0
	assert v.patchlevel == 11


def test_tuple():
	v = ucs.UCS_Version((4, 5, 6))
	assert v.major == 4
	assert v.minor == 5
	assert v.patchlevel == 6


def test_copy():
	v1 = ucs.UCS_Version((1, 2, 3))
	v2 = ucs.UCS_Version(v1)
	assert v1.major == 1
	assert v1.minor == 2
	assert v1.patchlevel == 3
	assert v1 == v2
	assert v1 is not v2


def test_type():
	with pytest.raises(TypeError):
		ucs.UCS_Version(445)
	with pytest.raises(TypeError):
		ucs.UCS_Version([4, 4, 5, 0])


def test_cmp():
	v = ucs.UCS_Version('2.3-4')
	assert v < ucs.UCS_Version('2.3-5')
	assert v < ucs.UCS_Version('2.4-1')
	assert v < ucs.UCS_Version('3.1-2')
	assert v == ucs.UCS_Version('2.3-4')
	assert v > ucs.UCS_Version('2.3-3')
	assert v > ucs.UCS_Version('2.2-5')
	assert v > ucs.UCS_Version('1.4-5')


def test_malformed():
	with pytest.raises(ValueError):
		ucs.UCS_Version('5.0.0')
	with pytest.raises(ValueError):
		ucs.UCS_Version('5-0-0')
	with pytest.raises(ValueError):
		ucs.UCS_Version('4.0')
	with pytest.raises(ValueError):
		ucs.UCS_Version('newest version')


def test_getter():
	v = ucs.UCS_Version('4.11-0')
	assert v['major'] == 4
	assert v['minor'] == 11
	assert v['patchlevel'] == 0


def test_str():
	v = ucs.UCS_Version([5, 1, 0])
	assert str(v) == '5.1-0'


def test_hash():
	v = ucs.UCS_Version([5, 0, 4])
	assert isinstance(v, Hashable)
	assert hash(v) == hash((v.major, v.minor, v.patchlevel))


def test_repr():
	v = ucs.UCS_Version('4.7-0')
	assert repr(v) == 'UCS_Version((4,7,0))'
