#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: VNC client
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

import univention.management.console as umc
import univention.management.console.handlers as umch
import univention.management.console.dialog as umcd
import univention.management.console.tools as umct
import univention.debug as ud

import univention.service_info as usi

import os

import notifier.popen

import _revamp

_ = umc.Translation( 'univention.management.console.handlers.vnc' ).translate

name = 'vnc'
icon = 'vnc/module'
short_description = _( 'VNC' )
long_description = _( 'Access to a System via VNC Session' )
categories = [ 'all', 'system' ]

command_description = {
	'vnc/config' : umch.command(
		short_description = _( 'VNC configuration' ),
		method = 'vnc_config',
		values = {},
		startup = True,
	),
	'vnc/start' : umch.command(
		short_description = _( 'VNC connection' ),
		method = 'vnc_start',
		values = {},
	),
	'vnc/stop' : umch.command(
		short_description = _( 'VNC connection' ),
		method = 'vnc_stop',
		values = {},
	),
	'vnc/password' : umch.command(
		short_description = _( 'VNC password' ),
		method = 'vnc_password',
		values = { 'password': umc.Password( _( 'Password' ) ) },
	),
}

class handler( umch.simpleHandler, _revamp.Web ):
	def __init__( self ):
		global command_description
		umch.simpleHandler.__init__( self, command_description )

	def _vnc_cmdline( self ):
		vncdir = os.path.join( '/home', self._username, '.vnc' )
		pidfile = None
		if os.path.isdir( vncdir ):
			for item in os.listdir( vncdir ):
				if os.path.isfile( os.path.join( vncdir, item ) ) and item.endswith( '.pid' ):
					pidfile = os.path.join( vncdir, item )
					break

		if not pidfile:
			return ()

		fd = open( pidfile, 'r' )
		pid = fd.readline()[ : -1 ]
		fd.close()
		try:
			fd = open( os.path.join( '/proc', pid, 'cmdline' ), 'r' )
			cmdline = fd.readline()[ : -1 ]
			fd.close()
			return cmdline.split( '\x00' )
		except:
			os.unlink( pidfile )
			pass
		return ()

	def _vnc_status( self ):
		vncdir = os.path.join( '/home', self._username, '.vnc' )
		if os.path.isfile( os.path.join( vncdir, 'passwd' ) ):
			pwdexists = True
		else:
			pwdexists = False
		running = False
		if os.path.isdir( vncdir ):
			for item in os.listdir( vncdir ):
				if os.path.isfile( os.path.join( vncdir, item ) ) and item.endswith( '.pid' ):
					try:
						fd = open( os.path.join( vncdir, item ), 'r' )
						pid= fd.readline()[ : -1 ]
						fd.close()
						if os.path.isfile( os.path.join( '/proc', pid, 'cmdline' ) ):
							running = True
					except:
						pass

					break

		ud.debug( ud.ADMIN, ud.ERROR, 'VNC server status: passwort exists: %s running %s' % ( pwdexists, running ) )
		return ( pwdexists, running )

	def vnc_config( self, object ):
		if not self.permitted( 'vnc/config', options = object.options ):
			self.finished( object.id(), {},
						   report = _( 'You are not permitted to run this command.' ),
						   success = False )
			return

		self.finished( object.id(), self._vnc_status() )

	def vnc_start( self, object ):
		pwdexists, running = self._vnc_status()
		res = 0

		if not running:
			res = os.system( 'su - %s -c "vncserver -geometry 800x600"' % self._username )

		self.finished( object.id(), res == 0 )

	def vnc_stop( self, object ):
		pwdexists, running = self._vnc_status()
		if running:
			args = self._vnc_cmdline()
			if '-rfbport' in args:
				port = args[ args.index( '-rfbport' ) + 1 ]
				port = int( port ) - 5900
				os.system( 'su - %s -c "vncserver -kill :%d"' % ( self._username, port ) )

		self.finished( object.id(), True )

	def vnc_password( self, object ):
		if not self.permitted( 'vnc/password', options = object.options ):
			self.finished( object.id(), {},
						   report = _( 'You are not permitted to run this command.' ),
						   success = False )
			return
		cmd = 'su - %s -c "/usr/share/univention-management-console/univention-vnc-setpassword %s"' % \
			  ( self._username, object.options[ 'password' ] )

		os.system( cmd )
		self.finished( object.id(), None )
