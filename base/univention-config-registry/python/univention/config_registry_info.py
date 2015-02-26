# -*- coding: utf-8 -*-
#
# Univention Configuration Registry
#  Config Registry information: read information about registered Config Registry
#  variables
#
# Copyright 2007-2015 Univention GmbH
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
# <http://www.gnu.org/licenses/>.

import os
import re

import univention.config_registry as ucr
import univention.info_tools as uit

# default locale
_locale = 'de'

class Variable( uit.LocalizedDictionary ):
	"""UCR variable description."""
	def __init__( self, registered = True ):
		uit.LocalizedDictionary.__init__( self )
		self.value = None
		self._registered = registered

	def check( self ):
		"""Check description for completeness."""
		missing = []
		if not self._registered:
			return missing

		for key in ( 'description', 'type', 'categories' ):
			if not self.get( key, None ):
				missing.append(key)
		return missing


class Category( uit.LocalizedDictionary ):
	"""UCR category description."""
	def __init__( self ):
		uit.LocalizedDictionary.__init__( self )

	def check( self ):
		"""Check description for completeness."""
		missing = []
		for key in ( 'name', 'icon' ):
			if not self.get(key, None):
				missing.append(key)
		return missing

class ConfigRegistryInfo( object ):
	"""UCR variable and category descriptions."""
	BASE_DIR = '/etc/univention/registry.info'
	CATEGORIES = 'categories'
	VARIABLES = 'variables'
	CUSTOMIZED = '_customized'
	FILE_SUFFIX = '.cfg'

	def __init__( self, install_mode = False, registered_only = True, load_customized=True ):
		"""Initialize variable and category descriptions.

		install_mode=True deactivates the use of an UCR instance.
		registered_only=False creates syntetic entries for all undescribed but set variables.
		load_customized=False deactivates loading customized descriptions.
		"""
		self.categories = {}
		self.variables = {}
		self.__patterns = {}
		if not install_mode:
			self.__configRegistry = ucr.ConfigRegistry()
			self.__configRegistry.load()
			self.load_categories()
			self.__load_variables( registered_only, load_customized )
		else:
			self.__configRegistry = None

	def check_categories( self ):
		"""Return dictionary of incomplete category descriptions."""
		"""Check all categories for completeness."""
		incomplete = {}
		for name, cat in self.categories.items():
			miss = cat.check()
			if miss:
				incomplete[name] = miss
		return incomplete

	def check_variables( self ):
		"""Return dictionary of incomplete variable descriptions."""
		incomplete = {}
		for name, var in self.variables.items():
			miss = var.check()
			if miss:
				incomplete[name] = miss
		return incomplete

	def read_categories( self, filename ):
		"""Load a single category description file."""
		cfg = uit.UnicodeConfig()
		cfg.read( filename )
		for sec in cfg.sections():
			# category already known?
			cat_name = sec.lower()
			if cat_name in self.categories:
				continue
			cat = Category()
			for name, value in cfg.items( sec ):
				cat[ name ] = value
			self.categories[ cat_name ] = cat

	def load_categories( self ):
		"""Load all category description files."""
		path = os.path.join( ConfigRegistryInfo.BASE_DIR, ConfigRegistryInfo.CATEGORIES )
		if os.path.exists ( path ):
			for filename in os.listdir( path ):
				self.read_categories( os.path.join( path, filename ) )

	@staticmethod
	def __pattern_sorter(args):
		"""Sort more specific (longer) regular expressions first."""
		pattern, data = args
		return ((len(pattern), pattern), data)

	def check_patterns( self ):
		# in install mode
		if self.__configRegistry is None:
			return
		# Try more specific (longer) regular expressions first
		for pattern, data in sorted(self.__patterns.items(),
				key=ConfigRegistryInfo.__pattern_sorter, reverse=True):
			regex = re.compile( pattern )
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
		"""Try to apply a description to a search term.

		This is not complete, because it would require a complete "intersect
		two regular languages" algorithm.
		"""
		patterns = {}
		for pattern, data in sorted(self.__patterns.items(),
				key=ConfigRegistryInfo.__pattern_sorter, reverse=True):
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

	def write_customized( self ):
		"""Persist the customized variable descriptions."""
		filename = os.path.join( ConfigRegistryInfo.BASE_DIR, ConfigRegistryInfo.VARIABLES,
								 ConfigRegistryInfo.CUSTOMIZED )
		self.__write_variables( filename )

	def __write_variables( self, filename = None, package = None ):
		"""Persist the variable descriptions into a file."""
		if filename:
			pass
		elif package:
			filename = os.path.join( ConfigRegistryInfo.BASE_DIR, ConfigRegistryInfo.VARIABLES,
									 package + ConfigRegistryInfo.FILE_SUFFIX )
		else:
			raise AttributeError( "neither 'filename' nor 'package' is specified" )
		try:
			fd = open( filename, 'w' )
		except IOError:
			return False

		cfg = uit.UnicodeConfig()
		for name, var in self.variables.items():
			cfg.add_section( name )
			for key in var.keys():
				items = var.normalize( key )
				for item, value in items.items():
					value = value
					cfg.set( name, item, value )

		cfg.write( fd )
		fd.close()

		return True

	def read_customized( self ):
		"""Read customized variable descriptions."""
		filename = os.path.join( ConfigRegistryInfo.BASE_DIR, ConfigRegistryInfo.VARIABLES,
								 ConfigRegistryInfo.CUSTOMIZED )
		self.read_variables( filename, override = True )

	def read_variables( self, filename = None, package = None, override = False ):
		"""Read variable descriptions."""
		if filename:
			pass
		elif package:
			filename = os.path.join( ConfigRegistryInfo.BASE_DIR, ConfigRegistryInfo.VARIABLES,
									 package + ConfigRegistryInfo.FILE_SUFFIX )
		else:
			raise AttributeError( "neither 'filename' nor 'package' is specified" )
		cfg = uit.UnicodeConfig()
		cfg.read( filename )
		for sec in cfg.sections():
			# is a pattern?
			if sec.find( '.*' ) != -1:
				self.__patterns[ sec ] = cfg.items( sec )
				continue
			# variable already known?
			if not override and sec in self.variables:
				continue
			var = Variable()
			for name, value in cfg.items( sec ):
				var[ name ] = value
			# get current value
			if self.__configRegistry is not None:
				var.value = self.__configRegistry.get( sec, None )
			self.variables[ sec ] = var

	def __load_variables( self, registered_only = True, load_customized=True ):
		"""Read default and customized variable descriptions.

		With default registered_only=True only variables for which a
		description exists are loaded, otherwise all currently set variables
		are also included.
		"""
		path = os.path.join( ConfigRegistryInfo.BASE_DIR, ConfigRegistryInfo.VARIABLES )
		if os.path.exists ( path ):
			for entry in os.listdir( path ):
				cfgfile = os.path.join( path, entry )
				if os.path.isfile( cfgfile ) and cfgfile[-len(ConfigRegistryInfo.FILE_SUFFIX):] == ConfigRegistryInfo.FILE_SUFFIX and entry != ConfigRegistryInfo.CUSTOMIZED:
					self.read_variables( cfgfile )
			self.check_patterns()
			if not registered_only:
				for key, value in self.__configRegistry.items():
					if key in self.variables:
						continue
					var = Variable( registered = False )
					var.value = value
					self.variables[ key ] = var
			# read customized infos afterwards to override existing entries
			if load_customized:
				self.read_customized()

	def get_categories( self ):
		'''returns a list of category names'''
		return self.categories.keys()

	def get_category( self, name ):
		'''returns a category object associated with the given name or
		None'''
		if name.lower() in self.categories:
			return self.categories[name.lower()]
		return None

	def get_variables( self, category = None ):
		"""Return dictionary of variable info blocks belonging to given category."""
		if not category:
			return self.variables
		temp = {}
		for name, var in self.variables.items():
			categories = var.get('categories')
			if not categories:
				continue
			if category in [_.lower() for _ in categories.split(',')]:
				temp[name] = var
		return temp

	def get_variable( self, key ):
		"""Return the description of requested variable."""
		return self.variables.get( key, None )

	def add_variable( self, key, variable ):
		'''this methods adds a new variable information item or
		overrides an old entry'''
		self.variables[ key ] = variable

def set_language( lang ):
	"""Set the default language."""
	global _locale
	_locale = lang
	uit.set_language(lang)
