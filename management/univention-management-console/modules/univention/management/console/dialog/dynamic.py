#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  dynamic dialog elements that may change
#
# Copyright 2007-2010 Univention GmbH
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

import copy

import base
import input

import univention.debug as ud

class DynamicList( base.List, input.Input ):
	"""Represent a list, that may change its appearance by appending or
	removing table rows"""
	def __init__( self, option = ( None, None ), header = [], row = [], default = None,
				  modifier = None, modified = {} ):
		base.List.__init__( self, header )
		input.Input.__init__( self, option )
		self.modifier = modifier
		self.modified = modified
		self.set_row( row )
		self.__items = []
		if row and default:
			for value in default:
				self.append_row( value )
		else:
			self.append_row()

	def set_row( self, row ):
		if self.modifier and self.modified:
			new_modifier = copy.deepcopy( self.modifier )
			new_modified = copy.deepcopy( self.modified[ new_modifier.default ] )
			row.insert( 0, new_modifier )
			row.append( new_modified )
		for item in row:
			if isinstance( item, input.Input ):
				item.set_text( '' )
		self.__row = row
		self.clear_content()
		if row:
			self.__row = base._verify_list_items( self.__row )

	# value == default values
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
		# if modifier and modified is set then change modified object corresponding
		# to modifier object and set correct default value
		if self.modifier and self.modified:
			if len(new_row) > 1:
				if value.has_key( new_row[0].option ):
					defaultval = value[ new_row[-1].option ]
					self.modify_row( len(self.__items)-1, value[ new_row[0].option ], defaultval )

	def remove_row( self, i ):
		base.List.remove_row( self, i )
		self.__items.pop( i )

	def modify_row( self, i, key, default = None ):
		if not self.modifier or not self.modified:
			return
		# get row number i
		row = self.get_row( i )
		# remove last element (modified obj)
		row.pop()
		# create new object depending on value of modifier object (key)
		modified_item = copy.deepcopy( self.modified[ key ] )
		modified_item.recreate_id()
		row.append( modified_item )
		if default != None:
			modified_item.default = default
		# update id list
		self.__items[i].pop()
		self.__items[i].append( modified_item.id() )

	def get_items( self ):
		return self.__items

class MultiValue( input.Input ):
	def __init__( self, option = ( None, None ), fields = [], default = None,
				  static_options = {}, attributes = {}, separator = ' ', label = None ):
		input.Input.__init__( self, option, default, static_options,
							  attributes )
		self.fields = fields
		self.separator = separator
		self.field_ids = []
		self.label = label
		for field in self.fields:
			self.field_ids.append( field.id() )

class ObjectSelect( input.Input ):
	'''
	  |------------------------------------------|
	  | Search for object properties             |
	  |------------------------------------------|
	  |             |          |                 |
	  |             |----------|                 |
	  |    list1    |    >     |      list2      |
	  |             |----------|                 |
  	  |             |    <     |                 |
	  |------------------------------------------|

	  modulename = name of module (e.g. computers/computer)
	  default = list of object dn to be displayed in list2
	  attr_display = name of attribute to be shown for each object
	  filter = ldap filter
	  basedn = ldap base dn
	  scope = ldap scope
	  search_disabled = enable/disable object property search (if disabled, display all matching objects)
	  search_properties = list of property keys that are available during search (if list is empty, all properties are enabled)
	'''
	def __init__( self, option = ( None, None ),
				  modulename = None, filter = None, attr_display = [ 'dn' ],
				  default = [], search_properties = [], search_disabled = False, basedn = None, scope = 'sub' ):
		input.Input.__init__( self, option )
		self.modulename = modulename
		self.filter = filter
		self.attr_display = attr_display
		self.search_properties = search_properties
		self.search_disabled = search_disabled
		self.default = default
		self.basedn = basedn
		self.scope = scope
		self.save = {}


class FileUpload( input.Input ):
	'''
		 |-------------------------------------|
		 | File 1    (X) Remove                |
		 | File 2    (X) Remove                |
		 | File ...  (X) Remove                |
		 | File n    (X) Remove                |
		 |-------------------------------------|
		 | <uploadfield with searchbutton>     |
		 |-------------------------------------|
		 | <upload-button>                     |
		 |-------------------------------------|

		 maxfiles = maximum number of files that can be uploaded (0 = unlimited)
	'''
	def __init__( self, option = ( None, None ), default = None, maxfiles = 0 ):
		input.Input.__init__( self, option )	
		self.maxfiles = maxfiles
		self.save = {}
		if default:
			self.save['uploadFilelist'] = default

DynamicTypes = ( type( DynamicList() ), type( MultiValue() ), type( ObjectSelect() ), type( FileUpload() ) )
