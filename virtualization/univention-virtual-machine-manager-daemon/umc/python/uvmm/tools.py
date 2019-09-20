# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: management of virtualization servers
#
# Copyright 2010-2019 Univention GmbH
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

from types import BuiltinMethodType, MethodType, FunctionType, TypeType, NoneType


BASE_TYPES = (int, float, long, bool, basestring, NoneType, list, tuple)


def object2dict(obj):
	"""
	Converts the attributes of an object to a dictionary.
	"""
	if isinstance(obj, BASE_TYPES):
		return obj
	attrs = {}
	for slot in obj.__dict__:
		if slot.startswith('__') and slot.endswith('__'):
			continue
		attr = getattr(obj, slot)
		if isinstance(attr, (BuiltinMethodType, MethodType, FunctionType, TypeType)):
			continue
		if isinstance(attr, (int, float, long, bool, NoneType)):
			attrs[slot] = attr
		elif isinstance(attr, basestring):
			if slot not in ('cpus',):
				if attr in ('0', 'FALSE'):
					attr = False
				elif attr in ('1', 'TRUE'):
					attr = True
			attrs[slot] = attr
		elif isinstance(attr, (list, tuple)):
			attrs[slot] = [object2dict(_) for _ in attr]
		elif isinstance(attr, dict):
			attrs[slot] = dict([
				(key, object2dict(value))
				for key, value in attr.items()
			])
		else:
			attrs[slot] = object2dict(attr)

	return attrs


if __name__ == '__main__':
	import doctest
	doctest.testmod()
