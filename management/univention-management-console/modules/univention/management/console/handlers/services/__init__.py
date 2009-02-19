#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: manages system services
#
# Copyright (C) 2006-2009 Univention GmbH
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

import os

import notifier.popen

import univention.config_registry as ucr
import univention.service_info as usi

import _revamp

_ = umc.Translation( 'univention.management.console.handlers.services' ).translate

name = 'services'
icon = 'services/module'
short_description = _( 'System services' )
long_description = _( 'Control over system services' )
categories = [ 'all' ]

class StartType( umc.StaticSelection ):
	def __init__( self ):
		umc.StaticSelection.__init__( self, _( 'Start type' ) )

	def choices( self ):
		return ( ( 'manual', _( 'Manual' ) ), ( 'auto', _( 'Automatically' ) ) )

umcd.copy( umc.StaticSelection, StartType )

service_type = umc.String( _( 'Service' ) )
start_type = StartType()

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
		short_description = _( 'List of services' ),
		method = 'service_list',
		startup = True,
		priority = 100,
	),
	'service/start_auto': umch.command(
		short_description = _( 'Set automatic start' ),
		method = 'service_start_type',
		values = { 'type' : start_type }
	),
	'service/start_manual': umch.command(
		short_description = _( 'Set automatic start' ),
		method = 'service_start_type',
		values = { 'type' : start_type }
	),
	'service/start_never': umch.command(
		short_description = _( 'Set automatic start' ),
		method = 'service_start_type',
		values = { 'type' : start_type }
	),
}

class handler( umch.simpleHandler, _revamp.Web ):
	def __init__( self ):
		global command_description
		umch.simpleHandler.__init__( self, command_description )

	def _run_it( self, services, action ):
		failed = []
		for srv in services:
			if os.system( '/etc/init.d/%s %s' % ( srv, action ) ):
				failed.append( srv )
		return failed

	def service_start( self, object ):
		if self.permitted( 'service/start', options = object.options ):
			cb = notifier.Callback( self._service_changed, object,
									_( 'Starting the following services failed: %(services)s' ) )
			func = notifier.Callback( self._run_it, object.options[ 'service' ], 'start' )
			thread = notifier.threads.Simple( 'service', func, cb )
			thread.run()
		else:
			self.finished( object.id(), {},
						   report = _( 'You are not permitted to run this command.' ),
						   success = False )

	def service_stop( self, object ):
		if self.permitted( 'service/stop', options = object.options ):
			cb = notifier.Callback( self._service_changed, object,
									_( 'Stopping the following services failed: %(services)s' ) )
			func = notifier.Callback( self._run_it, object.options[ 'service' ], 'stop' )
			thread = notifier.threads.Simple( 'service', func, cb )
			thread.run()
		else:
			self.finished( object.id(), {},
						   report = _( 'You are not permitted to run this command.' ),
						   success = False )

	def _service_changed( self, thread, result, object, error_message ):
		if result:
			self.finished( object.id(), {},
						   report = error_message % { 'services' : ', '.join( result ) },
						   success = False )
		else:
			self.finished( object.id(), {} )

	def service_list( self, object ):
		srvs = usi.ServiceInfo()
		umc.registry.load()

		for name, srv in srvs.services.items():
			key = '%s/autostart' % name
			# default: autostart=yes
			if srv.has_key( 'start_type' ):
				key = srv[ 'start_type' ]
			if not umc.registry.has_key( key ):
				srv.autostart = "yes"
			elif umc.registry[ key ].lower() in ( 'no' ):
				srv.autostart = "no"
			elif umc.registry[ key ].lower() in ( 'manually' ):
				srv.autostart = "manually"
			else:
				srv.autostart = "yes"

		self.finished( object.id(), srvs.services )

	def service_start_type( self, object ):
		srvs = usi.ServiceInfo()
		umc.registry.load()

		for name in object.options[ 'service' ]:
			srv = srvs.services.get( name, None )
			if srv:
				key = '%s/autostart' % name
				if srv.has_key( 'start_type' ):
					key = srv[ 'start_type' ]

				value = 'yes'
				if object.arguments[ 0 ] == 'service/start_auto':
					value = 'yes'
				if object.arguments[ 0 ] == 'service/start_manual':
					value = 'manually'
				if object.arguments[ 0 ] == 'service/start_never':
					value = 'no'
				ucr.handler_set( [ '%s=%s' % ( key, value ) ] )
		self.finished( object.id(), None )	

