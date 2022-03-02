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

from collections import OrderedDict


class LDAPObject(object):
	def __init__(self, dn, attrs):
		self.dn = dn
		self.attrs = attrs
		self.changed = {}

	def __repr__(self):
		return 'Object({!r}, {!r})'.format(self.dn, self.attrs)


def make_obj(obj):
	dn = obj.pop('dn')[0].decode('utf-8')
	return LDAPObject(dn, obj)


def parse_ldif(ldif):
	ret = []
	obj = {}
	for line in ldif.splitlines():
		if not line.strip():
			if obj:
				ret.append(make_obj(obj))
			obj = {}
			continue
		k, v = line.split(': ', 1)
		obj.setdefault(k, [])
		obj[k].append(v.encode('utf-8'))
	if obj:
		ret.append(make_obj(obj))
	return ret


class Database(object):
	def __init__(self):
		self.objs = OrderedDict()

	def fill(self, fname):
		with open(fname) as fd:
			objs = parse_ldif(fd.read())
			for obj in objs:
				self.add(obj)

	def __iter__(self):
		for obj in self.objs.values():
			yield obj

	def __repr__(self):
		return 'Database({!r})'.format(self.objs)

	def __getitem__(self, dn):
		return self.objs[dn].attrs

	def get(self, dn):
		obj = self.objs.get(dn)
		if obj:
			return obj.attrs

	def add(self, obj):
		self.objs[obj.dn] = obj
		return obj.dn

	def delete(self, dn):
		del self.objs[dn]

	def modify(self, dn, ml):
		obj = self.objs[dn]
		for attr, old, new in ml:
			if new:
				if not isinstance(new, (list, tuple)):
					new = [new]
				obj.attrs[attr] = new
			else:
				obj.attrs.pop(attr, None)


# def make_univention_object(object_type, attrs, parent=None):
# 	if parent is None:
# 		parent = get_domain()
# 	id_attr = 'cn'
# 	id_value = attrs[id_attr][0]
# 	attrs['univentionObjectType'] = [object_type]
# 	attrs['objectClass'].append('univentionObject')
# 	dn = '{}={},{}'.format(id_attr, id_value, parent)
# 	return LDAPObject(dn, attrs)
