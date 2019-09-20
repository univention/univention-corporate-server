#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention App Center
#  Metaclass
#
# Copyright 2015-2019 Univention GmbH
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


class UniventionMetaInfo(object):
	pop = False
	save_as_list = False
	save_as_dict = False
	inheriting = True
	auto_set_name = False

	def _add_inheritace_info(self, klass, name):
		if self.inheriting:
			inheritance_info = getattr(klass, '_univention_meta_inheritance', set())
			inheritance_info.add(name)
			klass._univention_meta_inheritance = inheritance_info

	def set_name(self, name):
		name_attr = self.auto_set_name
		if name_attr is True:
			name_attr = 'name'
		setattr(self, name_attr, name)

	def contribute_to_class(self, klass, name):
		if self.auto_set_name:
			self.set_name(name)
		if self.save_as_list:
			if not hasattr(klass, self.save_as_list):
				self._add_inheritace_info(klass, self.save_as_list)
				setattr(klass, self.save_as_list, [])
			getattr(klass, self.save_as_list).append(self)
		if self.save_as_dict:
			if not hasattr(klass, self.save_as_dict):
				self._add_inheritace_info(klass, self.save_as_dict)
				setattr(klass, self.save_as_dict, {})
			getattr(klass, self.save_as_dict)[name] = self


class UniventionMetaClass(type):

	def __new__(mcs, name, bases, attrs):
		meta_infos = []
		for key, value in attrs.items():
			if hasattr(value, 'contribute_to_class'):
				if value.pop:
					attrs.pop(key)
				meta_infos.append((key, value))
		inheritance_info = set()
		for base in bases:
			if hasattr(base, '_univention_meta_inheritance'):
				for inheritance_name in getattr(base, '_univention_meta_inheritance'):
					inheritance_value = getattr(base, inheritance_name)
					if isinstance(inheritance_value, dict):
						attrs.setdefault(inheritance_name, {}).update(inheritance_value)
					if isinstance(inheritance_value, list):
						attrs.setdefault(inheritance_name, []).extend(inheritance_value)
					inheritance_info.add(inheritance_name)
		attrs['_univention_meta_inheritance'] = inheritance_info
		new_cls = super(UniventionMetaClass, mcs).__new__(mcs, name, bases, attrs)
		for meta_info_name, meta_info in meta_infos:
			meta_info.contribute_to_class(new_cls, meta_info_name)
		return new_cls
