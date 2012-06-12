# -*- coding: utf-8 -*-
#
# Univention Management Console
#  i18n utils
#
# Copyright 2006-2012 Univention GmbH
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
from .config import ucr

from univention.lib.i18n import Locale

'''
usage:
obj = univention.management.console.Translation()
_ = obj.translate
'''

class I18N( object ):
	LOCALE_DIR = '/usr/share/univention-management-console/i18n/'

	def __init__( self, locale = None, domain = None ):
		self.mofile = None
		self.domain = domain
		self.locale = locale
		self.load( locale, domain )

	def load( self, locale = None, domain = None ):
		if locale is not None:
			self.locale = locale
		if domain is not None:
			self.domain = domain
		if self.locale is None or self.domain is None:
			LOCALE.info( 'Locale or domain missing. Stopped loading of translation' )
			return

		LOCALE.info( 'Loading locale %s for domain %s' % ( self.locale, self.domain ) )
		filename = os.path.join( I18N.LOCALE_DIR, self.locale.language, '%s.mo' % self.domain )
		if not os.path.isfile( filename ):
			filename = os.path.join( I18N.LOCALE_DIR, '%s_%s' % ( self.locale.language, self.locale.territory ), '%s.mo' % self.domain )
			if not os.path.isfile( filename ):
				LOCALE.warn( ' Could not find translation file' )
				self.mofile = None
				return

		LOCALE.info( 'Found translation file %s' % filename )
		self.mofile = polib.mofile( filename )

	def exists( self, message ):
		return self.mofile is not None and self.mofile.find( message, by = 'msgid' )

	def _( self, message ):
		if self.mofile:
			entry = self.mofile.find( message, by = 'msgid' )
			if entry is not None:
				return entry.msgstr

		return message

class I18N_Manager( dict ):
	def __init__( self ):
		lang, codeset = getdefaultlocale()
		if lang is None:
			lang = 'C'
		self.locale = Locale( lang )

	def set_locale( self, locale ):
		LOCALE.info( 'Setting locale to %s' % locale )
		self.locale.parse( locale )
		for domain, i18n in self.items():
			LOCALE.info( 'Loading translation for domain %s' % domain )
			i18n.load( locale = self.locale )

	def __setitem__( self, key, value ):
		value.domain = key
		dict.__setitem__( self, key, value )

	def _( self, message, domain = None ):
		LOCALE.info( 'Searching for %s translation of "%s' % ( str( self.locale ), message ) )
		if domain is not None:
			if not domain in self:
				self[ domain ] = I18N( self.locale, domain )
			return self[ domain ]._( message )
		for domain, i18n in self.items():
			LOCALE.info( 'Checking domain %s for translation' % domain )
			if i18n.exists( message ):
				return i18n._( message )

		return message

