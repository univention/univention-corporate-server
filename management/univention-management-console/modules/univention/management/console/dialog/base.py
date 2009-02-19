#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  base classes for UMCP dialogs
#
# Copyright (C) 2006-2009 Univention GmbH
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

import copy

import base

class Element( object ):
	__counter = 0
	def __init__( self, attributes = {} ):
		self.__id = None
		self.__attributes = copy.deepcopy( attributes )
		self.__create_id()

	def __str__( self ):
		return self.__id

	def __setitem__( self, key, value ):
		self.__attributes[ key ] = value

	def __delitem__( self, key ):
		if self.__attributes.has_key( key ):
			del self.__attributes[ key ]

	def __getitem__( self, key ):
		if self.__attributes.has_key( key ):
			return self.__attributes[ key ]
		return None

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

TextTypes = ( type( Text() ), type( Date() ), type( Number() ), type( HTML() ),
			  type( Fill() ) )

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
		self.set_title( title )

	def __str__( self ):
		return "%s:\n  %s" % ( Element.__str__( self ), _str_list( self ) )

	def set_title( self, text ):
		if isinstance( text, basestring ):
			text = Text( text )
		self.__title = text

	def get_title( self ):
		return self.__title

class Row( Element, list ):
	def __init__( self, sequence = [], attributes = {} ):
		Element.__init__( self, attributes )
		list.__init__( self, _verify_list_items( sequence ) )

class List( Element ):
	def __init__( self, header = None, content = None, sec_header = None, attributes = {} ):
		Element.__init__( self, attributes )
		if not header:
			self.__header = []
		else:
			self.set_header( header )
		if not sec_header:
			self.__sec_header = []
		else:
			self.set_second_header( sec_header )

		self.__content = []
		if content:
			for line in content:
				self.add_row( line )

	def __str__( self ):
		content = ''
		for line in self.__content:
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
		self.__content.append( Row( row, attributes ) )

	def remove_row( self, i ):
		try:
			self.__content.pop( i )
		except:
			pass

	def get_row( self, i ):
		return self.__content[ i ]

	def clear_content( self ):
		del self.__content
		self.__content = []

	def get_content( self ):
		return self.__content

	def num_columns( self ):
		return len( self.__header )

def _str_list( lst ):
	text = '['
	for i in lst:
		text += '%s,' % unicode( i )
	return text[ : -1 ] + ' ]'

ListTypes = ( type( Frame() ), type( List() ), type( Row() ) )
