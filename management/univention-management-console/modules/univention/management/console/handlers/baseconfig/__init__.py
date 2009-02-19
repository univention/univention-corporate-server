#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: manages Univention Config Registry variables
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

from fnmatch import *

import univention.management.console as umc
import univention.management.console.handlers as umch
import univention.management.console.dialog as umcd
import univention.management.console.protocol as umcp
import univention.management.console.tools as umct

import univention.debug as ud

import univention.config_registry
from univention.config_registry_info import ConfigRegistryInfo, Variable

import notifier.popen

import _revamp
import _types

_ = umc.Translation( \
	'univention.management.console.handlers.baseconfig' ).translate

icon = 'baseconfig/module'
short_description = _( 'Univention Configuration Registry' )
long_description = _( 'Add, modify and search Univention Configuration Registry variables' )
categories = [ 'all' ]

command_description = {
	'baseconfig/set': umch.command(
		short_description = _( 'Add' ),
		long_description = _( 'Add a new configuration registry variable' ),
		method = 'baseconfig_set',
		values = { 'key' : _types.key,
				   'value' : _types.value,
				   'type' : _types.bctype,
				   'categories' : _types.categories,
				   'descriptions' : _types.descr },
		startup = True,
		priority = 80
	),
	'baseconfig/show': umch.command(
		short_description = _( 'Show' ),
		long_description = _( 'Display information about a configuration registry variable' ),
		method = 'baseconfig_show',
		values = { 'key': _types.key },
	),
	'baseconfig/unset': umch.command(
		short_description = _( 'Remove' ),
		long_description = _( 'Unset a configuration registry value' ),
		method = 'baseconfig_unset',
		values = { 'key': _types.key },
	),
	'baseconfig/search': umch.command(
		short_description = _( 'Search' ),
		long_description = _( 'Search for a configuration registry value' ),
		method = 'baseconfig_search',
		values = { 'key' : _types.searchkey,
				   'filter': _types.filter,
				   'category' : _types.categorysearch },
		startup = True,
		caching = True,
		priority = 100
	),
}

class handler( umch.simpleHandler, _revamp.Web ):

	def __init__( self ):
		global command_description
		umch.simpleHandler.__init__( self, command_description )

	def __create_variable_info( self, options ):
		all_info = ConfigRegistryInfo( registered_only = False )
		info = ConfigRegistryInfo( install_mode = True )
		info.read_customized()
		var = Variable()

		# description
		for line in options[ 'descriptions' ]:
			text = line[ 'text' ]
			if not text: continue
			if line.has_key( 'lang' ):
				var[ 'description[%s]' % line[ 'lang' ] ] = text
			else:
				var[ 'description' ] = text
		# categories
		if options[ 'categories' ]:
			var[ 'categories' ] = ','.join( options[ 'categories' ] )

		# type
		var[ 'type' ] = options[ 'type' ]

		# are there any modifications?
		old_value = all_info.get_variable( options[ 'key' ] )
		if old_value != var:
			# save
			info.add_variable( options[ 'key' ], var )
			info.write_customized()

	def baseconfig_set( self, object ):
		success = True

		ud.debug( ud.ADMIN, ud.INFO, 'Baseconfig.set: options: %s' % str( object.options ) )
		if object.incomplete:
			object.status( 200 )
		elif object.options.has_key( 'key' ) and \
			   object.options.has_key( 'value' ):
			value = object.options[ 'value' ]
			if value == None:
				value = ''
			arg = [ '%s=%s' % ( object.options[ 'key' ].encode(), value.encode() ) ]
			univention.config_registry.handler_set( arg )
			if object.options.get( 'descriptions', '' ) or object.options.get( 'type', '' ) or \
				   object.options.get( 'categories', '' ):
				self.__create_variable_info( object.options )
			object.status( 200 )
		else:
			success = False
			object.status( 403 )

		self.finished( object.id(), None, success = success )

	def baseconfig_unset( self, object ):
		if object.options.has_key( 'key' ):
			univention.config_registry.handler_unset( object.options[ 'key' ] )

		self.finished( object.id(), {} )


	def baseconfig_show( self, object ):
		"""this method returns a dictionary of configuration registry variables
		found by searching for the (wildcard) expression defined by the UMCP
		request. Additionally a list of configuration registry categories can be defined"""
		if not object.incomplete:
			baseInfo = ConfigRegistryInfo( registered_only = False )
			vars = baseInfo.get_variables()
			if vars.has_key( object.options[ 'key' ] ):
				self.finished( object.id(), vars[ object.options[ 'key' ] ] )
			else:
				self.finished( object.id(), None, success = False )
		else:
			self.finished( object.id(), None, success = False )

	def baseconfig_search( self, object ):
		"""this method returns a dictionary of configuration registry variables
		found by searching for the (wildcard) expression defined by the UMCP
		request. Additionally a list of configuration registry categories can be defined"""
		variables = {}
		ud.debug( ud.ADMIN, ud.INFO, 'Baseconfig.search: options: %s' % str( object.options ) )
		if not object.incomplete:
			category = object.options.get( 'category', None )
			if category == 'all':
				# load _all_ config registry variables
				baseInfo = ConfigRegistryInfo( registered_only = False )
			else:
				# load _all registered_ config registry variables
				baseInfo = ConfigRegistryInfo()

			filter = object.options.get( 'filter', '*' )
			if filter == None:
				filter = ''
			key = object.options.get( 'key', 'variable' )
			if category in ( 'all', 'all-registered' ):
				cat = None
			else:
				cat = category

			for name, var in baseInfo.get_variables( cat ).items():
				if key == 'value':
					if var.value and fnmatch( var.value, filter ):
						variables[ name ] = var
				elif key == 'description':
					if var[ 'description' ] and fnmatch( var[ 'description' ], filter ):
						variables[ name ] = var
				else:
					if fnmatch( name, filter ):
						variables[ name ] = var
		else:
			key = 'variable'
			filter = '*'
			category = 'all'

		if not object.status():
			object.status( 200 )

		self.finished( object.id(), ( ( key, filter, category ), variables ) )
