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
import locale

from .log import *

'''
usage:
obj = univention.management.console.Translation()
_ = obj.translate
'''

class LocaleNotFound( Exception ):
	pass

class NullTranslation( object ):
	def __init__( self, namespace, language = None ):
		self._domain = namespace.replace( '/', '-' ).replace( '.', '-' )
		self._translation = None
		self.set_language( language )

	def set_language( self, language = None ):
		pass

	def translate( self, message ):
		return message

	_ = translate

class Translation( NullTranslation ):
	def set_language( self, language ):
		if language is None:
			LOCALE.info( 'Trying to determine default locale settings' )
			try:
				lang = locale.getlocale( locale.LC_MESSAGES )
				language = lang[ 0 ]
				if language is None:
					language = 'de'
			except locale.error:
				LOCALE.error( 'Failed to retrieve default locale' )
				raise LocaleNotFound()

		try:
			self._translation = gettext.translation( self._domain, languages = ( language, ) )
		except IOError:
			LOCALE.error( 'Could not find locale %s for domain %s' % ( language, self._domain ) )
			raise LocaleNotFound()

	def translate( self, message ):
		return self._translation.ugettext( message )
