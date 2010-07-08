#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Virtual Machine Manager
#  module: wizards for devices and virtual instances
#
# Copyright 2010 Univention GmbH
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

import copy
import os

import univention.management.console as umc
import univention.management.console.dialog as umcd
import univention.management.console.protocol as umcp

import univention.debug as ud

import univention.uvmm.node as uvmmn
import univention.uvmm.protocol as uvmmp

from types import *
from tools import *
import udm
import uvmmd

_ = umc.Translation('univention.management.console.handlers.uvmm').translate

class DeviceWizard( umcd.IWizard ):
	def __init__( self, command ):
		umcd.IWizard.__init__( self, command )
		self.title = _( 'Add a device' )
		self.pool_syntax = DynamicSelect( _( 'Storage pool' ) )
		self.image_syntax = DynamicSelect( _( 'Device image' ) )
		self.actions[ 'pool-selected' ] = self.pool_selected
		self.uvmm = uvmmd.Client( auto_connect = False )

		# page 0
		page = umcd.Page( self.title, _( 'What type of device should be created?' ) )
		page.options.append( umcd.make( ( 'device-type', DriveTypeSelect( _( 'Type of device' ) ) ) ) )
		self.append( page )

		# page 1
		page = umcd.Page( self.title, _( 'For the harddrive a new image can be created or an existing image can be used. If you choose to use an existing image make sure that it is not used by another virtual instance at the same time.' ) )
		page.options.append( umcd.make( ( 'existing-or-new-disk', DiskSelect( '' ) ) ) )
		self.append( page )

		# page 2
		page = umcd.Page( self.title )
		page.options.append( umcd.Text( '' ) ) # will be replaced with pool selection button
		page.options.append( umcd.make( ( 'device-image', self.image_syntax ) ) )
		self.append( page )

		# page 3
		page = umcd.Page( self.title, _( 'Select a storage pool that should be used for the image. The filename and size for the virtual harddrive have been set to default values. You may change these values to fit your needs.' ) )
		page.options.append( umcd.Text( '' ) ) # will be replaced with pool selection button
		page.options.append( umcd.make( ( 'image-name', umc.String( _( 'Filename' ) ) ) ) )
		page.options.append( umcd.make( ( 'image-size', umc.String( _( 'Size' ) ) ) ) )
		self.append( page )

		# page 4
		page = umcd.Page( self.title, _( 'The following device will be create:' ) )
		self.append( page )

	def _create_pool_select_button( self, options ):
		choices = []
		for storage in self.node.storages:
			opts = copy.copy( options )
			opts[ 'action' ] = 'pool-selected'
			opts[ 'device-pool' ] = storage.name
			action = umcd.Action( umcp.SimpleCommand( self.command, options = opts ) )
			choices.append( { 'description' : storage.name, 'actions' : [ action, ] } )
		return umcd.ChoiceButton( _( 'Pool' ), choices = choices )

	def action( self, object, node ):
		ud.debug( ud.ADMIN, ud.ERROR, 'device wizard: action! (current: %s)' % str( self.current ) )
		self.node_uri, self.node = node
		if self.current == None:
			# read pool
			ud.debug( ud.ADMIN, ud.ERROR, 'device wizard: node storage pools: %s' % str( self.node.storages ) )
			btn = self._create_pool_select_button( object.options )
			object.options[ 'device-pool' ] = 'default'
			self[ 2 ].options[ 0 ] = btn
			self[ 3 ].options[ 0 ] = btn

		return umcd.IWizard.action( self, object )

	def pool_selected( self, object ):
		vols = self.uvmm.storage_pool_volumes( self.node_uri, object.options.get( 'device-pool', 'default' ), object.options[ 'device-type' ] )
		ud.debug( ud.ADMIN, ud.ERROR, 'device wizard: node storage volumes: %s' % str( vols ) )
		self.image_syntax.update_choices( [ vol.source for vol in vols ] )

		return self[ self.current ]

	def next( self, object ):
		if self.current == 0: # which device type?
			# initialize pool and image selection
			self.pool_selected( object )
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
			if self.current == 2:
				ud.debug( ud.ADMIN, ud.ERROR, 'device wizard: collect information about existing disk image: %s' % object.options[ 'device-image' ] )
				vols = self.uvmm.storage_pool_volumes( self.node_uri, object.options.get( 'device-pool', 'default' ), object.options[ 'device-type' ] )
				for vol in vols:
					if vol.source == object.options[ 'device-image' ]:
						ud.debug( ud.ADMIN, ud.ERROR, 'device wizard: set information about existing disk image: %s' % object.options[ 'device-image' ] )
						object.options[ 'image-name' ] = os.path.basename( object.options[ 'device-image' ] )
						object.options[ 'image-size' ] = block2byte( vol.size )
				if not object.options[ 'device-image' ] in object.options.get( '_reuse_image', [] ) and vol.device == uvmmn.Disk.DEVICE_DISK and self.uvmm.is_image_used( self.node_uri, object.options[ 'device-image' ] ):
					if '_reuse_image' in object.options:
						object.options[ '_reuse_image' ].append( object.options[ 'device-image' ] )
					else:
						object.options[ '_reuse_image' ] = [ object.options[ 'device-image' ], ]
					return umcd.WizardResult( False, _( 'The selected image is already used by another virtual instance. You may consider to choose another image or continue if you are sure that it will not cause any problems.' ) )
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

		return umcd.WizardResult()

	def prev( self, object ):
		if self.current == 3:
			self.current = 1
			return self[ self.current ]
		if self.current == 4:
			if object.options[ 'existing-or-new-disk' ] == 'disk-new':
				self.current = 3
			else:
				self.current = 2

		return umcd.IWizard.prev( self, object )

	def finish( self, object ):
		# collect information about the device
		disk = uvmmn.Disk()
		if object.options[ 'device-type' ] == 'disk':
			disk.device = uvmmn.Disk.DEVICE_DISK
		else:
			disk.device = uvmmn.Disk.DEVICE_CDROM
		disk.size = byte2block( object.options[ 'image-size' ] )

		for pool in self.node.storages:
			if pool.name == object.options[ 'device-pool' ]:
				disk.source = pool.path
				break
		disk.source = os.path.join( disk.source, object.options[ 'image-name' ] )

		self._result = disk
		return umcd.WizardResult()

class InstanceWizard( umcd.IWizard ):
	def __init__( self, command ):
		umcd.IWizard.__init__( self, command )
		self.title = _( 'Create new virtual instance' )
		self.udm = udm.Client()
		self.uvmm = uvmmd.Client( auto_connect = False )
		self.node = None
		self.profile_syntax = DynamicSelect( _( 'Profiles' ) )
		self.profile_syntax.update_choices( [ item[ 'name' ] for item in self.udm.get_profiles() ] )
		self.device_wizard = DeviceWizard( command )
		self.device_wizard_active = False
		self.actions[ 'new-device' ] = self.new_device
		self.devices = []

		# page 0
		page = umcd.Page( self.title, _( 'By selecting a profile for the virtual instance most of the settings will be filled out with default values. In the following step these values may be modified.' ) )
		page.options.append( umcd.make( ( 'instance-profile', self.profile_syntax ) ) )
		self.append( page )

		# page 1
		page = umcd.Page( self.title, _( 'The settings shown below are all read from the selected profile. Please verify that these values fits your environment. At least the name for the virtual instance should be modified.' ) )
		page.options.append( umcd.make( ( 'name', umc.String( _( 'Name' ) ) ) ) )
		page.options.append( umcd.make( ( 'memory', umc.String( _( 'Memory' ) ) ) ) )
		page.options.append( umcd.make( ( 'cpus', NumberSelect( _( 'CPUs' ) ) ) ) )
		page.options.append( umcd.make( ( 'vnc', umc.Boolean( _( 'VNC' ) ) ) ) )
		self.append( page )

		# page 2
		page = umcd.Page( self.title, umcd.HTML( _( 'The virtual instance will be created with the settings shown below. You may now add additional devices by clicking the button <i>Add device</i>' ) ) )
		page.options.append( umcd.HTML( '' ) )
		add_btn = umcd.Button( _( 'Add device' ), 'uvmm/add', ( umcd.Action( umcp.SimpleCommand( command, options = { 'action' : 'new-device' } ) ), ) )
		page.actions.append( add_btn )
		self.append( page )

	def action( self, object, node ):
		self.node_uri, self.node = node
		return umcd.IWizard.action( self, object )

	def next( self, object ):
		if self.device_wizard_active:
			return self.device_wizard.next( object )
		if not 'instance-profile' in object.options:
			self.replace_title( _( 'Create a virtual instance' ) )
		else:
			self.replace_title( _( 'Create a virtual instance (profile: %(profile)s)' ) % { 'profile' : object.options[ 'instance-profile' ] } )
		if self.current == 0:
			self.profile = self.udm.get_profile( object.options[ 'instance-profile' ] )
			ud.debug( ud.ADMIN, ud.ERROR, 'device wizard: next: profile boot devices: %s' % str( self.profile[ 'bootdev' ] ) )
			object.options[ 'name' ] = self.profile[ 'name_prefix' ]
			object.options[ 'arch' ] = self.profile[ 'arch' ]
			object.options[ 'type' ] = self.profile[ 'virttech' ]
			object.options[ 'memory' ] = self.profile[ 'ram' ]
			object.options[ 'cpus' ] = self.profile[ 'cpus' ]
			object.options[ 'bootdev' ] = self.profile[ 'bootdev' ]
			object.options[ 'vnc' ] = self.profile[ 'vnc' ]
			object.options[ 'kblayout' ] = self.profile[ 'kblayout' ]
			object.options[ 'interface' ] = self.profile[ 'interface' ]
		if self.current == 1:
			if object.options[ 'name' ] == self.profile[ 'name_prefix' ]:
				return umcd.WizardResult( False, _( 'You should modify the name of the virtual instance' ) )
			if not self.uvmm.is_domain_name_unique( self.node_uri, object.options[ 'name' ] ):
				return umcd.WizardResult( False, _( 'The chosen name for the virtual instance is not unique. Please use another one.' ) )
			# activate device wizard to add a first mandatory device
			if not self.devices:
				self.new_device( object, cancel = False )
		return umcd.IWizard.next( self, object )

	def prev( self, object ):
		if self.device_wizard_active:
			return self.device_wizard.prev( object )

		return umcd.IWizard.prev( self, object )

	def _list_domain_settings( self, object ):
		'''add list with domain settings to page 2'''
		rows = []
		# rows.append( [ umcd.HTML( '<b>%s</b><br>' % _( 'Instance settings' ) ), ] )
		settings = umcd.List()
		for text, key in ( ( _( 'Name' ), 'name' ), ( _( 'CPUs' ), 'cpus' ), ( _( 'Memory' ), 'memory' ) ):
			settings.add_row( [ umcd.HTML( '<i>%s</i>' % text ), object.options.get( key, '' ) ] )
		if object.options.get( 'vnc' ):
			value = _( 'activated' )
		else:
			value = _( 'deactivated' )
		settings.add_row( [ umcd.HTML( '<i>%s</i>' % _( 'VNC access' ) ), value ] )
		rows.append( [ settings ] )

		rows.append( [ umcd.HTML( '<b>%s</b><br>' % _( 'Attached devices' ) ), ] )

		dev_template = _( '<li>%(type)s: %(size)s (image file %(image)s in pool %(pool)s)</li>' )
		html = '<ul class="umc_listing">'
		for dev in self.devices:
			values = {}
			if dev.device == uvmmn.Disk.DEVICE_DISK:
				values[ 'type' ] = _( 'hard drive' )
			else:
				values[ 'type' ] = _( 'CDROM drive' )
			values[ 'size' ] = block2byte( dev.size )
			values[ 'image' ] = os.path.basename( dev.source )
			dir = os.path.dirname( dev.source )
			values[ 'pool' ] = dir
			for pool in self.node.storages:
				if pool.path == dir:
					values[ 'pool' ] = pool.name
					break
			html += dev_template % values
		html += '</ul>'
		rows.append( [ umcd.HTML( html ) ] )
		self[ 2 ].options[ 0 ] = umcd.List( content = rows )

	def finish( self, object ):
		if self.device_wizard_active:
			self.device_wizard_active = False
			self.device_wizard.finish( object )
			self.devices.append( self.device_wizard.result() )
			self._list_domain_settings( object )
			self.device_wizard.reset()
		else:
			domain = uvmmp.Data_Domain()
			domain.name = object.options[ 'name' ]
			domain.arch = object.options[ 'arch' ]
			domain.virt_tech = object.options[ 'type' ]
			domain.maxMem = byte2block( object.options[ 'memory' ] )
			domain.vcpus = object.options[ 'cpus' ]
			if object.options[ 'bootdev' ] and object.options[ 'bootdev' ][ 0 ]:
				ud.debug( ud.ADMIN, ud.ERROR, 'device wizard: boot devices: %s' % str( object.options[ 'bootdev' ] ) )
				domain.boot = object.options[ 'bootdev' ]
			if object.options[ 'vnc' ]:
				gfx = uvmmn.Graphic()
				gfx.listen = '0.0.0.0'
				gfx.keymap = object.options[ 'kblayout' ]
				domain.graphics = [ gfx, ]
			# set device names
			dev_name = 'a'
			for dev in self.devices:
				dev.target_dev = 'hd%s' % dev_name
				dev_name = chr( ord( dev_name ) + 1 )
			domain.disks = self.devices
			iface = uvmmn.Interface()
			iface.source = object.options[ 'interface' ]
			self._result = domain

		return umcd.WizardResult()

	def new_device( self, object, cancel = True ):
		# all next, prev and finished events must be redirected to the device wizard
		self.device_wizard_active = True
		self.device_wizard_cancel = cancel
		self.device_number += 1
		object.options[ 'image-name' ] = object.options[ 'name' ] + '-%d.img' % self.device_number
		object.options[ 'image-size' ] = '8 GB'
		return self.device_wizard.action( object, ( self.node_uri, self.node ) )

	def setup( self, object, prev = None, next = None, finish = None, cancel = None ):
		if self.device_wizard_active:
			return self.device_wizard.setup( object, finish = _( 'Add' ), cancel = self.device_wizard_cancel )
		return umcd.IWizard.setup( self, object, cancel = False )

	def cancel( self, object ):
		if self.device_wizard_active:
			self.device_wizard_active = False
			# fall back to instance overview
			self.current = 2
			self.device_wizard.reset()

		return umcd.WizardResult()

	def reset( self ):
		self.devices = []
		self.device_number = 0
		self.device_wizard.reset()
		umcd.IWizard.reset( self )
