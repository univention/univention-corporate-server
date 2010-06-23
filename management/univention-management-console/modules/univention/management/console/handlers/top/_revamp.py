#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  top module: revamp module command result for the specific user interface
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

_ = umc.Translation( 'univention.management.console.handlers.top' ).translate

class Web( object ):
	def _web_top_view( self, object, res ):
		lst = umcd.List()
		opts = umcd.List()

		sort = umcd.make( self[ 'top/view' ][ 'sort' ], attributes = { 'width' : '165' },
						  default = object.options.get( 'sort', 'cpu' ) )
		count = umcd.make( self[ 'top/view' ][ 'count' ], attributes = { 'width' : '165' },
						   default = object.options.get( 'count', '50' ) )

		req = umcp.Command( args = [ 'top/view' ] )
		btn = umcd.Button( _( 'Reload' ), attributes = {'class': 'submit'}, 
						   actions = [ umcd.Action( req, [ sort.id(), count.id() ] ) ] )
		opts.add_row( [ sort, count ] )
		opts.add_row( [ umcd.HTML(' '), btn ] )

		lst.set_header( [ _( 'User' ), _( 'PID' ), _( 'CPU' ), _( 'Virtual size' ), _( 'Resident set size' ),
						  _( 'Memory in %' ), _( 'Program' ), _('Select') ] )
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
		choices = [ ( 'top/kill', _( 'Kill processes' ) ), ]
		select = umcd.SelectionButton( _( 'Select the operation' ), choices, actions, attributes = {'colspan': '2', 'width': '245'} ) #FIXME
		lst.add_row( [ umcd.Fill( 6 ), select ] )

		res.dialog = [ opts, lst ]
		self.revamped( object.id(), res )
