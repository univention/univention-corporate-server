#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  vnc module: revamp module command result for the specific user interface
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

import os

import univention.management.console as umc
import univention.management.console.dialog as umcd
import univention.management.console.protocol as umcp
import univention.management.console.tools as umct

import univention.debug as ud

_ = umc.Translation( 'univention.management.console.handlers.vnc' ).translate

class Web( object ):

	def _create_vnc_url( self ):
		args = self._vnc_cmdline()
		if '-rfbport' in args:
			port = args[ args.index( '-rfbport' ) + 1 ]

		url = '/univention-management-console/vnc/connect.php?port=%s&username=%s' % \
			  ( port, self._username )
		return '<a href="%s" target="_blank">%s</a>' % ( url, _( 'Connect to the VNC server' ) )

	def _web_vnc_config( self, object, res ):
		pwdexists, running = res.dialog
		lst = umcd.List()

		if not pwdexists:
			msg = _( 'To setup a VNC session a password is required and a running VNC server.' )
			lst.add_row( [ umcd.InfoBox( msg ) ] )

			pwd = umcd.make( self[ 'vnc/password' ][ 'password' ] )
			req = umcp.Command( args = [ 'vnc/password' ] )
			req_config = umcp.Command( args = [ 'vnc/config' ] )
			btn = umcd.SetButton( actions = [ umcd.Action( req, [ pwd.id() ] ),
											  umcd.Action( req_config ) ] )
			lst.add_row( [ pwd, btn ] )
			res.dialog = [ umcd.Frame( [ lst ], _( 'Set VNC password' ) ) ]
		elif not running:
			lst.add_row( [ umcd.InfoBox( _( 'Currently there is no VNC server running.' ) ) ] )
			req = umcp.Command( args = [ 'vnc/start' ] )
			req_config = umcp.Command( args = [ 'vnc/config' ] )
			btn = umcd.Button( _( 'Start' ), 'actions/ok',  attributes = {'class': 'submit'},
							   actions = [ umcd.Action( req ), umcd.Action( req_config ) ] )
			lst.add_row( [ btn ] )
			res.dialog = [ umcd.Frame( [ lst ], _( 'Start VNC server' ) ) ]
		else:
			lst.add_row( [ umcd.InfoBox( _( 'Password is set and the VNC server is running.' ) ) ] )
			lst.add_row( [ umcd.HTML( self._create_vnc_url() ) ] )
			req = umcp.Command( args = [ 'vnc/stop' ] )
			req_config = umcp.Command( args = [ 'vnc/config' ] )
			btn = umcd.Button( _( 'Stop VNC server' ),
							   actions = [ umcd.Action( req ), umcd.Action( req_config ) ] )
			lst.add_row( [ btn ] )
			res.dialog = [ umcd.Frame( [ lst ], _( 'Connect to VNC session' ) ) ]
		self.revamped( object.id(), res )
