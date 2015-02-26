# -*- coding: utf-8 -*-
#
# Univention Configuration Registry
#  dictionary class for localized keys
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

import ConfigParser
import re

# default locale
_locale = 'de'

class LocalizedValue( dict ):
	"""Localized description entry."""
	def __init__( self ):
		dict.__init__( self )
		self.__default = ''

	def get( self, locale = None ):
		global _locale
		if not locale:
			locale = _locale
		if locale in self:
			return self[ locale ]
		return self.__default

	def set( self, value, locale = None ):
		global _locale
		self[locale or _locale] = value

	def set_default( self, default ):
		self.__default = default

	def get_default( self ):
		return self.__default

class LocalizedDictionary( dict ):
	"""Localized descriptions."""
	_LOCALE_REGEX = re.compile('(?P<key>[a-zA-Z]*)\[(?P<lang>[a-z]*)\]$')

	def __init__( self ):
		dict.__init__( self )

	def __setitem__( self, key, value ):
		key = key.lower()
		matches = LocalizedDictionary._LOCALE_REGEX.match(key)
		# localized value?
		if matches:
			key, lang = matches.groups()
		val = self.setdefault(key, LocalizedValue())
		if matches:
			val.set(value, lang)
		else:
			val.set_default(value)

	def __getitem__( self, key ):
		key = key.lower()
		matches = LocalizedDictionary._LOCALE_REGEX.match(key)
		# localized value?
		if matches:
			key, lang = matches.groups()
		else:
			lang = None
		return dict.__getitem__(self, key).get(lang)

	def get( self, key, default = None ):
		try:
			value = self.__getitem__(key) or default
			return value
		except KeyError:
			return default

	def __contains__(self, key):
		key = key.lower()
		matches = LocalizedDictionary._LOCALE_REGEX.match(key)
		if matches:
			key = matches.group(1)
		return dict.__contains__(self, key)
	has_key = __contains__

	def __normalize_key( self, key ):
		if key not in self:
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
		if key not in self:
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
					fp.write( "%s = %s\n" % ( key, value.replace( '\n', '\n\t' ) ) )
			fp.write("\n")

def set_language( lang ):
	global _locale
	_locale = lang
