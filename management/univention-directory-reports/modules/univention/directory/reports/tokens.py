# -*- coding: utf-8 -*-
#
# Univention Directory Reports
#  token classes
#
# Copyright 2007-2019 Univention GmbH
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


class Token(object):

	def __init__(self, name=None, attrs={}, data=None):
		self.name = name
		self.attrs = attrs
		self.data = data

	def __nonzero__(self):
		return self.name is not None


class TextToken(Token):

	def __init__(self, text=''):
		Token.__init__(self, name='<empty>', data=text)

	def __str__(self):
		return self.data


class TemplateToken(Token):

	def __init__(self, name, attrs={}):
		Token.__init__(self, name, attrs)

	def __str__(self):
		attrs = ''
		for key, value in self.attrs.items():
			attrs += '%s="%s" ' % (key, value)
		return '<@%s %s@>' % (self.name, attrs[: -1])


class IContextToken(TemplateToken, list):

	def __init__(self, name, attrs, closing):
		TemplateToken.__init__(self, name, attrs)
		list.__init__(self)
		self.closing = closing
		self.objects = []

	def clear(self):
		while self.__len__():
			self.pop()

	def __str__(self):
		content = ''
		for item in self:
			content += str(item)
		return TemplateToken.__str__(self) + content + '<@/%s@>' % self.name


class ResolveToken(IContextToken):

	def __init__(self, attrs={}, closing=False):
		IContextToken.__init__(self, 'resolve', attrs, closing)


class QueryToken(IContextToken, list):

	def __init__(self, attrs={}, closing=False):
		IContextToken.__init__(self, 'query', attrs, closing)


class HeaderToken(IContextToken, list):

	def __init__(self, attrs={}, closing=False):
		IContextToken.__init__(self, 'header', attrs, closing)


class FooterToken(IContextToken, list):

	def __init__(self, attrs={}, closing=False):
		IContextToken.__init__(self, 'footer', attrs, closing)


class AttributeToken(TemplateToken):

	def __init__(self, attrs={}, value=''):
		TemplateToken.__init__(self, 'attribute', attrs)
		self.value = value


class PolicyToken(TemplateToken):

	def __init__(self, attrs={}, value=''):
		TemplateToken.__init__(self, 'policy', attrs)
		self.value = value


class DateToken(TemplateToken):

	def __init__(self, attrs={}, value=''):
		TemplateToken.__init__(self, 'date', attrs)
		self.value = value
