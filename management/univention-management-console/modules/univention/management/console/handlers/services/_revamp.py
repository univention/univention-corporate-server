# -*- coding: utf-8 -*-
#
# Univention Management Console
#  service module: revamps dialog result for the web interface
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

import string

import univention.management.console as umc
import univention.management.console.tools as umct
import univention.management.console.dialog as umcd
import univention.management.console.protocol as umcp

import univention.debug as ud

_ = umc.Translation( 'univention.management.console.handlers.services' ).translate

class Web( object ):
	def _web_service_list( self, object, res ):
		lst = umcd.List()
		servs = res.dialog
		boxes = []
		lst.set_header( [ umcd.Fill( 2, _( 'Name' ) ), _( 'Status' ), _( 'Start Type' ), _( 'Description' ) ] )
		for name, srv in servs.items():
			if srv.running:
				icon = umcd.Image( 'actions/yes', umct.SIZE_SMALL )
			else:
				icon = umcd.Image( 'actions/no', umct.SIZE_SMALL )
			chk = umcd.Checkbox( static_options = { 'service' : name } )
			boxes.append( chk.id() )
			image = umcd.Image( 'services/default', umct.SIZE_MEDIUM )
			type = _( 'manual' )
			if srv.autostart:
				type = _( 'automatically' )
			elif srv.autostart == None:
				type = _( 'unknown' )
			lst.add_row( [ image, name, icon, type, srv[ 'description' ], chk ] )
		req = umcp.Command( args = [], opts= { 'service' : [] } )
		req_list = umcp.Command( args = [ 'service/list' ],
								 opts = {} )
		actions = ( umcd.Action( req, boxes, True ), umcd.Action( req_list ) )
		choices = [ ( 'service/start', _( 'Start Services' ) ),
					( 'service/stop', _( 'Stop Services' ) ),
					( 'service/start_auto', _( 'Start Automatically' ) ),
					( 'service/start_manual', _( 'Start Manually' ) ), ]
		select = umcd.SelectionButton( _( 'Select the Operation' ), choices, actions )
		lst.add_row( [ umcd.Fill( 5 ), select ] )
		res.dialog = [ lst ]
		self.revamped( object.id(), res )
