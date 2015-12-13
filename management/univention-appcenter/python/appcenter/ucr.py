#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention App Center
#  univention-app wrapper for ucr functions
#
# Copyright 2015 Univention GmbH
#
# http://www.univention.de/
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
# <http://www.gnu.org/licenses/>.
#

from univention.config_registry import ConfigRegistry
from univention.config_registry.frontend import ucr_update

_UCR = ConfigRegistry()
_UCR.load()


def ucr_load():
	_UCR.load()


def ucr_get(key, default=None):
	return _UCR.get(key, default)


def ucr_save(values):
	ucr_update(_UCR, values)


def ucr_includes(key):
	return key in _UCR


def ucr_is_true(key, value=None):
	return _UCR.is_true(key, value)


def ucr_is_false(key):
	return _UCR.is_false(key)


def ucr_keys():
	return _UCR.iterkeys()


def ucr_evaluated_as_true(value):
	if isinstance(value, basestring):
		value = value.lower()
	return _UCR.is_true(value=value)


def ucr_instance():
	return _UCR
