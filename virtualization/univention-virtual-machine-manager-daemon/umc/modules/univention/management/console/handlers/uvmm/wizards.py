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

class DriveWizard( umcd.IWizard ):
	def __init__( self, command ):
		umcd.IWizard.__init__( self, command )
		self.title = _( 'Add a drive' )
		self.pool_syntax = DynamicSelect( _( 'Storage pool' ) )
		self.image_syntax = DynamicSelect( _( 'Drive image' ) )
		self.actions[ 'pool-selected' ] = self.pool_selected
		self.uvmm = uvmmd.Client( auto_connect = False )
		self.prev_first_page = False

		# page 0
		page = umcd.Page( self.title, _( 'What type of drive should be created?' ) )
		page.options.append( umcd.make( ( 'drive-type', DriveTypeSelect( _( 'Type of drive' ) ) ) ) )
		self.append( page )

		# page 1
		page = umcd.Page( self.title, _( 'For the harddrive a new image can be created or an existing image can be used. If you choose to use an existing image make sure that it is not used by another virtual instance at the same time.' ) )
		page.options.append( umcd.make( ( 'existing-or-new-disk', DiskSelect( '' ) ) ) )
		self.append( page )

		# page 2
		page = umcd.Page( self.title )
		page.options.append( umcd.Text( '' ) ) # will be replaced with pool selection button
		page.options.append( umcd.make( ( 'drive-image', self.image_syntax ) ) )
		self.append( page )

		# page 3
		page = umcd.Page( self.title, _( 'Select a storage pool that should be used for the image. The filename and size for the virtual harddrive have been set to default values. You may change these values to fit your needs.' ) )
		page.options.append( umcd.Text( '' ) ) # will be replaced with pool selection button
		page.options.append( umcd.make( ( 'image-name', umc.String( _( 'Filename' ) ) ) ) )
		page.options.append( umcd.make( ( 'image-size', umc.String( _( 'Size' ) ) ) ) )
		self.append( page )

		# page 4
		page = umcd.Page( self.title, _( 'The following drive will be create:' ) )
		self.append( page )

	def _create_pool_select_button( self, options ):
		choices = []
		for storage in self.node.storages:
			opts = copy.copy( options )
			opts[ 'action' ] = 'pool-selected'
			opts[ 'drive-pool' ] = storage.name
			action = umcd.Action( umcp.SimpleCommand( self.command, options = opts ) )
			choices.append( { 'description' : storage.name, 'actions' : [ action, ] } )
		return umcd.ChoiceButton( _( 'Pool' ), choices = choices, attributes = { 'width' : '300px' } )

	def reset( self ):
		self.prev_first_page = False
		umcd.IWizard.reset( self )

	def setup( self, object, prev = None, next = None, finish = None, cancel = None ):
		ud.debug( ud.ADMIN, ud.ERROR, 'drive wizard: setup! (current: %s, prev_first_page: %s)' % ( str( self.current ), self.prev_first_page ) )
		if self.current == 0 and self.prev_first_page:
			return umcd.IWizard.setup( self, object, prev = True, next = next, finish = finish, cancel = cancel )
		return umcd.IWizard.setup( self, object, prev = prev, next = next, finish = finish, cancel = cancel )

	def action( self, object, node ):
		ud.debug( ud.ADMIN, ud.ERROR, 'drive wizard: action! (current: %s)' % str( self.current ) )
		self.node_uri, self.node = node
		if self.current == None:
			# read pool
			ud.debug( ud.ADMIN, ud.ERROR, 'drive wizard: node storage pools: %s' % str( self.node.storages ) )
			btn = self._create_pool_select_button( object.options )
			object.options[ 'drive-pool' ] = 'default'
			self[ 2 ].options[ 0 ] = btn
			self[ 3 ].options[ 0 ] = btn

		return umcd.IWizard.action( self, object )

	def pool_selected( self, object ):
		ud.debug( ud.ADMIN, ud.ERROR, 'drive wizard: node storage volumes: %s' % str( self.node_uri ) )
		vols = self.uvmm.storage_pool_volumes( self.node_uri, object.options.get( 'drive-pool', 'default' ), object.options[ 'drive-type' ] )
		ud.debug( ud.ADMIN, ud.ERROR, 'drive wizard: node storage volumes: %s' % str( vols ) )
		self.image_syntax.update_choices( [ os.path.basename( vol.source ) for vol in vols ] )

		return self[ self.current ]

	def _disk_type_text( self, disk_type ):
		if disk_type == 'disk':
			return _( 'hard drive' )
		else:
			return _( 'CDROM drive' )

	def next( self, object ):
		if self.current == 0: # which drive type?
			# initialize pool and image selection
			self.pool_selected( object )
			if object.options[ 'drive-type' ] == 'disk':
				self.current = 1
				self[ 2 ].hint = None
			else:
				self.current = 2
				if self.image_syntax._choices:
					msg = _( 'If the required image is not found, you may copy the ISO image on the server into the directory /var/lib/libvirt/images. After that go to the previous page an return to this one. The image should now be available.' )
				else:
					msg = _( 'The list of available images is empty! You may copy the ISO image on the server into the directory /var/lib/libvirt/images. After that go to the previous page an return to this one. The image should now be available.' )
				self[ 2 ].hint = msg
		elif self.current == 1: # new or existing disk image?
			if object.options[ 'existing-or-new-disk' ] == 'disk-new':
				self.current = 3
			else:
				self.current = 2
				if object.options[ 'drive-type' ] == 'disk':
					self[ self.current ].description = _( 'Select the storage pool and afterwards one of the existing disk images' )
				else:
					self[ self.current ].description = _( 'Select the storage pool and afterwards one of the existing ISO image' )
		elif self.current in ( 2, 3 ): # select existing disk image
			if self.current == 2:
				ud.debug( ud.ADMIN, ud.ERROR, 'drive wizard: collect information about existing disk image: %s' % object.options[ 'drive-image' ] )
				vols = self.uvmm.storage_pool_volumes( self.node_uri, object.options.get( 'drive-pool', 'default' ), object.options[ 'drive-type' ] )
				for vol in vols:
					if vol.source == object.options[ 'drive-image' ]:
						ud.debug( ud.ADMIN, ud.ERROR, 'drive wizard: set information about existing disk image: %s' % object.options[ 'drive-image' ] )
						object.options[ 'image-name' ] = os.path.basename( object.options[ 'drive-image' ] )
						object.options[ 'image-size' ] = MemorySize.num2str( vol.size )
				if not object.options[ 'drive-image' ] in object.options.get( '_reuse_image', [] ) and vol.device == uvmmn.Disk.DEVICE_DISK and self.uvmm.is_image_used( self.node_uri, object.options[ 'drive-image' ] ):
					if '_reuse_image' in object.options:
						object.options[ '_reuse_image' ].append( object.options[ 'drive-image' ] )
					else:
						object.options[ '_reuse_image' ] = [ object.options[ 'drive-image' ], ]
					return umcd.WizardResult( False, _( 'The selected image is already used by another virtual instance. You may consider to choose another image or continue if you are sure that it will not cause any problems.' ) )
			self.current = 4
			self[ self.current ].options = []
			conf = umcd.List()
			conf.add_row( [ umcd.HTML( '<i>%s</i>' % _( 'Drive type' ) ), self._disk_type_text( object.options[ 'drive-type' ] ) ] )
			conf.add_row( [ umcd.HTML( '<i>%s</i>' % _( 'Storage pool' ) ), _( 'path: %(path)s' ) % { 'path' : self._disk_type_text( object.options[ 'drive-type' ] ) } ] )
			conf.add_row( [ umcd.HTML( '<i>%s</i>' % _( 'Image filename' ) ), object.options[ 'image-name' ] ] )
			conf.add_row( [ umcd.HTML( '<i>%s</i>' % _( 'Image size' ) ), object.options[ 'image-size' ] ] )
			self[ self.current ].options.append( conf )
			# self[ self.current ].options.append( umcd.HTML( _( '<b>Drive type</b>: %(type)s' ) % { 'type' : self._disk_type_text( object.options[ 'drive-type' ] ) } ) )
			# self[ self.current ].options.append( umcd.HTML( _( '<b>Storage pool</b>: %(pool)s (path: %(path)s)' ) % { 'pool' : object.options[ 'drive-pool' ], 'path' : self._get_pool_path( object.options[ 'drive-pool' ] ) } ) )
			# self[ self.current ].options.append( umcd.HTML( _( '<b>Image filename</b>: %(image)s' ) % { 'image' : object.options[ 'image-name' ] } ) )
			# self[ self.current ].options.append( umcd.HTML( _( '<b>Image size</b>: %(size)s' ) % { 'size' : object.options[ 'image-size' ] } ) )
		else:
			if self.current == None:
				self.current = 0
			else:
				self.current += 1

		return umcd.WizardResult()

	def prev( self, object ):
		if self.current == 2:
			self.current = 0
		elif self.current == 3:
			self.current = 1
		elif self.current == 4:
			if object.options[ 'existing-or-new-disk' ] == 'disk-new' and object.options[ 'drive-type' ] == 'disk':
				self.current = 3
			else:
				self.current = 2
		else:
			return umcd.IWizard.prev( self, object )

		return umcd.WizardResult()

	def _get_pool_path( self, pool_name ):
		for pool in self.node.storages:
			if pool.name == pool_name:
				return pool.path

		return ''

	def finish( self, object ):
		# collect information about the drive
		disk = uvmmn.Disk()
		if object.options[ 'drive-type' ] == 'disk':
			disk.device = uvmmn.Disk.DEVICE_DISK
		else:
			disk.device = uvmmn.Disk.DEVICE_CDROM
		disk.size = MemorySize.str2num( object.options[ 'image-size' ], unit = 'MB' )

		disk.source = self._get_pool_path( object.options[ 'drive-pool' ] )
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
		self.drive_wizard = DriveWizard( command )
		self.drive_wizard_active = False
		self.actions[ 'new-drive' ] = self.new_drive
		self.drives = []

		# page 0
		page = umcd.Page( self.title, _( 'By selecting a profile for the virtual instance most of the settings will be filled out with default values. In the following step these values may be modified.' ) )
		page.options.append( umcd.make( ( 'instance-profile', self.profile_syntax ) ) )
		self.append( page )

		# page 1
		page = umcd.Page( self.title, _( 'The settings shown below are all read from the selected profile. Please verify that these values fits your environment. At least the name for the virtual instance should be modified.' ) )
		page.options.append( umcd.make( ( 'name', umc.String( _( 'Name' ) ) ) ) )
		page.options.append( umcd.make( ( 'memory', umc.String( _( 'Memory (in MB)' ) ) ) ) )
		page.options.append( umcd.make( ( 'cpus', NumberSelect( _( 'CPUs' ) ) ) ) )
		page.options.append( umcd.make( ( 'vnc', umc.Boolean( _( 'VNC' ) ) ) ) )
		self.append( page )

		# page 2
		page = umcd.Page( self.title, umcd.HTML( _( 'The virtual instance will be created with the settings shown below. You may now add additional drives by clicking the button <i>Add drive</i>' ) ) )
		page.options.append( umcd.HTML( '' ) )
		add_btn = umcd.Button( _( 'Add drive' ), 'uvmm/add', ( umcd.Action( umcp.SimpleCommand( command, options = { 'action' : 'new-drive' } ) ), ) )
		page.actions.append( add_btn )
		self.append( page )

	def action( self, object, node ):
		self.node_uri, self.node = node
		return umcd.IWizard.action( self, object )

	def next( self, object ):
		if self.drive_wizard_active:
			return self.drive_wizard.next( object )
		if not 'instance-profile' in object.options:
			self.replace_title( _( 'Create a virtual instance' ) )
		else:
			if not object.options.get( 'name' ):
				self.replace_title( _( 'Create a virtual instance (profile: %(profile)s)' ) % { 'profile' : object.options[ 'instance-profile' ] } )
			else:
				self.replace_title( _( 'Create a virtual instance <i>%(name)s</i>' ) % { 'name' : object.options[ 'name' ] } )
		if self.current == 0:
			self.profile = self.udm.get_profile( object.options[ 'instance-profile' ] )
			ud.debug( ud.ADMIN, ud.ERROR, 'drive wizard: next: profile boot drives: %s' % str( self.profile[ 'bootdev' ] ) )
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
			mem_size = MemorySize.str2num( object.options[ 'memory' ], unit = 'MB' )
			four_mb = MemorySize.str2num( '4', unit = 'MB' )
			if mem_size < four_mb:
				object.options[ 'memory' ] = '4 MB'
				return umcd.WizardResult( False, _( 'You must at least use 4 MB for a virtual instance.' ) )
			if mem_size > self.max_memory:
				object.options[ 'memory' ] = MemorySize.num2str( self.max_memory * 0.75 )
				return umcd.WizardResult( False, _( 'Your physical server does not have that much memory. As a suggestion the a mount of memory was set to 75% of the available memory.' ) )
			# activate drive wizard to add a first mandatory drive
			if not self.drives:
				self.drive_wizard.prev_first_page = True
				self.new_drive( object, cancel = False )
		return umcd.IWizard.next( self, object )

	def prev( self, object ):
		if self.drive_wizard_active:
			if self.drive_wizard.current == 0:
				self.drive_wizard_active = False
				self.drive_wizard.reset()
			else:
				return self.drive_wizard.prev( object )

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

		rows.append( [ umcd.HTML( '<b>%s</b><br>' % _( 'Attached drives' ) ), ] )

		dev_template = _( '<li>%(type)s: %(size)s (image file %(image)s in pool %(pool)s)</li>' )
		html = '<ul class="umc_listing">'
		for dev in self.drives:
			values = {}
			if dev.device == uvmmn.Disk.DEVICE_DISK:
				values[ 'type' ] = _( 'hard drive' )
			else:
				values[ 'type' ] = _( 'CDROM drive' )
			values[ 'size' ] = MemorySize.num2str( dev.size )
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
		if self.drive_wizard_active:
			self.drive_wizard_active = False
			self.drive_wizard.finish( object )
			self.drives.append( self.drive_wizard.result() )
			self._list_domain_settings( object )
			self.drive_wizard.reset()
		else:
			domain = uvmmp.Data_Domain()
			domain.name = object.options[ 'name' ]
			domain.arch = object.options[ 'arch' ]
			domain.domain_type, domain.os_type = object.options[ 'type' ].split( '-' )
			domain.maxMem = MemorySize.str2num( object.options[ 'memory' ], unit = 'MB' )
			domain.vcpus = object.options[ 'cpus' ]
			if object.options[ 'bootdev' ] and object.options[ 'bootdev' ][ 0 ]:
				ud.debug( ud.ADMIN, ud.ERROR, 'device wizard: boot drives: %s' % str( object.options[ 'bootdev' ] ) )
				domain.boot = object.options[ 'bootdev' ]
			if object.options[ 'vnc' ]:
				gfx = uvmmn.Graphic()
				gfx.listen = '0.0.0.0'
				gfx.keymap = object.options[ 'kblayout' ]
				domain.graphics = [ gfx, ]
			# set drive names
			dev_name = 'a'
			for dev in self.drives:
				dev.target_dev = 'hd%s' % dev_name
				dev_name = chr( ord( dev_name ) + 1 )
			domain.disks = self.drives
			iface = uvmmn.Interface()
			iface.source = object.options[ 'interface' ]
			self._result = domain

		return umcd.WizardResult()

	def new_drive( self, object, cancel = True ):
		# all next, prev and finished events must be redirected to the drive wizard
		self.drive_wizard_active = True
		self.drive_wizard_cancel = cancel
		self.drive_number += 1
		object.options[ 'image-name' ] = object.options[ 'name' ] + '-%d.img' % self.drive_number
		object.options[ 'image-size' ] = '8 GB'
		self.drive_wizard.replace_title( _( 'Add drive to <i>%(name)s</i>' ) % { 'name' : object.options[ 'name' ] } )
		return self.drive_wizard.action( object, ( self.node_uri, self.node ) )

	def setup( self, object, prev = None, next = None, finish = None, cancel = None ):
		if self.drive_wizard_active:
			return self.drive_wizard.setup( object, finish = _( 'Add' ), cancel = self.drive_wizard_cancel )
		return umcd.IWizard.setup( self, object, cancel = False )

	def cancel( self, object ):
		if self.drive_wizard_active:
			self.drive_wizard_active = False
			# fall back to instance overview
			self.current = 2
			self.drive_wizard.reset()

		return umcd.WizardResult()

	def reset( self ):
		self.drives = []
		self.drive_number = 0
		self.drive_wizard.reset()
		umcd.IWizard.reset( self )
