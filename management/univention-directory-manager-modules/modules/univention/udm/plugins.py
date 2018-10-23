# -*- coding: utf-8 -*-
#
# Copyright 2018 Univention GmbH
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
# <http://www.gnu.org/licenses/>.

import importlib
import os.path
from glob import glob
from collections import OrderedDict

class Plugin(type):
	def __new__(mcs, name, bases, attrs):
		new_cls = super(Plugin, mcs).__new__(mcs, name, bases, attrs)
		Plugins.add_plugin(new_cls)
		return new_cls

class Plugins(object):
	_plugins = OrderedDict()  # If only I had OrderedSet()...
	_imported = {}

	def __init__(self, python_paths):
		self.python_paths = python_paths
		for python_path in python_paths:
			self._imported.setdefault(python_path, False)

	@classmethod
	def add_plugin(cls, plugin):
		cls._plugins[plugin] = True

	def __iter__(self):
		self._import()
		for plugin in self._plugins:
			if any(plugin.__module__.startswith(python_path) for python_path in self.python_paths):
				yield plugin

	def _import(self):
		for python_path in self.python_paths:
			self._import_path(python_path)

	def _import_path(self, python_path):
		if self._imported.get(python_path):
			return
		base_module = importlib.import_module(python_path)
		base_module_dir = os.path.dirname(base_module.__file__)
		path = os.path.join(base_module_dir, '*.py')
		for pymodule in glob(path):
			pymodule_name = os.path.basename(pymodule)[:-3]  # without .py
			importlib.import_module('{}.{}'.format(python_path, pymodule_name))
		self._imported[python_path] = True

