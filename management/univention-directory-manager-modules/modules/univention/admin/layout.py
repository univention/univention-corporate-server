# -*- coding: utf-8 -*-
"""
|UDM| classes to define layouts
"""
# Copyright 2011-2019 Univention GmbH
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

import copy


class ILayoutElement(dict):
	"""
	Describes the layout information for a tab or a groupbox.
	"""

	def __init__(self, label, description='', layout=[]):
		dict.__init__(self)
		self.__setitem__('label', label)
		self.__setitem__('description', description)
		self.__setitem__('layout', copy.copy(layout))

	@property
	def label(self):
		return self['label']

	@property
	def description(self):
		return self['description']

	@property
	def layout(self):
		return self['layout']

	@layout.setter
	def layout(self, value):
		self['layout'] = value

	def replace(self, old, new, recursive=True):
		new_layout = []
		replaced = False
		for item in self.layout:
			if replaced:
				new_layout.append(item)
				continue
			if isinstance(item, basestring) and item == old:
				new_layout.append(new)
				replaced = True
			elif isinstance(item, (tuple, list)):
				line = []
				for elem in item:
					if elem == old:
						replaced = True
						line.append(new)
					else:
						line.append(elem)
				new_layout.append(line)
			elif isinstance(item, ILayoutElement) and recursive:
				replaced, layout = item.replace(old, new, recursive)
				new_layout.append(item)
			else:
				new_layout.append(item)
		self.layout = new_layout

		return (replaced, self.layout)

	def remove(self, field, recursive=True):
		new_layout = []
		removed = False
		if self.exists(field):
			for item in self.layout:
				if removed:
					new_layout.append(item)
					continue
				if isinstance(item, basestring) and item != field:
					new_layout.append(item)
				elif isinstance(item, (tuple, list)):
					line = []
					for elem in item:
						if elem != field:
							line.append(elem)
						else:
							removed = True
					new_layout.append(line)
				elif isinstance(item, ILayoutElement) and recursive:
					removed, layout = item.remove(field, recursive)
					new_layout.append(item)
				else:
					removed = True
			self.layout = new_layout

		return (removed, self.layout)

	def exists(self, field):
		for item in self.layout:
			if isinstance(item, basestring) and item == field:
				return True
			elif isinstance(item, (tuple, list)):
				if field in item:
					return True
			elif isinstance(item, ILayoutElement):
				if item.exists(field):
					return True

		return False

	def insert(self, position, field):
		if position == -1:
			self.layout.insert(0, field)
			return

		fline = (position - 1) // 2
		fpos = (position - 1) % 2

		currentLine = fline

		if len(self.layout) <= currentLine or currentLine < 0:
			self.layout.append(field)
		else:
			if isinstance(self.layout[currentLine], basestring):
				if fpos == 0:
					self.layout[currentLine] = [field, self.layout[currentLine]]
				else:
					self.layout[currentLine] = [self.layout[currentLine], field]
			else:
				self.layout[currentLine].insert(fpos, field)


class Tab(ILayoutElement):

	def __init__(self, label, description='', advanced=False, layout=[], is_app_tab=False, help_text=None):
		ILayoutElement.__init__(self, label, description, layout)
		self.__setitem__('advanced', advanced)
		self.__setitem__('is_app_tab', is_app_tab)
		self.__setitem__('help_text', help_text)

	@property
	def is_app_tab(self):
		return self['is_app_tab']

	@is_app_tab.setter
	def is_app_tab(self, value):
		self['is_app_tab'] = value

	@property
	def advanced(self):
		return self['advanced']

	@advanced.setter
	def advanced(self, value):
		self['advanced'] = value


class Group(ILayoutElement):
	pass
