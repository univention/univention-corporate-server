# -*- coding: utf-8 -*-
#
# Univention Configuration Registry
#  Config Registry information: read information about registered Config Registry
#  variables
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

import os
import re

import univention.config_registry as ucr
import univention.info_tools as uit
try:
	from typing import Dict, List, Optional, Tuple  # noqa F401
except ImportError:
	pass

# default locale
_locale = 'de'


class Variable(uit.LocalizedDictionary):
	"""UCR variable description."""

	def __init__(self, registered=True):
		# type: (bool) -> None
		uit.LocalizedDictionary.__init__(self)
		self.value = None  # type: Optional[str]
		self._registered = registered

	def check(self):
		# type: () -> List[str]
		"""
		Check description for completeness.

		:returns: List of missing settings.
		"""
		missing = []  # type: List[str]
		if not self._registered:
			return missing

		for key in ('description', 'type', 'categories'):
			if not self.get(key, None):
				missing.append(key)
		return missing


class Category(uit.LocalizedDictionary):
	"""UCR category description."""

	def __init__(self):
		# type: () -> None
		uit.LocalizedDictionary.__init__(self)

	def check(self):
		# type: () -> List[str]
		"""
		Check description for completeness.

		:returns: List of missing settings.
		"""
		missing = []  # type: List[str]
		for key in ('name', 'icon'):
			if not self.get(key, None):
				missing.append(key)
		return missing


class ConfigRegistryInfo(object):
	"""UCR variable and category descriptions."""
	BASE_DIR = '/etc/univention/registry.info'
	CATEGORIES = 'categories'
	VARIABLES = 'variables'
	CUSTOMIZED = '_customized'
	FILE_SUFFIX = '.cfg'

	def __init__(self, install_mode=False, registered_only=True, load_customized=True):
		# type: (bool, bool, bool) -> None
		"""
		Initialize variable and category descriptions.

		:param install_mode: `True` deactivates the use of an UCR instance.
		:param registered_only: `False` creates synthetic entries for all undescribed but set variables.
		:param load_customized: `False` deactivates loading customized descriptions.
		"""
		self.categories = {}  # type: Dict[str, Category]
		self.variables = {}  # type: Dict[str, Variable]
		self.__patterns = {}  # type: Dict[str, List[Tuple[str, str]]]
		if not install_mode:
			self.__configRegistry = ucr.ConfigRegistry()  # type: Optional[ucr.ConfigRegistry]
			self.__configRegistry.load()
			self.load_categories()
			self.__load_variables(registered_only, load_customized)
		else:
			self.__configRegistry = None

	def check_categories(self):
		# type: () -> Dict[str, List[str]]
		"""
		Check all categories for completeness.

		:returns: dictionary of incomplete category descriptions.
		"""
		incomplete = {}  # type: Dict[str, List[str]]
		for name, cat in self.categories.items():
			miss = cat.check()
			if miss:
				incomplete[name] = miss
		return incomplete

	def check_variables(self):
		# type: () -> Dict[str, List[str]]
		"""
		Check variables.

		:returns: dictionary of incomplete variable descriptions.
		"""
		incomplete = {}  # type: Dict[str, List[str]]
		for name, var in self.variables.items():
			miss = var.check()
			if miss:
				incomplete[name] = miss
		return incomplete

	def read_categories(self, filename):
		# type: (str) -> None
		"""
		Load a single category description file.

		:param filename: File to load.
		"""
		cfg = uit.UnicodeConfig()
		cfg.read(filename)
		for sec in cfg.sections():
			# category already known?
			cat_name = sec.lower()
			if cat_name in self.categories:
				continue
			cat = Category()
			for name, value in cfg.items(sec):
				cat[name] = value
			self.categories[cat_name] = cat

	def load_categories(self):
		# type: () -> None
		"""Load all category description files."""
		path = os.path.join(ConfigRegistryInfo.BASE_DIR, ConfigRegistryInfo.CATEGORIES)
		if os.path.exists(path):
			for filename in os.listdir(path):
				self.read_categories(os.path.join(path, filename))

	@staticmethod
	def __pattern_sorter(args):
		# type: (Tuple) -> Tuple[Tuple[int, str], str]
		"""Sort more specific (longer) regular expressions first."""
		pattern, data = args
		return ((len(pattern), pattern), data)

	def check_patterns(self):
		# type: () -> None
		"""
		Match descriptions agains currently defined UCR variables.
		"""
		# in install mode
		if self.__configRegistry is None:
			return
		# Try more specific (longer) regular expressions first
		for pattern, data in sorted(self.__patterns.items(), key=ConfigRegistryInfo.__pattern_sorter, reverse=True):
			regex = re.compile(pattern)
			# find config registry variables that match this pattern and are
			# not already listed in self.variables
			for key, value in self.__configRegistry.items():
				if key in self.variables:
					continue
				if not regex.match(key):
					continue
				# create variable object with values
				var = Variable()
				var.value = value
				# var.update() does not use __setitem__()
				for name, value in data:
					var[name] = value
				self.variables[key] = var

	def describe_search_term(self, term):
		# type: (str) -> Dict[str, Variable]
		"""
		Try to apply a description to a search term.

		This is not complete, because it would require a complete "intersect
		two regular languages" algorithm.

		:param term: Search term.
		:returns: Dictionary mapping variable pattern to Variable info blocks.
		"""
		patterns = {}  # type: Dict[str, Variable]
		for pattern, data in sorted(self.__patterns.items(), key=ConfigRegistryInfo.__pattern_sorter, reverse=True):
			regex = re.compile(pattern)
			match = regex.search(term)
			if not match:
				regex = re.compile(term)
				match = regex.search(pattern)
			if match:
				var = Variable()
				# var.update() does not use __setitem__()
				for name, value in data:
					var[name] = value
				patterns[pattern] = var
		return patterns

	def write_customized(self):
		# type: () -> None
		"""Persist the customized variable descriptions."""
		filename = os.path.join(ConfigRegistryInfo.BASE_DIR, ConfigRegistryInfo.VARIABLES, ConfigRegistryInfo.CUSTOMIZED)
		self.__write_variables(filename)

	def __write_variables(self, filename=None, package=None):
		# type: (str, str) -> bool
		"""
		Persist the variable descriptions into a file.

		:param filename: Explicit filename for saving.
		:param package: Explicit package name.
		:raises AttributeError: if neither `filename` nor `package` are given.
		:returns: `True` on success, `False` otherwise.
		"""
		if filename:
			pass
		elif package:
			filename = os.path.join(ConfigRegistryInfo.BASE_DIR, ConfigRegistryInfo.VARIABLES, package + ConfigRegistryInfo.FILE_SUFFIX)
		else:
			raise AttributeError("neither 'filename' nor 'package' is specified")
		try:
			fd = open(filename, 'w')
		except IOError:
			return False

		cfg = uit.UnicodeConfig()
		for name, var in self.variables.items():
			cfg.add_section(name)
			for key in var.keys():
				items = var.normalize(key)
				for item, value in items.items():
					value = value
					cfg.set(name, item, value)

		cfg.write(fd)
		fd.close()

		return True

	def read_customized(self):
		# type: () -> None
		"""Read customized variable descriptions."""
		filename = os.path.join(ConfigRegistryInfo.BASE_DIR, ConfigRegistryInfo.VARIABLES, ConfigRegistryInfo.CUSTOMIZED)
		self.read_variables(filename, override=True)

	def read_variables(self, filename=None, package=None, override=False):
		# type: (str, str, bool) -> None
		"""
		Read variable descriptions.

		:param filename: Explicit filename for loading.
		:param package: Explicit package name.
		:param override: `True` to overwrite already loaded descriptions.
		:raises AttributeError: if neither `filename` nor `package` are given.
		"""
		if filename:
			pass
		elif package:
			filename = os.path.join(ConfigRegistryInfo.BASE_DIR, ConfigRegistryInfo.VARIABLES, package + ConfigRegistryInfo.FILE_SUFFIX)
		else:
			raise AttributeError("neither 'filename' nor 'package' is specified")
		cfg = uit.UnicodeConfig()
		cfg.read(filename)
		for sec in cfg.sections():
			# is a pattern?
			if sec.find('.*') != -1:
				self.__patterns[sec] = cfg.items(sec)
				continue
			# variable already known?
			if not override and sec in self.variables:
				continue
			var = Variable()
			for name, value in cfg.items(sec):
				var[name] = value
			# get current value
			if self.__configRegistry is not None:
				var.value = self.__configRegistry.get(sec, None)
			self.variables[sec] = var

	def __load_variables(self, registered_only=True, load_customized=True):
		# type: (bool, bool) -> None
		"""
		Read default and customized variable descriptions.

		:param registered_only: With default `True` only variables for which a description exists are loaded, otherwise all currently set variables are also included.
		:param load_customized: Load customized variable descriptions.
		"""
		path = os.path.join(ConfigRegistryInfo.BASE_DIR, ConfigRegistryInfo.VARIABLES)
		if os.path.exists(path):
			for entry in os.listdir(path):
				cfgfile = os.path.join(path, entry)
				if os.path.isfile(cfgfile) and cfgfile.endswith(ConfigRegistryInfo.FILE_SUFFIX) and entry != ConfigRegistryInfo.CUSTOMIZED:
					self.read_variables(cfgfile)
			self.check_patterns()
			if not registered_only and self.__configRegistry is not None:
				for key, value in self.__configRegistry.items():
					if key in self.variables:
						continue
					var = Variable(registered=False)
					var.value = value
					self.variables[key] = var
			# read customized infos afterwards to override existing entries
			if load_customized:
				self.read_customized()

	def get_categories(self):
		# type: () -> List[str]
		"""
		Return a list of category names.

		:returns: List if categories.
		"""
		return self.categories.keys()

	def get_category(self, name):
		# type: (str) -> Optional[Category]
		"""
		Returns a category object associated with the given name or None.

		:param name: Name of the category.
		:returns:
		"""
		if name.lower() in self.categories:
			return self.categories[name.lower()]
		return None

	def get_variables(self, category=None):
		# type: (str) -> Dict[str, Variable]
		"""
		Return dictionary of variable info blocks belonging to given category.

		:param category: Name of the category. `None` defaults to all variables.
		:returns: Dictionary mapping variable-name to :py:class:`Variable` instance.
		"""
		if not category:
			return self.variables
		temp = {}  # type: Dict[str, Variable]
		for name, var in self.variables.items():
			categories = var.get('categories')
			if not categories:
				continue
			if category in [_.lower() for _ in categories.split(',')]:
				temp[name] = var
		return temp

	def get_variable(self, key):
		# type: (str) -> Optional[Variable]
		"""
		Return the description of a variable.

		:param key: Variable name.
		:returns: description object or `None`.
		"""
		return self.variables.get(key, None)

	def add_variable(self, key, variable):
		# type: (str, Variable) -> None
		"""
		Add a new variable information item or overrides an old entry.

		:param key: Variable name.
		:param variable: :py:class:`Variable` instance.
		"""
		self.variables[key] = variable


def set_language(lang):
	# type: (str) -> None
	"""Set the default language."""
	global _locale
	_locale = lang
	uit.set_language(lang)
