#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: manages Univention Config Registry variables
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

from fnmatch import fnmatch

import univention.management.console as umc
import univention.management.console.modules as umcm
import univention.debug as ud

import univention.config_registry as ucr
from univention.config_registry_info import ConfigRegistryInfo, Variable

_ = umc.Translation( 'univention-management-console-modules-ucr' ).translate

class Instance( umcm.Base ):
	def __create_variable_info( self, options ):
		all_info = ConfigRegistryInfo( registered_only = False )
		info = ConfigRegistryInfo( install_mode = True )
		info.read_customized()
		var = Variable()

		# description
		for line in options[ 'descriptions' ]:
			text = line[ 'text' ]
			if not text: continue
			if 'lang' in line:
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

	def set( self, request ):
		if isinstance( request.options, ( list, tuple ) ):
			for var in request.options:
				if 'value' in var:
					value = var[ 'value' ]
					if  value is None:
						value = ''
						arg = [ '%s=%s' % ( key.encode(), value.encode() ) ]
						ucr.handler_set( arg )
				if 'descriptions' in var or 'type' in var or 'categories' in var:
					self.__create_variable_info( var )
			request.status = 200
			success = True
		else:
			success = False
			request.status = 403

		self.finished( request.id(), success )

	def unset( self, request ):
		response = False
		if 'key' in request.options:
			ucr.handler_unset( request.options[ 'key' ] )
			response = True

		self.finished( request.id(), response )

	def get( self, request ):
		ucrReg = ucr.ConfigRegistry()
		ucrReg.load()
		ucrInfo = ConfigRegistryInfo( registered_only = False )
		var = ucrInfo.get_variable( str( request.options[ 'variable' ] ) )
		value = ucrReg.get( str( request.options[ 'variable' ] ) )
		if not var and value:
			self.finished( request.id(),  { 'variable' : request.options[ 'variable' ], 'value' : value } )
		elif var:
			var[ 'value' ] = value
			self.finished( request.id(), var.normalize() )
		else:
			self.finished( request.id(), False, message = _( 'The UCR variable %(variable)s could not be found' ) % { 'variable' : request.options[ 'variable' ] } )

	def categories( self, request ):
		ucrInfo = ConfigRegistryInfo( registered_only = False )
		self.finished( request.id(), dict( ucrInfo.categories ) )

	def search( self, request ):
		'''Returns a dictionary of configuration registry variables
		found by searching for the (wildcard) expression defined by the
		UMCP request. Additionally a list of configuration registry
		categories can be defined.

		The dictionary returned is compatible with the Dojo data store
		format.'''
		variables = []
		ud.debug( ud.ADMIN, ud.INFO, 'UCR.search: options: %s' % str( request.options ) )
		category = request.options.get( 'category', None )
		if category == 'all':
			# load _all_ config registry variables
			baseInfo = ConfigRegistryInfo( registered_only = False )
		else:
			# load _all registered_ config registry variables
			baseInfo = ConfigRegistryInfo()

		filter = request.options.get( 'filter', '*' )
		if filter == None:
			filter = ''
		key = request.options.get( 'key', 'variable' )
		if category in ( 'all', 'all-registered' ):
			cat = None
		else:
			cat = category

		for name, var in baseInfo.get_variables( cat ).items():
			if key == 'value':
				if var.value and fnmatch( var.value, filter ):
					variables.append( { 'key' : name, 'value' : var.value } )
			elif key == 'description':
				descr = var.get( 'description', '' )
				if descr and fnmatch( descr, filter ):
					variables.append( { 'key' : name, 'value' : var.value } )
			else:
				if fnmatch( name, filter ):
					variables.append( { 'key' : name, 'value' : var.value } )

		if not request.status:
			request.status = 200

		self.finished( request.id(), { 'identifier' : 'key', 'label' : 'key', 'items' : variables } )
