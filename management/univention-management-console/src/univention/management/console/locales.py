# -*- coding: utf-8 -*-
#
# Univention Management Console
#  i18n utils
#
# Copyright 2006-2011 Univention GmbH
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

import gettext
from locale import getlocale, getdefaultlocale
import re
import os

import polib

from .log import LOCALE

'''
usage:
obj = univention.management.console.Translation()
_ = obj.translate
'''

class LocaleNotFound( Exception ):
	pass

class Locale( object ):
	'''Represents a locale specification and provides simple access to
	language, territory, codeset and modifier'''

	REGEX = re.compile( '(?P<language>[a-z]{2})(_(?P<territory>[A-Z]{2}))?(.(?P<codeset>[a-zA-Z-0-9]+)(@(?P<modifier>.+))?)?' )

	def __init__( self, locale = None ):
		self.language = None
		if locale is not None:
			self.parse( locale )

	def parse( self, locale ):
		if not isinstance( locale, basestring ):
			raise TypeError( 'locale must be of type string' )
		regex = Locale.REGEX.match( locale )
		if not regex:
			raise AttributeError( 'attribute does not match locale specification language[_territory][.codeset][@modifier]' )

		for key, value in regex.groupdict().items():
			setattr( self, key, value )

	def __str__( self ):
		text = self.language
		if getattr( self, 'territory' ) is not None:
			text += '_%s' % self.territory
		if getattr( self, 'codeset' ) is not None:
			text += '.%s' % self.codeset
		if getattr( self, 'modifier' ) is not None:
			text += '@%s' % self.modifier
		return text

class NullTranslation( object ):
	def __init__( self, namespace = None, locale_spec = None, localedir = None ):
		self.domain = namespace
		self._translation = None
		self._localedir = localedir
		self._localespec = None
		self._locale = locale_spec

	def _set_domain( self, namespace ):
		if namespace is not None:
			self._domain = namespace.replace( '/', '-' ).replace( '.', '-' )
		else:
			self._domain = None

	domain =property( fset = _set_domain )

	def _get_locale( self ):
		return self._localespec

	def _set_locale( self, locale_spec = None ):
		if locale_spec is None:
			return
		try:
			self._localespec = Locale( locale_spec )
		except (AttributeError, TypeError ), e:
			LOCALE.error( 'Failed to set locale: %s' % str( e ) )
			raise

		LOCALE.warn( 'Setting locale to %s' % self.locale )

	locale = property( fget = _get_locale, fset = _set_locale )

	def translate( self, message ):
		if self._translation is None:
			return message
		return self._translation.ugettext( message )

	_ = translate

class Translation( NullTranslation ):
	def set_language( self, language = None ):
		self.locale = language

		if not self._domain:
			return

		if self.locale is None:
			LOCALE.info( 'Trying to determine default locale settings' )
			try:
				lang = getlocale( locale.LC_MESSAGES )
				if lang[ 0 ] is None:
					lang = getdefaultlocale()
				language = lang[ 0 ]
				if language is None:
					language = 'de'
			except locale.error:
				LOCALE.error( 'Failed to retrieve default locale' )
				raise LocaleNotFound()

		try:
			self._translation = gettext.translation( self._domain, languages = ( self.locale.language, ), localedir = self._localedir )
		except IOError, e:
			LOCALE.warn( 'Failed to set locale to %s (locale directory: %s): %s' % ( self.locale.language, str( self._localedir ), str( e ) ) )
			try:
				self._translation = gettext.translation( self._domain, languages = ( '%s_%s' % ( self.locale.language, self.locale.territory ), ), localedir = self._localedir )
			except IOError:
				self._translation = None
				LOCALE.error( 'Could not find translation file for language %s of domain %s' % ( language, self._domain ) )

class I18N_Error( Exception ):
	pass

class I18N( object ):
	LOCALE_DIR = '/usr/share/univention-management-console/i18n/'

	def __init__( self, locale, domain ):
		self.mofile = None
		self.domain = domain
		self.locale = locale
		self.load( locale, domain )

	def load( self, locale = None, domain = None ):
		if locale is not None:
			self.locale = locale
		if domain is not None:
			self.domain = domain
		filename = os.path.join( I18N.LOCALE_DIR, self.locale.language, '%s.mo' % self.domain )
		if not os.path.isfile( filename ):
			filename = os.path.join( I18N.LOCALE_DIR, '%s_%s' % ( self.locale.language, self.locale.territory ), '%s.mo' % self.domain )
			if not os.path.isfile( filename ):
				raise I18N_Error( 'No translation file found' )

		self.mofile = polib.mofile( filename )

	def exists( self, message ):
		return self.mofile.find( message, by = 'msgid' )

	def _( self, message ):
		entry = self.mofile.find( message, by = 'msgid' )
		if entry is not None:
			return entry.msgstr

		return message

class I18N_Manager( dict ):
	def __init__( self ):
		self.locale = Locale()

	def set_locale( self, locale ):
		self.locale.parse( locale )
		for i18n in self.values():
			i18n.load( locale = self.locale )

	def _( self, message, domain = None ):
		if domain is not None:
			if not domain in self:
				self[ domain ] = I18N( self.locale, domain )
			return self[ domain ]._( message )
		for domain, i18n in self.items():
			if i18n.exists( message ):
				return i18n._( message )

		return message

