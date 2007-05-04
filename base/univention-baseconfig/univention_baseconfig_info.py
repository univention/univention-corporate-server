#
# Univention Baseconfig
#  Baseconfig information: read information about registered Baseconfig
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

import ConfigParser
import locale
import os
import re
import string

import univention_baseconfig

# default locale
_locale = 'de'

class LocalizedValue( dict ):
	def __init__( self ):
		dict.__init__( self )
		self.__default = ''

	def get( self, locale = None ):
		global _locale
		if not locale:
			locale = _locale
		if self.has_key( locale ):
			return self[ locale ]
		return self.__default

	def set( self, value, locale = None ):
		global _locale
		if locale:
			self[ locale ] = value
		else:
			self[ _locale ] = value

	def set_default( self, default ):
		self.__default = default

	def get_default( self ):
		return self.__default

	def __str__( self ):
		if self.__default:
			return "%s->%s" % ( dict.__str__( self ), self.__default )
		else:
			return "%s->None" % dict.__str__( self )

class LocalizedDictionary( dict ):
	_locale_regex = re.compile( '(?P<key>[a-zA-Z]*)\[(?P<lang>[a-z]*)\]' )

	def __init__( self ):
		dict.__init__( self )

	def __setitem__( self, key, value ):
		key = string.lower( key )
		matches = LocalizedDictionary._locale_regex.match( key )
		# localized value?
		if matches:
			grp = matches.groupdict()
			if not self.has_key( grp[ 'key' ] ):
				dict.__setitem__( self, grp[ 'key' ], LocalizedValue() )
			dict.__getitem__( self, grp[ 'key' ] ).set( value, grp[ 'lang' ] )
		else:
			if not self.has_key( key ):
				dict.__setitem__( self, key, LocalizedValue() )
			dict.__getitem__( self, key ).set_default( value )

	def __getitem__( self, key ):
		key = string.lower( key )
		matches = LocalizedDictionary._locale_regex.match( key )
		# localized value?
		if matches:
			grp = matches.groupdict()
			if self.has_key( grp[ 'key' ] ):
				value = dict.__getitem__( self,grp[ 'key' ] )
				return value.get( value, grp[ 'lang' ] )
		else:
			if self.has_key( key ):
				return dict.__getitem__( self, key ).get()

		return None

	def has_key( self, key ):
		return dict.has_key( self, string.lower( key ) )

	def normalize( self, key ):
		if not self.has_key( key ):
			return {}
		temp = {}
		variable = dict.__getitem__( self, key )
		for locale, value in variable.items():
			temp[ '%s[%s]' % ( key, locale ) ] = value

		if variable.get_default():
			temp[ key ] = variable.get_default()

		return temp

class Variable( LocalizedDictionary ):
	def __init__( self ):
		LocalizedDictionary.__init__( self )
		self.value = None

	def check( self ):
		for key in ( 'description', 'type', 'categories' ):
			if not self.has_key( key ) or not self[ key ]:
				return False

		return True

class Category( LocalizedDictionary ):
	def __init__( self ):
		LocalizedDictionary.__init__( self )

	def check( self ):
		for key in ( 'name', 'icon' ):
			if not self.has_key( key ) or not self[ key ]:
				return False

		return True

class BaseconfigInfo( object ):
	BASE_DIR = '/etc/univention/base.info'
	CATEGORIES = 'categories'
	VARIABLES = 'variables'
	FILE_SUFFIX = '.cfg'

	def __init__( self, install_mode = False ):
		self.categories = {}
		self.variables = {}
		self.__patterns = {}
		if not install_mode:
			self.__baseConfig = univention_baseconfig.baseConfig()
			self.__baseConfig.load()
			self.__load_categories()
			self.__load_variables()
		else:
			self.__baseConfig = None

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
		cfg = ConfigParser.ConfigParser()
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

	def __load_categories( self ):
		path = os.path.join( BaseconfigInfo.BASE_DIR, BaseconfigInfo.CATEGORIES )
		for filename in os.listdir( path ):
			self.read_categories( os.path.join( path, filename ) )

	def check_patterns( self ):
		# in install mode
		if not self.__baseConfig:
			return
		for pattern, data in self.__patterns.items():
			regex = re.compile( pattern )
			vars = []
			# find baseconfig variables that match this pattern and are
			# not already listed in self.variables
			for bvar in self.__baseConfig.keys():
				if regex.match( bvar ) and not bvar in self.variables.keys():
					# Does another pattern match this variable too?
					if not bvar in vars:
						vars.append( bvar )

			# create variable object with values
			var = Variable()
			for name, value in data:
				var[ name ] = value

			# add a reference for each baseconfig variable to the
			# Variable object
			for key in vars:
				self.variables[ key ] = var

		# all patterns processed
		self.__patterns = {}

	def write_variables( self, filename = None, package = None ):
		if not filename and not package:
			raise AttributeError( "neither 'filename' nor 'package' is specified" )
		if not filename:
			filename = os.path.join( BaseconfigInfo.BASE_DIR,
									 BaseconfigInfo.VARIABLES,
									 package + BaseconfigInfo.FILE_SUFFIX )
		try:
			fd = open( filename, 'w' )
		except:
			return False

		cfg = ConfigParser.ConfigParser()
		for name, var in self.variables.items():
			cfg.add_section( name )
			for key in var.keys():
				items = var.normalize( key )
				for item, value in items.items():
					cfg.set( name, item, value )

		cfg.write( fd )
		fd.close()

		return True

	def read_variables( self, filename = None, package = None ):
		if not filename and not package:
			raise AttributeError( "neither 'filename' nor 'package' is specified" )
		if not filename:
			filename = os.path.join( BaseconfigInfo.BASE_DIR,
									 BaseconfigInfo.VARIABLES,
									 package + BaseconfigInfo.FILE_SUFFIX )
		cfg = ConfigParser.ConfigParser()
		cfg.read( filename )
		for sec in cfg.sections():
			# is a pattern?
			if sec.find( '.*' ) != -1:
				self.__patterns[ sec ] = cfg.items( sec )
				continue
			# variable already known?
			if sec in self.variables.keys():
				continue
			var = Variable()
			for name, value in cfg.items( sec ):
				var[ name ] = value
			if self.__baseConfig and self.__baseConfig.has_key( sec ):
				var.value = self.__baseConfig[ sec ]
			self.variables[ sec ] = var

	def __load_variables( self ):
		path = os.path.join( BaseconfigInfo.BASE_DIR, BaseconfigInfo.VARIABLES )
		for entry in os.listdir( path ):
			cfgfile = os.path.join( path, entry )
			if os.path.isfile( cfgfile ):
				self.read_variables( cfgfile )
		self.check_patterns()

	def get_categories( self ):
		'''returns a list fo category names'''
		return self.categories.keys()

	def get_category( self, name ):
		'''returns a category object assoziated with the given name or
		None'''
		if self.categories.has_key( name ):
			return self.categories[ name ]
		return None

	def get_variables( self, category = None ):
		if not category:
			return self.variables
		temp = {}
		for name, var in self.variables.items():
			if category in var[ 'categories' ].split( ',' ):
				temp[ name ] = var
		return temp

	def add_variable( self, key, variable ):
		'''this methods adds a new variable information item or
		overrides an old entry'''
		if variable.check():
			self.variables[ key ] = variable

def set_language( lang ):
	global _locale
	_locale = lang

if __name__ == '__main__':
	import sys

	if len( sys.argv ) > 1:
		info = BaseconfigInfo( install_mode = False )
		info.read_variables( sys.argv[ 1 ] )
		var = Variable()
		var[ 'description[de]' ] = 'Ein Test'
		var[ 'description[en]' ] = 'A Test'
		var[ 'type' ] = 'str'
		var[ 'categories' ] = 'TestCat'
		info.add_variable( 'test/1', var )
		info.write_variables( package = 'test-package' )
	else:
		info = BaseconfigInfo()
	print 'Variables:', info.variables.keys()
	print 'Categories:', info.categories.keys()
