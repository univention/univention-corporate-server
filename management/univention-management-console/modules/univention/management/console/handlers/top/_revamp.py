#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  top module: revamp module command result for the specific user interface
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
	def _web_top_view( self, object, res ):
		lst = umcd.List()
		opts = umcd.List()

		sort = umcd.make( self[ 'top/view' ][ 'sort' ], attributes = { 'width' : '150' },
						  default = object.options.get( 'sort', 'cpu' ) )
		count = umcd.make( self[ 'top/view' ][ 'count' ], attributes = { 'width' : '50' },
						   default = object.options.get( 'count', '50' ) )

		req = umcp.Command( args = [ 'top/view' ] )
		btn = umcd.Button( _( 'Reload' ), 'actions/ok',
						   actions = [ umcd.Action( req, [ sort.id(), count.id() ] ) ] )
		opts.add_row( [ sort, count, btn ] )

		lst.set_header( [ _( 'User' ), _( 'PID' ), _( 'CPU' ), _( 'Virtual Size' ), _( 'Resident Set Size' ),
						  _( 'Memory in %' ), _( 'Program' ), '' ] )
		boxes = []

		for proc in res.dialog:
			chk = umcd.Checkbox( static_options = { 'pid' : proc.pid } )
			boxes.append( chk.id() )
			lst.add_row( [ proc.uid, proc.pid, proc.cpu, proc.vsize, proc.rssize, proc.mem, proc.prog, chk ] )

		req = umcp.Command( args = [], opts= { 'signal' : 'kill', 'pid' : [] } )
		req_list = umcp.Command( args = [ 'top/view' ],
								 opts = { 'sort' : object.options.get( 'sort', 'cpu' ),
										  'count' : object.options.get( 'count', '50' ) } )
		actions = ( umcd.Action( req, boxes, True ), umcd.Action( req_list ) )
		choices = [ ( 'top/kill', _( 'Kill Processes' ) ), ]
		select = umcd.SelectionButton( _( 'Select the Operation' ), choices, actions )
		lst.add_row( [ umcd.Fill( 7 ), select ] )

		res.dialog = [ opts, lst ]
		self.revamped( object.id(), res )
