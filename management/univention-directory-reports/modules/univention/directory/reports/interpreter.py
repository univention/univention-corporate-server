# -*- coding: utf-8 -*-
#
# Univention Directory Reports
#  analyse a tokenized list and perform the tasks
#
# Copyright 2007-2014 Univention GmbH
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

import univention.admin.modules as ua_modules
import univention.admin.objects as ua_objects
import univention.admin.uldap as ua_ldap

from tokens import *
import admin

import univention.admin.localization
translation=univention.admin.localization.translation('univention-directory-reports')
_=translation.translate

import copy
import fnmatch
import re

class Interpreter( object ):
	def __init__( self, base_object, tokens ):
		self._base_object = base_object
		self._tokens = tokens

	def run( self, tokens = [], base_objects = [] ):
		if not tokens:
			tokens = self._tokens
		if not base_objects:
			base_objects = [ self._base_object, ]
		if not isinstance( base_objects, ( list, tuple ) ):
			base_objects = [ base_objects, ]
		for token in tokens:
			if isinstance( token, ( QueryToken, ResolveToken ) ):
				if isinstance( token, QueryToken ):
					self.query( token, base_objects[ 0 ] )
				else:
					self.resolve( token, base_objects[ 0 ] )
				if not token.objects or not len( token ):
					token.clear()
					if token.attrs.has_key( 'alternative' ):
						token.insert( 0, TextToken( token.attrs[ 'alternative' ] ) )
					continue
				if len( token.objects ) > 1:
					temp = copy.deepcopy( list( token ) )
					self.run( list( token ), token.objects[ 0 ] )
					for obj in token.objects[ 1 : ]:
						base_tokens = copy.deepcopy( temp )
						self.run( base_tokens, obj )
						token.extend( base_tokens )
				else:
					self.run( token, token.objects )
				if token.attrs.has_key( 'separator' ):
					cp = copy.deepcopy( (list( token ) ) )
					while len( token ): token.pop()
					for item in cp:
						token.append( item )
						token.append( TextToken( token.attrs[ 'separator' ] ) )
					if len( token ):
						token.pop()
				if token.attrs.has_key( 'header' ):
					token.insert( 0, TextToken( token.attrs[ 'header' ] ) )
				if token.attrs.has_key( 'footer' ):
					token.append( TextToken( token.attrs[ 'footer' ] ) )
			elif isinstance( token, AttributeToken ):
				self.attribute( token, base_objects[ 0 ] )
				if token.value:
					if token.attrs.has_key( 'append' ):
						token.value += token.attrs[ 'append' ]
					if token.attrs.has_key( 'prepend' ):
						token.value = token.attrs[ 'prepend' ] + token.value
			elif isinstance( token, PolicyToken ):
				self.policy( token, base_objects[ 0 ] )

	def resolve( self, token, base ):
		if token.attrs.has_key( 'module' ):
			attr = token.attrs.get( 'dn-attribute', None )
			if attr and base.has_key( attr ) and base[ attr ]:
				values = base[ attr ]
				if not isinstance( values, ( list, tuple ) ):
					values = [ values, ]
				for value in values:
					new_base = admin.get_object( token.attrs[ 'module' ], value )
					token.objects.append( new_base )

	def query( self, token, base ):
		if token.attrs.has_key( 'module' ):
			attr = token.attrs.get( 'start', None )
			if attr and base.has_key( attr ) and base[ attr ]:
				new_base = admin.get_object( token.attrs[ 'module' ], base[ attr ][ 0 ] )
				if not isinstance( base[ attr ], ( list, tuple ) ):
					base[ attr ] = [ base[ attr ], ]
				filter = token.attrs.get( 'pattern', None )
				if filter:
					filter = filter.split( '=', 1 )
				regex = token.attrs.get( 'regex', None )
				if regex:
					regex = regex.split( '=', 1 )
					regex[ 1 ] = re.compile( regex[ 1 ] )
				objects = self._query_recursive( base[ attr ], token.attrs[ 'next' ],
												 token.attrs[ 'module' ], filter, regex )
				token.objects.extend( objects )

	def _query_recursive( self, objects, attr, module, filter = None, regex = None ):
		_objs = []
		for dn in objects:
			obj = admin.get_object( module, dn )
			if not filter and not regex:
				_objs.append( obj )
			elif filter and obj.has_key( filter[ 0 ] ) and obj[ filter[ 0 ] ] and \
				 fnmatch.fnmatch( obj[ filter[ 0 ] ], filter[ 1 ] ):
				_objs.append( obj )
			elif regex and obj.has_key( regex[ 0 ] ) and obj[ regex[ 0 ] ] and \
				 regex[ 1 ].match( obj[ regex[ 0 ] ] ):
				_objs.append( obj )
			if not obj.has_key( attr ):
				continue

			_objs.extend( self._query_recursive( obj[ attr ], attr, module, filter, regex ) )

		return _objs

	def policy( self, token, base ):
		if token.attrs.has_key( 'module' ) and ( token.attrs.has_key( 'inherited' ) or
												 token.attrs.has_key( 'direct' ) ):
			policy = ua_objects.getPolicyReference( base, token.attrs[ 'module' ] )
			# need to call str() directly in order to force a correct translation
			token.value = str(_( 'No' ))
			if token.attrs.has_key( 'direct' ) and policy:
				token.value = str(_( 'Yes' ))
			elif token.attrs.has_key( 'inherited' ) and not policy:
				token.value = str(_( 'Yes' ))

	def attribute( self, token, base ):
		if token.attrs.has_key( 'name' ):
			if base.info.has_key( token.attrs[ 'name' ] ):
				value = base.info[ token.attrs[ 'name' ] ]
				if isinstance( value, ( list, tuple ) ):
					if not value or (type(value) is str and value.lower() == 'none'):
						if token.attrs.has_key( 'default' ):
							token.value = token.attrs[ 'default' ]
						else:
							token.value = ''
					else:
						sep = token.attrs.get( 'separator', ', ' )
						token.value = sep.join( value )
				else:
					token.value = value
			elif token.attrs.has_key( 'default' ):
				token.value = token.attrs[ 'default' ]
			if token.value == None or token.value == '':
				token.value = ''
				if token.attrs.has_key( 'default' ):
					token.value = token.attrs[ 'default' ]
