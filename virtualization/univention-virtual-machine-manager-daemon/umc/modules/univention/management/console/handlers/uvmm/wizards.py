#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Virtual Machine Manager
#  module: wizards for devices and virtual instances
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
import univention.management.console.dialog as umcd

_ = umc.Translation('univention.management.console.handlers.uvmm').translate

class Page( object ):
	def __init__( self, title = '', description = '' ):
		self.title = title
		self.description = description
		self.options = []
		self.buttons = []

	def setup( self, command, prev = True, next = True ):
		wizard = umcd.Wizard( self.title )
		wizard._content.add_row( [ umcd.Fill( 2, description ), ] )
		wizard._content.add_row( [ umcd.Fill( 2, umcd.Text( '' ) ), ] )
		items = []
		for option in self.options:
			items.append( option.id() )
			wizard._content.add_row( [ option, ] )
		wizard._content.add_row( [ umcd.Fill( 2, umcd.Text( '' ) ), ] )
		if not self.buttons:
			if next:
				next_btn = umcd.NextButton( ( umcd.Action( umcp.SimpleCommand( command, { 'action' : 'next' } ), items ), ) )
			else:
				next_btn = ''
			if pref:
				prev_btn = umcd.PrevButton( ( umcd.Action( umcp.SimpleCommand( command, { 'action' : 'prev' } ), items ), ) )
			else:
				prev_btn = ''

			wizard._content.add_row( [ prev_btn, next_btn ] )
		else:
			wizard._content.add_row( self.buttons )

		return wizard.setup()

class IWizard( list ):
	def __init__( self ):
		list.__init__( self )
		self.current = None
		self.actions = { 'next' : self.next, 'prev' : self.prev }

	def action( self, object ):
		if 'action' in object.options:
			action = object.options[ 'action' ]
			del object.options[ 'action' ]
		else:
			action = 'next'

		if action in self.actions:
			return self.actions[ action ]( object )

		return None

	def next( self, object ):
		if self.current == None:
			self.current = 0
		elif self.current == ( len( self ) - 1 ):
			return None
		else:
			self.current += 1

		return self[ self.current ]

	def prev( self, object ):
		if self.current == 0:
			return None
		else:
			self.current -= 1

		return self[ self.current ]

class DeviceWizard( IWizard ):
	def __init__( self ):
		IWizard.__init__( self )

		page = Page( _( 'Create Device' ), _( 'What type of device should be created?' ) )
		page.options.append( umcd.make( ( 'device_type', DriveTypeSelect( _( 'Type of device' ) ) ) ) )
		self.append( page )

		page = Page( _( 'New or existing harddrive' ), _( 'For the harddrive a new image can be created or an existing image can be used. If you choose to use an existing image make sure that it is not used by another virtual instance at the same time.' ) )
		page.options.append( umcd.make( ( 'device_type', DiskSelect( '' ) ) ) )
		self.append( page )

		page = Page( _( '' ), _( 'For the harddrive a new image can be created or an existing image can be used. If you choose to use an existing image make sure that it is not used by another virtual instance at the same time.' ) )
		page.options.append( umcd.make( ( 'existing-or-new-disk', DiskSelect( '' ) ) ) )
		self.append( page )

	def next( self, object ):
		if self.current == 0:
			if object.options[ 'device_type' ] == 'disk':
				self.current = 1
			else:
				self.current = 2
		elif self.current == 1: # new or existing disk image?
			self.current = 3
			if object.options[ 'existing-or-new-disk' ] == 'disk-new':
				pass
			else:
				self.current = 3
		else:
			self.current += 1

		return self[ self.current ]

class InstanceWizard( IWizard ):
	def __init__( self ):
		IWizard.__init__( self )
