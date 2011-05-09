# -*- coding: utf-8 -*-
#
# Univention Management Console
#  UMC syntax definitions
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

import os
import re
import sys
import locales
import xml.parsers.expat

from tools import ElementTree
import verify

_ = locales.Translation( 'univention.management.console' ).translate

class XML_Definition( ElementTree ):
	'''Definition of a syntax class'''
	def __init__( self, root = None, filename = None ):
		ElementTree.__init__( self, element = root, file = filename )

	@property
	def name( self ):
		return self._root.get( 'name' )

	@property
	def base( self ):
		return self._root.get( 'base' )

	@property
	def regex_invalid( self ):
		tag = self.find( 'regex-invalid' )
		if tag != None:
			return tag.text
		return None

	@property
	def regex( self ):
		tag = self.find( 'regex' )
		if tag != None:
			return tag.text
		return None

	@property
	def item( self ):
		item = self.find( 'item' )
		if not item:
			return ( None, None )
		return ( item.get( 'key' ), item.get( 'value' ) )

	@property
	def choices( self ):
		return [ elem.text for elem in self.findall( 'choices' ) ]

	@property
	def verify_function( self ):
		verify_tag = self.find( 'verify' )
		if verify_tag != None:
			return verify_tag.get( 'function' )
		return None

class Manager( dict ):
	'''Manager of all available syntax definitions'''

	DIRECTORY = os.path.join( sys.prefix, 'share/univention-management-console/syntax' )
	def __init__( self ):
		dict.__init__( self )
		self.load()

	def get( self, name ):
		if name in self:
			return self[ name ]

		return None

	def load( self ):
		self.clear()
		for filename in os.listdir( Manager.DIRECTORY ):
			if not filename.endswith( '.xml' ):
				continue
			try:
				definitions = ElementTree( file = os.path.join( Manager.DIRECTORY, filename ) )
				for syntax_elem in definitions.findall( 'definitions/syntax' ):
					syntax = XML_Definition( root = syntax_elem )
					self[ syntax.name ] = syntax
			except xml.parsers.expat.ExpatError:
				continue

	def verify( self, syntax_name, value ):
		syntax = self.get( syntax_name )
		if not syntax:
			raise verify.SyntaxVerificationError( _( 'Unknown syntax %s' ) % syntax_name )

		verify_func = None
		if not syntax.verify_function:
			if syntax.base:
				syntax_base = self.get( syntax.base )
				if syntax_base and syntax_base.verify_function:
					verify_func = syntax_base.verify_function
		else:
			verify_func = syntax.verify_function

		if not verify_func:
			raise verify.SyntaxVerificationError( _( 'Base type verification failed (type %(base)s): no verify function defined' ) % { 'base' : syntax.name } )

		func = getattr( verify, verify_func )

		if not func:
			raise verify.SyntaxVerificationError( _( 'Base type verification failed (type %(base)s): function to verify syntax could not be found (%(function)s)' ) % { 'base' : syntax.name, 'function' : syntax.verify_function } )

		func( value, syntax, self.verify )

		return True

verify.import_verification_functions()
