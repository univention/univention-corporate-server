# -*- coding: utf-8 -*-
#
# Copyright 2018-2019 Univention GmbH
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
# you and Univention.
#
# This program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <https://www.gnu.org/licenses/>.

from collections import OrderedDict
from typing import Any, Dict, Iterable, Text, TypeVar

PluginTV = TypeVar('PluginTV', bound='univention.udm.plugins.Plugin')


class Plugin(type):
	"""
	Meta class for plugins.
	"""
	def __new__(mcs, name, bases, attrs):  # type: (Plugin, str, Iterable[str], Dict[str, Any]) -> PluginTV
		new_cls = super(Plugin, mcs).__new__(mcs, name, bases, attrs)
		Plugins.add_plugin(new_cls)
		return new_cls

class Plugins(object):
	"""
	Register `Plugin` subclasses and iterate over them.
	"""

	_plugins = None  # type: OrderedDict
	_imported = {}  # type: Dict[Text, bool]

	def __init__(self, python_path):  # type: (Text) -> None
		"""
		:param str python_path: fully dotted Python path that the plugins will
			be found below
		"""
		...

	@classmethod
	def add_plugin(cls, plugin):  # type: (PluginTV) -> None
		"""
		Called by `Plugin` meta class to register a new `Plugin` subclass.

		:param type plugin: a `Plugin` subclass
		"""
		...

	def __iter__(self):  # type: () -> PluginTV
		"""
		Iterator for registered `Plugin` subclasses.

		:return: `Plugin` subclass
		:rtype: type
		"""
		...

	def load(self):  # type: () -> None
		"""Load plugins."""
		...
