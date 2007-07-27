#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  modutils module: revamp module command result for the specific user interface
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import univention.management.console as umc
import univention.management.console.dialog as umcd
import univention.management.console.protocol as umcp
import univention.management.console.tools as umct

import univention.debug as ud

import tools

_ = umc.Translation( 'univention.management.console.handlers.top' ).translate

class Web( object ):
	def _web_modutils_search( self, object, res ):
		main = []
		# add search form
		select = umcd.make( self[ 'modutils/search' ][ 'category' ],
							default = object.options.get( 'category', 'arch' ),
							attributes = { 'width' : '200' } )
		key = umcd.make( self[ 'modutils/search' ][ 'key' ],
						 default = object.options.get( 'key', 'name' ),
						 attributes = { 'width' : '200' } )
		text = umcd.make( self[ 'modutils/search' ][ 'pattern' ],
						  default = object.options.get( 'pattern', '*' ),
						  attributes = { 'width' : '250' } )

		form = umcd.SearchForm( 'modutils/search', [ [ ( select, 'arch' ), '' ],
													   [ ( key, 'name' ), ( text, '*' ) ] ] )
		main.append( [ form ] )

		# append result list
		if not object.incomplete:
			result = umcd.List()

			if res.dialog:
				result.set_header( [ _( 'Module' ), _( 'Loaded' ), _( 'Used By' ), '' ] )
				for mod in res.dialog:
					if mod.loaded:
						icon = umcd.Image( 'services/start', umct.SIZE_SMALL )
					else:
						icon = umcd.Image( 'services/stop', umct.SIZE_SMALL )
					ud.debug( ud.ADMIN, ud.INFO, 'modutils: name: %s' % mod.name )
					ud.debug( ud.ADMIN, ud.INFO, 'modutils: icon: %s' % icon )
					ud.debug( ud.ADMIN, ud.INFO, 'modutils: usedby: %s' % ', '.join( mod.usedby ) )
					result.add_row( [ mod.name, icon, ', '.join( mod.usedby ) ] )
			else:
				result.add_row( [ _( 'No kernel modules were found.' ) ] )

			main.append( umcd.Frame( [ result ], _( 'Search Result' ) ) )

		res.dialog = main

		self.revamped( object.id(), res )
