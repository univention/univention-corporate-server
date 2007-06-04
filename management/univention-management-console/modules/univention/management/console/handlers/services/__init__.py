#!/usr/bin/python2.4
#
# Univention Management Console
#  module: manages system services
#
# Copyright (C) 2006, 2007 Univention GmbH
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
import univention.management.console.categories as umcc


import os

import notifier.popen

import univention_service_info as usi

import _revamp

_ = umc.Translation( 'univention.management.console.handlers.services' ).translate

name = 'services'
icon = 'services/module'
short_description = _( 'System Services' )
long_description = _( 'controls system services' )
categories = [ 'all', 'services' ]

umcc.insert( umcc.Category( 'services', _( 'Services' ), _( 'Control Services' ), priority = 10 ) )

service_type = umc.String( _( 'Service' ) )

command_description = {
	'service/start': umch.command(
		short_description = _( 'Start a service' ),
		method = 'service_start',
		values = { 'service': service_type },
	),
	'service/stop': umch.command(
		short_description = _( 'Stop a service' ),
		method = 'service_stop',
		values = { 'service': service_type },
	),
	'service/restart': umch.command(
		short_description = _( 'Restart a service' ),
		method = 'service_restart',
		values = { 'service': service_type },
	),
	'service/reload': umch.command(
		short_description = _( 'Reload a service' ),
		method = 'service_reload',
		values = { 'service': service_type },
	),
	'service/status': umch.command(
		short_description = _( 'Stop a service' ),
		method = 'service_stop',
		values = { 'service': service_type },
		),
	'service/remove': umch.command(
		short_description = _( 'Remove a service' ),
		method = 'service_remove',
		values = { 'service': service_type },
	),
	'service/add': umch.command(
		short_description = _( 'Add a service' ),
		method = 'service_add',
		values = { 'service': service_type },
	),
	'service/list': umch.command(
		short_description = _( 'List all services' ),
		method = 'service_list',
		startup = True,
		priority = 100,
	),
}

class handler( umch.simpleHandler, _revamp.Web ):
	def __init__( self ):
		global command_description
		umch.simpleHandler.__init__( self, command_description )

# 	def __execute_service( self, service, cmd, callback ):
# 		init_script = '/etc/init.d/%s' % service

# 		if os.path.exists( init_script ):
# 			proc = notifier.popen.Shell( '%s %s' % ( init_script, cmd ),
# 										 stdout = False )
# 			proc.signal_connect( 'finished', callback )

# 	def _done( self, pid, status, stdout, id, dialog ):
# 		if not status:
# 			dialog.append( umcd.Text( _( 'Service started successfully.' ) ) )
# 			self.finished( id, dialog )
# 		else:
# 			dialog.append( umcd.Text( _( 'Failed to start service.' ) ) )
# 			self.finished( id, dialog, success = False )

# 	def __doit( self, object, action ):
# 		if object.options.has_key( 'service' ):
# 			cb = notifier.Callback( self._done, object.id(), umcd.Dialog() )
# 			self.__execute_service( object.options[ 'service' ], 'start', cb )

# 	def service_start( self, object ):
# 		self.__doit( object, 'start' )

# 	def service_stop( self, object ):
# 		self.__doit( object, 'stop' )

# 	def service_reload( self, object ):
# 		self.__doit( object, 'reload' )

# 	def service_restart( self, object ):
# 		self.__doit( object, 'restart' )

# 	def service_status( self, object ):
# 		lst = umcd.List()

# 		lst.setHeader( [ umcd.Text( _( 'Name' ) ), umcd.Text( _( 'Status' ) ) ] )

# 		if object.options.has_key( 'service' ):
# 			if type( object.options[ 'service' ]) == type( [ ] ):
# 				for srv in object.options[ 'service' ]:
# 					if self.__valid_srv( srv ):
# 						# This is still blocking, but may be fast enough
# 						status = self.__service_status( srv )
# 						lst.appendRow( [ umcd.Text ( srv ),
# 										 umcd.Text( status ) ] )

# 		self.finished( object.id(), umcd.Dialog( [ lst ] ) )

# 	def service_remove( self, object ):
# 		pass

# 	def service_add( self, object ):
# 		pass

	def service_list( self, object ):
		srvs = usi.ServiceInfo()

		self.finished( object.id(), srvs.services )
