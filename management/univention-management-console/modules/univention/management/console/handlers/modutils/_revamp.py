#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  modutils module: revamp module command result for the specific user interface
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

import univention.management.console as umc
import univention.management.console.dialog as umcd
import univention.management.console.protocol as umcp
import univention.management.console.tools as umct

import univention.debug as ud

import tools

_ = umc.Translation( 'univention.management.console.handlers.modutils' ).translate

class Web( object ):
	def _web_modutils_search( self, object, res ):
		main = []
		# add search form
		select = umcd.make( self[ 'modutils/search' ][ 'category' ],
							default = object.options.get( 'category', 'all' ),
							attributes = { 'width' : '250' } )
		key = umcd.make( self[ 'modutils/search' ][ 'key' ],
						 default = object.options.get( 'key', 'name' ),
						 attributes = { 'width' : '250' } )
		text = umcd.make( self[ 'modutils/search' ][ 'pattern' ],
						  default = object.options.get( 'pattern', '*' ),
						  attributes = { 'width' : '250' } )
		loaded = umcd.make( self[ 'modutils/search' ][ 'loaded' ],
						  default = object.options.get( 'loaded', True ), attributes = {'valign': 'bottom'} )

		form = umcd.SearchForm( 'modutils/search', [ [ ( select, 'all' ), ( loaded, 'loaded' ) ],
													   [ ( key, 'name' ), ( text, '*' ) ] ] )
		main.append( [ form ] )

		# append result list
		if not object.incomplete:
			result = umcd.List()

			if res.dialog:
				result.set_header( [ _( 'Module' ), _( 'Loaded' ), _( 'Used by' ), '' ] )
				for mod in res.dialog:
					if mod.loaded:
						icon = umcd.Image( 'actions/yes', umct.SIZE_SMALL )
						req = umcp.Command( args = [ 'modutils/show' ],
											opts = { 'module' : mod.name, 'load' : False,
													 'category' : object.options.get( 'category', 'all' ),
													 'pattern' : object.options.get( 'pattern', '*' ),
													 'loaded' : object.options.get( 'loaded', True ),
													 'key' : object.options.get( 'key', 'name' ),
													 } )
						req.set_flag( 'web:startup', True )
						req.set_flag( 'web:startup_cache', False )
						req.set_flag( 'web:startup_dialog', True )
						req.set_flag( 'web:startup_referrer', False )
						req.set_flag( 'web:startup_format', _( 'Unload module: %(module)s' ) )
						btn = umcd.Button( mod.name, 'modutils/kmodule', umcd.Action( req ) )
					else:
						icon = umcd.Image( 'actions/no', umct.SIZE_SMALL )
						req = umcp.Command( args = [ 'modutils/show' ],
											opts = { 'module' : mod.name, 'load' : True,
													 'category' : object.options.get( 'category', 'all' ),
													 'pattern' : object.options.get( 'pattern', '*' ),
													 'loaded' : object.options.get( 'loaded', True ),
													 'key' : object.options.get( 'key', 'name' ),
													 } )
						req.set_flag( 'web:startup', True )
						req.set_flag( 'web:startup_cache', False )
						req.set_flag( 'web:startup_dialog', True )
						req.set_flag( 'web:startup_referrer', False )
						req.set_flag( 'web:startup_format', _( 'Load module: %(module)s' ) )
						btn = umcd.Button( mod.name, 'modutils/kmodule', umcd.Action( req ) )

					result.add_row( [ btn, icon, ', '.join( mod.usedby ) ] )
			else:
				result.add_row( [ _( 'No kernel modules were found.' ) ] )

			main.append( umcd.Frame( [ result ], _( 'Search results' ) ) )

		res.dialog = main

		self.revamped( object.id(), res )

	def _web_modutils_show( self, object, res ):
		result = umcd.List()
		mod = res.dialog
		if object.options[ 'load' ]:
			result.add_row( [ umcd.make_readonly( self[ 'modutils/load' ][ 'module' ],
												  default = object.options[ 'module' ] ) ] )
			args = umcd.make( self[ 'modutils/load' ][ 'arguments' ] )
			result.add_row( [ args ] )
			req = umcp.Command( args = [ 'modutils/load' ], opts = { 'module' : mod.name } )
			req_list = umcp.Command( args = [ 'modutils/search' ],
									 opts = { 'category' : object.options[ 'category' ],
									 		  'pattern' : object.options[ 'pattern' ],
									 		  'loaded' : object.options[ 'loaded' ],
											  'key' : object.options[ 'key' ] } )
			result.add_row( [	umcd.CancelButton(attributes = {'class': 'cancel'}),
								umcd.Button( label = _( 'Load' ), attributes = {'class': 'submit'}, actions = [ umcd.Action( req, [ args.id() ] ), umcd.Action( req_list ) ] )
							 ] )
		else:
			req = umcp.Command( args = [ 'modutils/unload' ], opts = { 'module' : mod.name } )
			req_list = umcp.Command( args = [ 'modutils/search' ],
									 opts = { 'category' : object.options[ 'category' ],
									 		  'pattern' : object.options[ 'pattern' ],
									 		  'loaded' : object.options[ 'loaded' ],
											  'key' : object.options[ 'key' ] } )
			result.add_row( [ umcd.Question( _( "Unloading a kernel module may result in an unstable system. Are you sure that the module '%s' should be unloaded?" ) % mod.name,
										actions = [ umcd.Action( req ), umcd.Action( req_list ) ] , okay = _( 'Unload' ) ) ] )

		res.dialog = [ result ]
		self.revamped( object.id(), res )
