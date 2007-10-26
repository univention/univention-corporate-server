# -*- coding: utf-8 -*-
#
# Univention Configuration Registry
#  Config Registry information: read information about registered Config Registry
#  variables
#
# Copyright (C) 2007 Univention GmbH
#
# http://www.univention.de/
#
# All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# Binary versions of this file provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import locale
import os
import re
import string

import univention.config_registry as ucr
import univention.info_tools as uit

# default locale
_locale = 'de'

class Variable( uit.LocalizedDictionary ):
	def __init__( self, registered = True ):
		uit.LocalizedDictionary.__init__( self )
		self.value = None
		self._registered = registered

	def check( self ):
		if not self._registered:
			return True

		for key in ( 'description', 'type', 'categories' ):
			if not self.get( key, None ):
				return False

		return True


class Category( uit.LocalizedDictionary ):
	def __init__( self ):
		uit.LocalizedDictionary.__init__( self )

	def check( self ):
		for key in ( 'name', 'icon' ):
			if not self.has_key( key ) or not self[ key ]:
				return False

		return True

class ConfigRegistryInfo( object ):
	BASE_DIR = '/etc/univention/registry.info'
	CATEGORIES = 'categories'
	VARIABLES = 'variables'
	CUSTOMIZED = '_customized'
	FILE_SUFFIX = '.cfg'

	def __init__( self, install_mode = False, registered_only = True ):
		self.categories = {}
		self.variables = {}
		self.__patterns = {}
		if not install_mode:
			self.__configRegistry = ucr.ConfigRegistry()
			self.__configRegistry.load()
			self.load_categories()
			self.__load_variables( registered_only )
		else:
			self.__configRegistry = None

	def check_categories( self ):
		failed = []
		for name, cat in self.categories.items():
			if not cat.check():
				failed.append( name )
		return failed

	def check_variables( self ):
		failed = []
		for name, var in self.variables.items():
			if not var.check():
				failed.append( name )
		return failed

	def read_categories( self, filename ):
		cfg = uit.UnicodeConfig()
		cfg.read( filename )
		for sec in cfg.sections():
			# category already known?
			cat_name = string.lower( sec )
			if cat_name in self.categories.keys():
				continue
			cat = Category()
			for name, value in cfg.items( sec ):
				cat[ name ] = value
			self.categories[ cat_name ] = cat

	def load_categories( self ):
		path = os.path.join( ConfigRegistryInfo.BASE_DIR, ConfigRegistryInfo.CATEGORIES )
		for filename in os.listdir( path ):
			self.read_categories( os.path.join( path, filename ) )

	def check_patterns( self ):
		# in install mode
		if self.__configRegistry == None:
			return
		for pattern, data in self.__patterns.items():
			regex = re.compile( pattern )
			vars = []
			# find config registry variables that match this pattern and are
			# not already listed in self.variables
			for bvar in self.__configRegistry.keys():
				if regex.match( bvar ) and not bvar in self.variables.keys():
					# Does another pattern match this variable too?
					if not bvar in vars:
						vars.append( bvar )

			# add a reference for each config registry variable to the
			# Variable object
			for key in vars:
				# create variable object with values
				var = Variable()
				for name, value in data:
					var[ name ] = value
				var.value = self.__configRegistry.get( key, None )
				self.variables[ key ] = var

		# all patterns processed
		self.__patterns = {}

	def write_customized( self ):
		filename = os.path.join( ConfigRegistryInfo.BASE_DIR, ConfigRegistryInfo.VARIABLES,
								 ConfigRegistryInfo.CUSTOMIZED )
		self.__write_variables( filename )

	def __write_variables( self, filename = None, package = None ):
		if not filename and not package:
			raise AttributeError( "neither 'filename' nor 'package' is specified" )
		if not filename:
			filename = os.path.join( ConfigRegistryInfo.BASE_DIR, ConfigRegistryInfo.VARIABLES,
									 package + ConfigRegistryInfo.FILE_SUFFIX )
		try:
			fd = open( filename, 'w' )
		except:
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
		filename = os.path.join( ConfigRegistryInfo.BASE_DIR, ConfigRegistryInfo.VARIABLES,
								 ConfigRegistryInfo.CUSTOMIZED )
		self.read_variables( filename, override = True )

	def read_variables( self, filename = None, package = None, override = False ):
		if not filename and not package:
			raise AttributeError( "neither 'filename' nor 'package' is specified" )
		if not filename:
			filename = os.path.join( ConfigRegistryInfo.BASE_DIR, ConfigRegistryInfo.VARIABLES,
									 package + ConfigRegistryInfo.FILE_SUFFIX )
		cfg = uit.UnicodeConfig()
		cfg.read( filename )
		for sec in cfg.sections():
			# is a pattern?
			if sec.find( '.*' ) != -1:
				self.__patterns[ sec ] = cfg.items( sec )
				continue
			# variable already known?
			if not override and sec in self.variables.keys():
				continue
			var = Variable()
			for name, value in cfg.items( sec ):
				var[ name ] = value
			# set current value
			if self.__configRegistry != None:
				var.value = self.__configRegistry.get( sec, None )
			self.variables[ sec ] = var

	def __load_variables( self, registered_only = True ):
		path = os.path.join( ConfigRegistryInfo.BASE_DIR, ConfigRegistryInfo.VARIABLES )
		for entry in os.listdir( path ):
			cfgfile = os.path.join( path, entry )
			if os.path.isfile( cfgfile ) and cfgfile[-len(ConfigRegistryInfo.FILE_SUFFIX):] == ConfigRegistryInfo.FILE_SUFFIX and entry != ConfigRegistryInfo.CUSTOMIZED:
				self.read_variables( cfgfile )
		self.check_patterns()
		if not registered_only:
			for key, value in self.__configRegistry.items():
				if self.variables.has_key( key ):
					continue
				var = Variable( registered = False )
				var.value = value
				self.variables[ key ] = var
		# read customized infos afterwards to override existing entries
		self.read_customized()

	def get_categories( self ):
		'''returns a list of category names'''
		return self.categories.keys()

	def get_category( self, name ):
		'''returns a category object associated with the given name or
		None'''
		if self.categories.has_key( string.lower( name ) ):
			return self.categories[ string.lower( name ) ]
		return None

	def get_variables( self, category = None ):
		if not category:
			return self.variables
		temp = {}
		for name, var in self.variables.items():
			if not var[ 'categories' ]: continue
			if category in map( lambda x: string.lower( x ), var[ 'categories' ].split( ',' ) ):
				temp[ name ] = var
		return temp

	def get_variable( self, key ):
		return self.variables.get( key, None )

	def add_variable( self, key, variable ):
		'''this methods adds a new variable information item or
		overrides an old entry'''
		if variable.check():
			self.variables[ key ] = variable

def set_language( lang ):
	global _locale
	_locale = lang
