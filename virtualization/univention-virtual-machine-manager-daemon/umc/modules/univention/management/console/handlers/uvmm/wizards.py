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

import copy

import univention.management.console as umc
import univention.management.console.dialog as umcd
import univention.management.console.protocol as umcp

from types import *

_ = umc.Translation('univention.management.console.handlers.uvmm').translate

class Page( object ):
	def __init__( self, title = '', description = '' ):
		self.title = title
		self.description = description
		self.options = []
		self.buttons = []

	def setup( self, command, options, prev = True, next = True, finish = False ):
		wizard = umcd.Wizard( self.title )
		wizard._content.add_row( [ umcd.Fill( 2, self.description ), ] )
		wizard._content.add_row( [ umcd.Fill( 2, umcd.Text( '' ) ), ] )
		items = []
		for option in self.options:
			if hasattr( option, 'option' ):
				items.append( option.id() )
				if option.option in options:
					option.default = options[ option.option ]
			wizard._content.add_row( [ option, ] )
		wizard._content.add_row( [ umcd.Fill( 2, umcd.Text( '' ) ), ] )
		if not self.buttons:
			if next:
				opts = copy.copy( options )
				opts[ 'action' ] = 'next'
				next_btn = umcd.NextButton( ( umcd.Action( umcp.SimpleCommand( command, opts ), items ), ) )
			elif finish:
				opts = copy.copy( options )
				opts[ 'action' ] = 'finish'
				next_btn = umcd.Button( _( 'Finish' ), 'actions/finish', ( umcd.Action( umcp.SimpleCommand( command, opts ), items ), ), { 'class' : 'button_right' } )
			else:
				next_btn = ''
			if prev:
				opts = copy.copy( options )
				opts[ 'action' ] = 'prev'
				prev = umcp.SimpleCommand( command, opts )
				prev.verify_options = False
				prev_btn = umcd.PrevButton( ( umcd.Action( prev, items ), ) )
			else:
				prev_btn = ''

			wizard._content.add_row( [ prev_btn, next_btn ] )
		else:
			wizard._content.add_row( self.buttons )

		return wizard.setup()

class IWizard( list ):
	def __init__( self, command = '' ):
		list.__init__( self )
		self.current = None
		self.command = command
		self.actions = { 'next' : self.next, 'prev' : self.prev, 'finish' : self.finish }

	def action( self, object ):
		if 'action' in object.options:
			action = object.options[ 'action' ]
			del object.options[ 'action' ]
		else:
			action = 'next'

		if action in self.actions:
			return self.actions[ action ]( object ) != None

		return False

	def setup( self, object ):
		prev = True
		next = True
		finish = False
		if self.current == ( len( self ) - 1 ): # last page
			next = False
			finish = True
		elif not self.current:
			prev = False
		return self[ self.current ].setup( self.command, object.options, prev = prev, next = next, finish = finish )

	def finish( self, object ):
		pass

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
	def __init__( self, command ):
		IWizard.__init__( self, command )
		self.title = _( 'Add a device' )
		self.pool_syntax = DynamicSelect( _( 'Storage pool' ) )
		self.pool_syntax.update_choices( [ '/var/lib/libvirt/images', '/var/lib/xen/images' ] )
		self.image_syntax = DynamicSelect( _( 'Device image' ) )

		# page 0
		page = Page( self.title, _( 'What type of device should be created?' ) )
		page.options.append( umcd.make( ( 'device-type', DriveTypeSelect( _( 'Type of device' ) ) ) ) )
		self.append( page )

		# page 1
		page = Page( self.title, _( 'For the harddrive a new image can be created or an existing image can be used. If you choose to use an existing image make sure that it is not used by another virtual instance at the same time.' ) )
		page.options.append( umcd.make( ( 'existing-or-new-disk', DiskSelect( '' ) ) ) )
		self.append( page )

		# page 2
		page = Page( self.title )
		page.options.append( umcd.make( ( 'device-pool', self.pool_syntax ) ) ) # FIXME: this must be a button
		page.options.append( umcd.make( ( 'device-image', self.image_syntax ) ) )
		self.append( page )

		# page 3
		page = Page( self.title, _( 'Select a storage pool that should be used for the image. The filename and size for the virtual harddrive have been set to default values. You may change these values to fit your needs.' ) )
		page.options.append( umcd.make( ( 'device-pool', self.pool_syntax ) ) )
		page.options.append( umcd.make( ( 'image-name', umc.String( _( 'Filename' ) ) ) ) )
		page.options.append( umcd.make( ( 'image-size', umc.String( _( 'Size' ) ) ) ) )
		self.append( page )

		# page 4
		page = Page( self.title, _( 'The following device will be create:' ) )
		self.append( page )

	def next( self, object ):
		if self.current == 0: #which device type?
			if object.options[ 'device-type' ] == 'disk':
				self.current = 1
			else:
				self.current = 2
		elif self.current == 1: # new or existing disk image?
			if object.options[ 'existing-or-new-disk' ] == 'disk-new':
				self.current = 3
			else:
				self.current = 2
				if object.options[ 'device-type' ] == 'disk':
					self[ self.current ].description = _( 'Select the storage pool and afterwards one of the existing disk images' )
				else:
					self[ self.current ].description = _( 'Select the storage pool and afterwards one of the existing ISO image' )
		elif self.current in ( 2, 3 ): # select existing disk image
			self.current = 4
			self[ self.current ].options = []
			self[ self.current ].options.append( umcd.HTML( _( '<b>Device type</b>: %(type)s' ) % { 'type' : object.options[ 'device-type' ] } ) )
			self[ self.current ].options.append( umcd.HTML( _( '<b>Storage pool</b>: %(pool)s' ) % { 'pool' : object.options[ 'device-pool' ] } ) )
			self[ self.current ].options.append( umcd.HTML( _( '<b>Image filename</b>: %(image)s' ) % { 'image' : object.options[ 'image-name' ] } ) )
			self[ self.current ].options.append( umcd.HTML( _( '<b>Image size</b>: %(size)s' ) % { 'size' : object.options[ 'image-size' ] } ) )
		else:
			if self.current == None:
				self.current = 0
			else:
				self.current += 1

		return self[ self.current ]

	def prev( self, object ):
		if self.current == 3:
			self.current = 1
			return self[ self.current ]

		return IWizard.prev( self, object )

class InstanceWizard( IWizard ):
	def __init__( self, command ):
		IWizard.__init__( self, command )
