# -*- coding: utf-8 -*-
#
# Univention Management Console
#  class representing a link object within a UMCP dialog
#
# Copyright 2006-2010 Univention GmbH
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

import base

import univention.management.console.locales as locales
import univention.management.console.tools as umct

_ = locales.Translation( 'univention.management.console.dialog' ).translate

class Link( base.Text ):
	def __init__( self, description = '', link = '', icon = None, icon_and_text = False, attributes = {} ):
		base.Text.__init__( self, description, attributes )
		self._link = link
		self._icon = icon
		self._icon_and_text = icon_and_text
		self._icon_size = umct.SIZE_MEDIUM

	def show_icon_and_text( self ):
		return self._icon_and_text

	def get_icon( self ):
		return self._icon

	def get_icon_size( self ):
		return self._icon_size

	def set_icon_size( self, size ):
		self._icon_size = size

	def get_link( self ):
		return self._link

	def set_link( self, link ):
		'''
		A given link may be the next request or just a string.
		The latter needs to be parseable as a href-uri in html.
		'''
		self._link = link

class JS_Link( Link ):
	def __init__( self, description = '', function = '', *args ):
		Link.__init__( self, description )
		self.set_link( function, *args )

	def set_link( self, function, *args ):
		self._link = JS_Link.invoke_js( function, *args )

	@staticmethod
	def invoke_js( function, *args ):
		parameters = []
		for arg in args:
			if isinstance( arg, ( tuple, list ) ):
				parameters.append( "new Array( '%s' )" % "', '".join( arg ) )
			elif isinstance( arg, bool ):
				parameters.append( str( arg ).lower() )
			elif isinstance( arg, ( int, float ) ):
				parameters.append( str( arg ) )
			else:
				parameters.append( "'%s'" % str( arg ) )

		return 'javascript:%s(%s)' % ( function, ', '.join( parameters ) )

class ToggleCheckboxes( base.HTML ):
	def __init__( self ):
		base.HTML.__init__( self )

	def checkboxes( self, ids ):
		jsall = JS_Link.invoke_js( 'umc_checkbox_toggle', ids, True )
		jsnone = JS_Link.invoke_js( 'umc_checkbox_toggle', ids, False )
		self._text = '%s&nbsp;(<a href="%s">%s</a>/<a href="%s">%s</a>)' % ( _( 'Select' ), jsall,_( 'All' ), jsnone, _( 'None' ) )

	def __unicode__( self ):
		return unicode( self._text )

	def __str__( self ):
		return self._text

LinkTypes = ( type( Link() ), type( JS_Link() ), type( ToggleCheckboxes() ) )
