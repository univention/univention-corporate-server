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
import univention.management.console.dialog as umcd
import univention.management.console.protocol as umcp

import univention.debug as ud

_ = umc.Translation( 'univention.management.console.handlers.services' ).translate

def _utf8( text ):
	return unicode( text.encode( 'iso-8859-1' ), 'utf8' )

class Web( object ):
	def _web_service_list( self, object, res ):
		lst = umcd.List()
		servs = res.dialog
		boxes = []
		lst.set_header( [ _( 'Name' ), _( 'Status' ), _( 'Description' ) ] )
		for name, srv in servs.items():
			if srv.running:
				status = _( 'running' )
			else:
				status = _( 'stopped' )
				chk = umcd.Checkbox( static_options = { 'service' : name } )
				boxes.append( chk.id() )
			lst.add_row( [ name, status, _utf8( srv[ 'description' ] ), chk ] )
		req = umcp.Command( args = [], opts= { 'printers' : [] } )
		req_list = umcp.Command( args = [ 'cups/list' ],
								 opts = { 'filter' : filter, 'key' : key } )
		actions = ( umcd.Action( req, boxes, True ), umcd.Action( req_list ) )
		choices = [ ( 'service/start', _( 'Start Services' ) ),
					( 'service/stop', _( 'Stop Services' ) ) ]
		select = umcd.SelectionButton( _( 'Select the Operation' ), choices, actions )
		lst.add_row( [ umcd.Fill( 3 ), select ] )
		res.dialog = [ lst ]
		self.revamped( object.id(), res )
