#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  vnc module: revamp module command result for the specific user interface
#
# Copyright (C) 2007-2009 Univention GmbH
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
			btn = umcd.Button( _( 'Start' ), 'actions/ok',
							   actions = [ umcd.Action( req ), umcd.Action( req_config ) ] )
			lst.add_row( [ btn ] )
			res.dialog = [ umcd.Frame( [ lst ], _( 'Start VNC server' ) ) ]
		else:
			lst.add_row( [ umcd.InfoBox( _( 'Password is set and the VNC server is running.' ) ) ] )
			lst.add_row( [ umcd.HTML( self._create_vnc_url() ) ] )
			req = umcp.Command( args = [ 'vnc/stop' ] )
			req_config = umcp.Command( args = [ 'vnc/config' ] )
			btn = umcd.Button( _( 'Stop VNC server' ), 'actions/ok',
							   actions = [ umcd.Action( req ), umcd.Action( req_config ) ] )
			lst.add_row( [ btn ] )
			res.dialog = [ umcd.Frame( [ lst ], _( 'Connect to VNC session' ) ) ]
		self.revamped( object.id(), res )
