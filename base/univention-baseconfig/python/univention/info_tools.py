# -*- coding: utf-8 -*-
#
# Univention Baseconfig
#  dictionary class for localized keys
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
import re
import string

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

class LocalizedDictionary( dict ):
	_locale_regex = re.compile( '(?P<key>[a-zA-Z]*)\[(?P<lang>[a-z]*)\]' )

	def __init__( self ):
		dict.__init__( self )

	def __setitem__( self, key, value ):
		key = string.lower( key )
		if not isinstance( key, unicode ):
			key = unicode( key, 'iso-8859-1' )
		if not isinstance( value, unicode ):
			value = unicode( value, 'iso-8859-1' )
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
				value = dict.__getitem__( self, grp[ 'key' ] )
				return value.get( value, grp[ 'lang' ] )
		else:
			if self.has_key( key ):
				return dict.__getitem__( self, key ).get()

		return None

	def get( self, key, default = None ):
		if self.has_key( key ):
			return self.__getitem__( key )
		return default

	def has_key( self, key ):
		return dict.has_key( self, string.lower( key ) )

	def __normalize_key( self, key ):
		if not self.has_key( key ):
			return {}

		temp = {}
		variable = dict.__getitem__( self, key )
		for locale, value in variable.items():
			temp[ '%s[%s]' % ( key, locale ) ] = value

		if variable.get_default():
			temp[ key ] = variable.get_default()

		return temp

	def normalize( self, key = None ):
		if key:
			return self.__normalize_key( key )
		temp = {}
		for key in self.keys():
			temp.update( self.__normalize_key( key ) )
		return temp

	def get_dict( self, key ):
		if not self.has_key( key ):
			return {}
		return dict.__getitem__( self, key )

	def __eq__( self, other ):
		if not isinstance( other, dict ):
			return False
		me = self.normalize()
		you = other.normalize()
		return dict.__eq__( me, you )

	def __ne__( self, other ):
		return not self.__eq__( other )

# my config parser
class UnicodeConfig( ConfigParser.ConfigParser ):
	def __init__( self ):
		ConfigParser.ConfigParser.__init__( self )

	def write( self, fp ):
		"""Write an .ini-format representation of the configuration state."""
		if self._defaults:
			fp.write("[%s]\n" % DEFAULTSECT)
			for (key, value) in self._defaults.items():
				fp.write("%s = %s\n" % (key, str(value).replace('\n', '\n\t')))
			fp.write("\n")
		for section in self._sections:
			fp.write("[%s]\n" % section)
			for (key, value) in self._sections[section].items():
				if key != "__name__":
					if not isinstance( value, unicode ):
						value = unicode( value, 'iso-8859-1' )
					if not isinstance( key, unicode ):
						key = unicode( key, 'iso-8859-1' )
					fp.write( "%s = %s\n" % ( key.encode( 'utf8' ),
											  value.encode( 'utf8' ).replace( '\n', '\n\t' )
) )
			fp.write("\n")


def set_language( lang ):
	global _locale
	_locale = lang
