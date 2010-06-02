#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: management of OpenDVDI instances
#
# Copyright (C) 2010 Univention GmbH
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
import univention.management.console.protocol as umcp

import univention.debug as ud
import univention.config_registry as ucr

import copy
import os
import socket

import notifier.popen

from uvmmd import *
from broker import *

_ = umc.Translation('univention.management.console.handlers.opendvdi').translate

name = 'opendvdi'
icon = 'opendvdi/module'
short_description = _('OpenDVDI')
long_description = _('Management of OpenDVDI connections')
categories = [ 'system', 'all' ]
# hide_tabs = True

class SearchKeys( umc.StaticSelection ):
	def __init__( self, required = True ):
		umc.StaticSelection.__init__( self, unicode( _( 'Search key' ) ), required = required )

	def choices( self ):
		return ( ( 'username', _( 'Username' ) ), ( 'client', _( 'Client' ) ) )

umcd.copy( umc.StaticSelection, SearchKeys )

command_description = {
	'opendvdi/session/search': umch.command(
		short_description = _('Sessions'),
		long_description = _('Sessions'),
		method = 'uvmm_session_search',
		values = {
			'key' : SearchKeys(),
			'filter' : umcd.String( _( 'Filter' ) ),
			},
		startup = True,
		),
	'opendvdi/instance/search': umch.command(
		short_description = _('Templates'),
		long_description = _('Templates'),
		method = 'uvmm_instance_search',
		values = {
			'instance' : umcd.String( _( 'Virtual instance' ) ),
			},
		startup = True,
		),
	'opendvdi/session/view': umch.command(
		short_description = _('Session details'),
		long_description = _('Session details'),
		method = 'uvmm_session_view',
		values = {
			'session' : umcd.String( _( 'Session ID' ) ),
			},
		),
	'opendvdi/template/create': umch.command(
		short_description = _('Create Template'),
		long_description = _('Create Template'),
		method = 'uvmm_template_create',
		values = {
			'username' : umcd.String( _( 'Name' ) ),
			'creation_time' : umcd.String( _( 'Creation time' ) ),
			'name' : umcd.String( _( 'Name' ) ),
			'os' : umcd.String( _( 'Operating System' ) ),
			'description' : umcd.String( _( 'Description' ) ),
			},
		),
}

class handler( umch.simpleHandler ):
	def __init__( self ):
		global command_description
		umch.simpleHandler.__init__( self, command_description )
		self.broker = SessionBroker()
		self.uvmm = UVMM_Client( auto_connect = False )

	def opendvdi_session_search( self, object ):
		res = umcp.Response( object )

		select = umcd.make( self[ 'opendvdi/session/search' ][ 'key' ], default = 'username', attributes = { 'width' : '200' } )
		text = umcd.make( self[ 'opendvdi/session/search' ][ 'filter' ], default = object.options.get( 'filter', '*' ), attributes = { 'width' : '250' } )
		form = umcd.SearchForm( 'opendvdi/session/search', [ [ ( select, 'username' ), ( text, '*' ) ] ] )

		if object.incomplete:
			res.dialog = form
			self.finished( object.id(), res )
			return

		# FIXME: retrieve list from session broker
		key = object.options[ 'key' ]
		filter = object.options[ 'filter' ]
		if key == 'username':
			sessions = self.broker.get_sessions( username = filter )
		else:
			sessions = self.broker.get_sessions( client = filter )

		result = umcd.List()
		result.set_header( [ _( 'User' ), _( 'Client' ), _( 'Server' ), _( 'Status' ) ] )
		for session in sessions:
			result.add_row( [] )
		
		res.dialog = [ form, result ]
		self.finished( object.id(), res )

	def opendvdi_session_view( self, object ):
		res = umcp.Response( object )
		info = self.broker.get_session( object.options[ 'id' ] )

		lst = umcd.List()
		lst.add_row( [ _( 'Username' ), '' ] )
		lst.add_row( [ _( 'Client' ), '' ] )
		lst.add_row( [ _( 'Server' ), '' ] )
		session = umcd.List()
		session.add_row( [ _( 'Status' ), '' ] )
		session.add_row( [ _( 'Type' ), '' ] )
		session.add_row( [ _( 'Started' ), '' ] )
		session.add_row( [ _( 'Virtual instance' ), '' ] )
		session.add_row( [ _( 'Update intervall' ), '' ] )
		session.add_row( [ _( 'Last update' ), '' ] )

		res.dialog = [ lst, umcd.Section( _( 'Session' ), session, hidable = False ) ]
		self.finished( object.id(), res )

	def opendvdi_instance_search( self, object ):
		res = umcp.Response( object )
		text = umcd.make( self[ 'opendvdi/instance/search' ][ 'filter' ], default = object.options.get( 'filter', '*' ), attributes = { 'width' : '250' } )
		form = umcd.SearchForm( 'opendvdi/instance/search', [ [ ( text, '*' ) ] ] )

		if object.incomplete:
			res.dialog = form
			self.finished( object.id(), res )
			return

		result = umcd.List()
		result.set_header( [ _( 'User' ), _( 'Client' ), _( 'Server' ), _( 'Status' ) ] )
		for session in sessions:
			result.add_row( [] )
		
		res.dialog = [ form, result ]
		
		self.finished( object.id(), res )

	def opendvdi_template_create( self, object ):
		res = umcp.Response( object )
		self.finished( object.id(), res )

