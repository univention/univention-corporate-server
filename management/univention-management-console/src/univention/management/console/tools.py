#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  JSON helper classes, locale stuff etc.
#
# Copyright 2006-2019 Univention GmbH
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

import locale

# JSON


class JSON_Object(object):

	'''Converts Python object into JSON compatible data
	structures. Types like lists, tuples and dictionary are converted
	directly. If none of these types matches the method tries to convert
	the attributes of the object and generate a dict to represent it.'''

	def _json_list(self, obj):
		result = []
		for item in obj:
			if isinstance(item, JSON_Object):
				result.append(item.json())
			else:
				result.append(item)
		return result

	def _json_dict(self, obj):
		result = {}
		for key, value in obj.items():
			if isinstance(value, JSON_Object):
				result[key] = value.json()
			else:
				result[key] = value
		return result

	def json(self):
		if isinstance(self, (list, tuple)):
			return self._json_list(self)
		elif isinstance(self, dict):
			return self._json_dict(self)
		return self._json_dict(self.__dict__)


class JSON_List(list, JSON_Object):
	pass


class JSON_Dict(dict, JSON_Object):
	pass

# locales


def locale_get():
	'''Get locale name for messages. If no specific locale is set for
	process the default setting is returned.'''
	lang, encoding = locale.getlocale(locale.LC_MESSAGES)
	if not lang:
		lang, encoding = locale.getdefaultlocale(locale.LC_MESSAGES)

	return lang
