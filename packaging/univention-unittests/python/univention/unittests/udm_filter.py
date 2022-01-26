#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright 2020-2021 Univention GmbH
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

from fnmatch import fnmatch


class AndFilter(object):
	def __init__(self, children):
		self.children = children

	def __repr__(self):
		return 'AND({!r})'.format(self.children)

	def matches(self, obj):
		return all(child.matches(obj) for child in self.children)


class OrFilter(object):
	def __init__(self, children):
		self.children = children

	def __repr__(self):
		return 'OR({!r})'.format(self.children)

	def matches(self, obj):
		return any(child.matches(obj) for child in self.children)


class NotFilter(object):
	def __init__(self, children):
		assert len(children) == 1
		self.child = children[0]

	def __repr__(self):
		return 'NOT({!r})'.format(self.child)

	def matches(self, obj):
		return not self.child.matches(obj)


class AttrFilter(object):
	def __init__(self, key, value):
		self.key = key
		self.value = value

	def __repr__(self):
		return 'ATTR({}={})'.format(self.key, self.value)

	def matches(self, obj):
		obj_values = obj.attrs.get(self.key, [])
		if not self.value:
			return not obj_values
		for obj_value in obj_values:
			obj_value = obj_value.decode('utf-8')
			if fnmatch(obj_value, self.value):
				return True
		return False


def find_bracket_idx(filter_string):
	if not filter_string.startswith('('):
		raise ValueError(filter_string)
	i = 0
	for idx, c in enumerate(filter_string):
		if c == '(':
			i += 1
		if c == ')':
			i -= 1
		if i == 0:
			return idx


def parse_filter(filter_string):
	if filter_string.startswith('(&'):
		if not filter_string.endswith(')'):
			raise ValueError(filter_string)
		idx = find_bracket_idx(filter_string)
		inside = filter_string[2:idx]
		filter_obj = [AndFilter(parse_filter(inside))]
	elif filter_string.startswith('(|'):
		if not filter_string.endswith(')'):
			raise ValueError(filter_string)
		idx = find_bracket_idx(filter_string)
		inside = filter_string[2:idx]
		filter_obj = [OrFilter(parse_filter(inside))]
	elif filter_string.startswith('(!'):
		if not filter_string.endswith(')'):
			raise ValueError(filter_string)
		idx = find_bracket_idx(filter_string)
		inside = filter_string[2:idx]
		filter_obj = [NotFilter(parse_filter(inside))]
	else:
		idx = filter_string.find(')')
		filter_obj = [AttrFilter(*filter_string[1:idx].split('=', 1))]
	tail = filter_string[idx + 1:]
	if tail:
		return filter_obj + parse_filter(tail)
	else:
		return filter_obj


def make_filter(filter_string):
	if not filter_string:
		return AndFilter([])
	else:
		if not filter_string.startswith('(') and not filter_string.endswith(')'):
			filter_string = '(' + filter_string + ')'
		filter_objs = parse_filter(filter_string)
		return AndFilter(filter_objs)
