#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  base classes for UMCP dialogs
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

import copy as copy_module

import base

class Element( object ):
	__counter = 0
	def __init__( self, attributes = {} ):
		self.__id = None
		self.__attributes = copy_module.deepcopy( attributes )
		self.__create_id()

	def __str__( self ):
		return self.__id

	def __setitem__( self, key, value ):
		self.__attributes[ key ] = value

	def __delitem__( self, key ):
		if self.__attributes.has_key( key ):
			del self.__attributes[ key ]

	def __getitem__( self, key ):
		if key in self.__attributes:
			return self.__attributes[ key ]
		return None

	def __contains__( self, key ):
		return key in self.__attributes

	def __create_id( self ):
		self.__id = '%s%d' % ( self.type(), Element.__counter )
		Element.__counter += 1

	def has_attributes( self ):
		return len( self.__attributes ) > 0

	def attributes( self ):
		return self.__attributes

	def recreate_id( self ):
		self.__create_id()

	def id( self ):
		return self.__id

	def type( self ):
		return self.__class__.__name__

class Progressbar( Element ):
	def __init__( self, percentage = 0.0, label = None, attributes = {} ):
		Element.__init__( self, attributes )
		self.percentage = str( percentage )
		self.label = label

class Text( Element ):
	def __init__( self, text = '', attributes = {} ):
		Element.__init__( self, attributes )
		self._text = text

	def __str__( self ):
		return self._text

	def set_text( self, text ):
		self._text = text

	def get_text( self ):
		return self._text

class Date( Text ):
	def __init__( self, date = '', attributes = {} ):
		Text.__init__( self, date, attributes )

class Number( Text ):
	def __init__( self, number = '', attributes = {} ):
		if not isinstance( number, basestring ):
			number = str( number )
		Text.__init__( self, number, attributes )

class HTML( Text ):
	def __init__( self, text = '', attributes = {} ):
		Text.__init__( self, text, attributes )

class Fill( Text ):
	def __init__( self, columns = 2, text = '', vertical = False ):
		if not vertical:
			Text.__init__( self, text, { 'colspan' : str( columns ) } )
		else:
			Text.__init__( self, text, { 'rowspan' : str( columns ) } )

class ModuleDescription( Text ):
	def __init__( self, title = '', text = '', attributes = {} ):
		Text.__init__( self, text, attributes )
		self.title = title

TextTypes = ( type( ModuleDescription() ), type( Progressbar() ), type( Text() ), type( Date() ), type( Number() ), type( HTML() ), type( Fill() ) )

def _verify_list_items( sequence ):
	# map strings to umcd.Text
	for i in range( 0, len( sequence ) ):
		if isinstance( sequence[ i ], basestring ):
			sequence[ i ] = Text( sequence[ i ] )
		if isinstance( sequence[ i ], ( int, float ) ):
			sequence[ i ] = Number( sequence[ i ] )
		elif isinstance( sequence[ i ], ( list, tuple ) ):
			sequence[ i ] = _verify_list_items( sequence[ i ] )
	return sequence

class Frame( Element, list ):
	def __init__( self, elements = [], title = '' ):
		Element.__init__( self )
		list.__init__( self, _verify_list_items( elements ) )
		if title:
			self.set_title( title )
		else:
			self.__title = None

	def __str__( self ):
		return "%s:\n  %s" % ( Element.__str__( self ), _str_list( self ) )

	def set_title( self, text ):
		if isinstance( text, basestring ):
			text = Text( text )
		self.__title = text

	def get_title( self ):
		return self.__title

class Cell( Element ):
	def __init__( self, item = '', attributes = {} ):
		Element.__init__( self, attributes )
		self.item = item

class Row( Element, list ):
	def __init__( self, sequence = [], attributes = {}, default_type = None ):
		Element.__init__( self, attributes )
		self.default_type = default_type
		list.__init__( self, _verify_list_items( sequence ) )

	def set_cell( self, no, content ):
		list.__setitem__( self, no, content )

	def get_cell( self, no ):
		return list.__getitem__( self, no )

class List( Element ):
	def __init__( self, header = None, content = None, sec_header = None, attributes = {}, default_type = None ):
		Element.__init__( self, attributes )
		self.default_type = default_type
		if not header:
			self.__header = []
		else:
			self.set_header( header )
		if not sec_header:
			self.__sec_header = []
		else:
			self.set_second_header( sec_header )

		self._content = []
		self.__content = self._content # for backward compatibility Bug #19554
		if content:
			for line in content:
				self.add_row( line )

	def __str__( self ):
		content = ''
		for line in self._content:
			content += _str_list( line ) + ', '
		return "%s:\n  header: %s\n  content: %s" % \
			( Element.__str__( self ), _str_list( self.__header ),
			  content[ : -2 ] )

	def set_header( self, header ):
		self.__header = Row( header )

	def get_header( self ):
		return self.__header

	def set_second_header( self, header ):
		self.__sec_header = Row( header )

	def get_second_header( self ):
		return self.__sec_header

	def add_row( self, row, attributes = {} ):
		self._content.append( Row( row, attributes, default_type = self.default_type ) )

	def insert_row( self, i, row, attributes = {} ):
		self._content.insert( i, Row( row, attributes, default_type = self.default_type ) )

	def remove_row( self, i ):
		try:
			self._content.pop( i )
		except:
			pass

	def get_row( self, i ):
		return self._content[ i ]

	def clear_content( self ):
		del self._content
		self._content = []
		self.__content = self._content # for backward compatibility Bug #19554

	def get_content( self ):
		return self._content

	def num_columns( self ):
		return len( self.__header )

def _str_list( lst ):
	text = '['
	for i in lst:
		text += '%s,' % unicode( i )
	return text[ : -1 ] + ' ]'

class SimpleTreeView( Element ):
	def __init__( self, tree_data = None, attributes = {}, collapsible = 0, name = 'treeview-table' ):
		self._tree_data = tree_data
		self.collapsible = collapsible
		self.name = name
		Element.__init__( self, attributes )

class SimpleTreeTable( List ):
	def __init__( self, tree_data = None, dialog = '', attributes = {}, collapsible = 0, name = 'treeview-table' ):
		attributes.update( { 'type' : 'umc_tree_view_table' } )
		List.__init__( self, attributes = attributes )

		self._separator_col = Cell( item = Text( '' ), attributes = { 'type' : 'umc_tree_table_separator' } )
		self.add_row( [ Cell( item = SimpleTreeView( tree_data, collapsible = collapsible, name = name ), attributes = { 'type' : 'umc_tree_table_treeview' } ), self._separator_col, '' ] )
		self.set_dialog( dialog )

	def set_dialog( self, dialog ):
		if isinstance( dialog, Element ):
			dialog[ 'type' ] = 'umc_tree_table_dialog'
		self._content[ 0 ].set_cell( 2, dialog )

	def set_tree_data( self, tree_data ):
		self._content[ 0 ].get_cell( 0 ).item._tree_data = tree_data

class Section( Element ):
	def __init__( self, title = '', body = '', hideable = False, hidden = False, name = 'section', attributes = {} ):
		Element.__init__( self, attributes )
		self.title = title
		self.body = body
		self.hideable = hideable
		self.hidden = hidden
		self.name = name

ListTypes = ( type( Section() ), type( Frame() ), type( List() ), type( Row() ), type( Cell() ), type( SimpleTreeTable() ), type( SimpleTreeView() ) )
