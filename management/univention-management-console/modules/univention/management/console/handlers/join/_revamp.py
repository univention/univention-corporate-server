#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  join module: revamp module command result for the specific user interface
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

import os

import univention.management.console as umc
import univention.management.console.dialog as umcd
import univention.management.console.protocol as umcp
import univention.management.console.tools as umct

import univention.debug as ud

_ = umc.Translation( 'univention.management.console.handlers.join' ).translate

class Web( object ):

	def _web_join_status( self, object, res ):
		joined, scripts = res.dialog
		lst = umcd.List()

		if joined:
			lst.set_header( [ umcd.Text( _( 'Script' ), attributes = { 'colspan' : '2' } ),
							  _( 'Status' ), _( 'Current Version' ), _( 'Last Version' ) ] )
			for script in scripts:
				runnable = False
				if not script.current_version:
					cur = '-'
				else:
					cur = script.current_version
				if script.last_version == None:
					last = _( 'never started' )
				elif script.last_version == '':
					last = '-'
				else:
					last = script.last_version

				# check
				if script.last_version == None:
					runnable = True
				elif script.last_version == '' and script.current_version:
					runnable = True
				elif script.last_version and script.current_version and \
					 int( script.last_version ) < int( script.current_version ):
					runnable = True

				success = _( 'successful' )
				if script.success == False:
					success = _( 'failed' )
				elif script.success == None:
					success = '-'
				name = script.filename[ 2 : -5 ]

				if runnable:
					req = umcp.Command( args = [ 'join/script' ],
										opts = { 'script' : script.filename,
												 'name' : name }, incomplete = True )
					req.set_flag( 'web:startup', True )
					req.set_flag( 'web:startup_dialog', True )
					req.set_flag( 'web:startup_format',
								  _( "Join Script: %(name)s" ) % { 'name' : name } )
					btn = umcd.Button( name, 'join/script', umcd.Action( req ) )
					btn[ 'colspan' ] = '2'
					lst.add_row( [ btn, success, cur, last ] )
				else:
					btn = umcd.Image( 'join/script_inactive',
									  attributes = { 'type' : 'umc_list_element_part_left' } )
					txt = umcd.Text( name, attributes = { 'type' : 'umc_list_element_part_right' } )
					lst.add_row( [ btn, txt, success, cur, last ],
								 attributes = { 'type' : 'umc_list_inactive' } )
			if not umc.registry.get( 'server/role', None ) == 'domaincontroller_master':
				req = umcp.Command( args = [ 'join/rejoin' ], incomplete = True )
				req.set_flag( 'web:startup', True )
				req.set_flag( 'web:startup_dialog', True )
				req.set_flag( 'web:startup_format', _( 'Re-join' ) )
				lst.add_row( [ umcd.Button( _( 'Re-join the System' ), 'actions/ok',
											[ umcd.Action( req ) ] ) ] )
			res.dialog = [ umcd.Frame( [ lst ], _( 'Current Status' ) ) ]
		else:
			lst.add_row( [ umcd.InfoBox( _( 'The system has not been joined yet.' ) ) ] )
			req = umcp.Command( args = [ 'join/rejoin' ] )
			req.set_flag( 'web:startup', True )
			req.set_flag( 'web:startup_dialog', True )
			req.set_flag( 'web:startup_format', _( 'Join' ) )
			lst.add_row( [ umcd.Button( _( 'Join the System' ), 'actions/ok',
										[ umcd.Action( req ) ] ) ] )
			res.dialog = [ lst ]

		self.revamped( object.id(), res )

	def _web_join_rejoin( self, object, res ):
		lst = umcd.List()
		if object.incomplete:
			user = umcd.make( self[ 'join/rejoin' ][ 'account' ], default = self._username )
			pwd =  umcd.make( self[ 'join/rejoin' ][ 'password' ] )

			lst.add_row( [ user, pwd ] )
			req = umcp.Command( args = [ 'join/rejoin' ] )
			lst.add_row( [ umcd.Button( _( 'Join' ), 'actions/ok',
										umcd.Action( req, [ user.id(), pwd.id() ] ),
										close_dialog = False ),
						   umcd.CancelButton() ] )
			res.dialog = [ umcd.Frame( [ lst ], _( 'Credentials for Join' ) ) ]
		else:
			success, log = res.dialog
			if success:
				lst.add_row( [ umcd.InfoBox( _( 'The Join Process was successful!' ) ) ] )
			else:
				lst.add_row( [ umcd.InfoBox( _( 'The Join Process has failed!' ) ) ] )
			html = '<pre>' + '\n'.join( log ) + '</pre>'
			html = html.replace( '\x1b[60G', '\t\t\t' )
			lst.add_row( [ umcd.HTML( html ) ] )
			lst.add_row( [ umcd.CloseButton() ] )
			res.dialog = [ umcd.Frame( [ lst ], _( 'Log File' ) ) ]

		self.revamped( object.id(), res )

	def _web_join_script( self, object, res ):
		lst = umcd.List()
		if object.incomplete:#  or not object.options.get( 'account', None ) or not \
# 				object.options.get( 'password', None ):
			if not umc.registry.get( 'server/role', None ) in ( 'domaincontroller_master',
																'domaincontroller_backup' ):
				user = umcd.make( self[ 'join/script' ][ 'account' ],
								  default = object.options.get( 'account', self._username ) )
				pwd =  umcd.make( self[ 'join/script' ][ 'password' ] )

				lst.add_row( [ user, pwd ] )
				req = umcp.Command( args = [ 'join/script' ],
									opts = { 'script' : object.options[ 'script' ] } )
				lst.add_row( [ umcd.Button( _( 'Join' ), 'actions/ok',
											umcd.Action( req, [ user.id(), pwd.id() ] ),
											close_dialog = False ),
							   umcd.CancelButton() ] )
				res.dialog = [ umcd.Frame( [ lst ], _( 'Credentials for Join' ) ) ]
			else:
				lst.add_row( [ umcd.InfoBox( _( 'No Credentials are required.' ) ) ] )
				req = umcp.Command( args = [ 'join/script' ],
									opts = { 'script' : object.options[ 'script' ] } )
				lst.add_row( [ umcd.Button( _( 'Run Script' ), 'actions/ok',
											umcd.Action( req ), close_dialog = False ),
							   umcd.CancelButton() ] )
				res.dialog = [ umcd.Frame( [ lst ], _( 'Credentials for Join' ) ) ]

		else:
			success, log = res.dialog
			if success:
				lst.add_row( [ umcd.InfoBox( _( 'The Join Script was successful!' ) ) ] )
			else:
				lst.add_row( [ umcd.InfoBox( _( 'The Join Script has failed!' ) ) ] )
			html = '<pre>' + '\n'.join( log ) + '</pre>'
			lst.add_row( [ umcd.HTML( html ) ] )
			lst.add_row( [ umcd.CloseButton() ] )
			res.dialog = [ umcd.Frame( [ lst ], _( 'Log File' ) ) ]

		self.revamped( object.id(), res )
