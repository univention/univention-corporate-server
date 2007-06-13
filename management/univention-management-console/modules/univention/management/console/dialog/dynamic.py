#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  dynamic dialog elements that may change
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301 USA

import copy

import base
import input

class DynamicList( base.List, input.Input ):
	"""Represent a list, that may change its appearance by appending or
	removing table rows"""
	def __init__( self, option = ( None, None ), header = [], row = [], default = None ):
		base.List.__init__( self, header )
		input.Input.__init__( self, option )
		self.set_row( row )
		self.__items = []
		if row and default:
			for value in default:
				self.append_row( value )
		else:
			self.append_row()

	def set_row( self, row ):
		for item in row:
			if isinstance( item, input.Input ):
				item.set_text( '' )
		self.__row = row
		self.clear_content()
		if row:
			self.__row = base._verify_list_items( self.__row )

	def append_row( self, value = {} ):
		new_row = copy.deepcopy( self.__row )
		ids = []
		for item in new_row:
			item.recreate_id()
			if type( item ) in input.InputTypes:
				if value.has_key( item.option ):
					item.default = value[ item.option ]
				ids.append( item.id() )
		self.__items.append( ids )
		self.add_row( new_row )

	def remove_row( self, i ):
		base.List.remove_row( self, i )
		self.__items.pop( i )

	def get_items( self ):
		return self.__items

class MultiValue( input.Input ):
	def __init__( self, option = ( None, None ), fields = [], default = None,
				  static_options = {}, attributes = {}, separator = ' ' ):
		input.Input.__init__( self, option, default, static_options,
							  attributes )
		self.fields = fields
		self.separator = separator
		self.field_ids = []
		for field in self.fields:
			self.field_ids.append( field.id() )

class ObjectSelect( input.Input ):
	def __init__( self, option = ( None, None ),
				  modulename = None, filter = None, attr_display = [ 'dn' ],
				  default = [], search_disabled = False, basedn = None, scope = 'sub' ):
		input.Input.__init__( self, option )
		self.modulename = modulename
		self.filter = filter
		self.attr_display = attr_display
		self.search_disabled = search_disabled
		self.default = default
		self.basedn = basedn
		self.scope = scope
		self.save = {}

DynamicTypes = ( type( DynamicList() ), type( MultiValue() ), type( ObjectSelect() ) )
