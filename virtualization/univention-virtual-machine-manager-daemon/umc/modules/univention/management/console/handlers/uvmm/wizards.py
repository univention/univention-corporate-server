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
		self.reset()
		self.domain = None

		# page 0
		page = umcd.Page( self.title, _( 'What type of drive should be created?' ) )
		page.options.append( umcd.make( ( 'drive-type', DriveTypeSelect( _( 'Type of drive' ) ) ) ) )
		self.append( page )

		# page 1
		page = umcd.Page( self.title, _( 'For the hard drive a new image can be created or an existing one can be chosen. An existing image should only be used by one virtual instance at a time.' ) )
		page.options.append( umcd.make( ( 'existing-or-new-disk', DiskSelect( '' ) ) ) )
		self.append( page )

		# page 2
		page = umcd.Page( self.title )
		page.options.append( umcd.Text( '' ) ) # will be replaced with pool selection button
		page.options.append( umcd.make( ( 'drive-image', self.image_syntax ) ) )
		self.append( page )

		# page 3
		page = umcd.Page( self.title, _( 'Each hard drive image is located within a so called storage pool, which might be a local directory, a device, an LVM volume or any type of share (e.g. mounted via iSCSI, NFS or CIFS). The newly create image will have the specified name and size provided by the following settings. Currently these was been set to default images. It has to be ensured that there is enough space left in the defined storage pool.' ) )
		page.options.append( umcd.Text( '' ) ) # will be replaced with pool selection button
		page.options.append( umcd.make( ( 'image-name', umc.String( _( 'Filename' ) ) ) ) )
		page.options.append( umcd.make( ( 'image-size', umc.String( _( 'Size (default unit MB)' ), regex = MemorySize.SIZE_REGEX ) ) ) )
		self.append( page )

		# page 4
		page = umcd.Page( self.title, _( 'The following drive will be created:' ) )
		self.append( page )

	def _create_pool_select_button( self, options, button = True ):
		choices = []
		ud.debug( ud.ADMIN, ud.INFO, 'DRIVE-POOL: %s' % options.get( 'drive-pool', 'NOT SET' ) )
		opts = copy.deepcopy( options )
		opts[ 'action' ] = 'pool-selected'
		action = umcd.Action( umcp.SimpleCommand( self.command, options = opts ) )
		for storage in self.node.storages:
			if not storage.active:
				continue
			if storage.name == 'default':
				descr = _( 'Local directory' )
			else:
				descr = storage.name
			choices.append( ( storage.name, descr ) )
		ud.debug( ud.ADMIN, ud.INFO, 'DRIVE-POOL: %s' % options.get( 'drive-pool', 'NOT SET' ) )
		if button:
			return umcd.SimpleSelectButton( _( 'Pool' ), option = 'drive-pool', choices = choices, actions = [ action ], attributes = { 'width' : '300px' }, default = options.get( 'drive-pool' ) )
		self.pool_syntax.update_choices( choices )
		return umcd.Selection( ( 'drive-pool', self.pool_syntax ), default = options.get( 'drive-pool' ), attributes = { 'width' : '300px' } )

	def reset( self ):
		self.replace_title( self.title )
		self.prev_first_page = False
		umcd.IWizard.reset( self )

	def setup( self, object, prev = None, next = None, finish = None, cancel = None ):
		ud.debug( ud.ADMIN, ud.INFO, 'drive wizard: setup! (current: %s, prev_first_page: %s)' % ( str( self.current ), self.prev_first_page ) )
		if self.current == 0 and self.prev_first_page:
			return umcd.IWizard.setup( self, object, prev = True, next = next, finish = finish, cancel = cancel )
		return umcd.IWizard.setup( self, object, prev = prev, next = next, finish = finish, cancel = cancel )

	def action( self, object, node ):
		ud.debug( ud.ADMIN, ud.INFO, 'drive wizard: action! (current: %s)' % str( self.current ) )
		self.node_uri, self.node = node
		if self.current == None:
			# read pool
			ud.debug( ud.ADMIN, ud.INFO, 'drive wizard: node storage pools: %s' % str( self.node.storages ) )
			object.options[ 'drive-pool' ] = 'default'
			object.options[ 'image-size' ] = '8 GB'
		return umcd.IWizard.action( self, object )

	def pool_selected( self, object ):
		ud.debug( ud.ADMIN, ud.INFO, 'drive wizard: node storage volumes: %s' % str( self.node_uri ) )
		vols = self.uvmm.storage_pool_volumes( self.node_uri, object.options.get( 'drive-pool', 'default' ), object.options[ 'drive-type' ] )
		ud.debug( ud.ADMIN, ud.INFO, 'drive wizard: node storage volumes: %s' % map(str, vols))
		choices = []
		for vol in vols:
			basename = os.path.basename( vol.source )
			if basename.rfind( '.' ) >= 0:
				suffix = basename[ basename.rfind( '.' ) + 1 : ]
				if suffix in ( 'xml', 'snapshot' ):
					continue
			choices.append( basename )
		choices.sort()
		self.image_syntax.update_choices( choices )

		# recreate pool button
		btn = self._create_pool_select_button( object.options )
		self[ 2 ].options[ 0 ] = btn
		self[ 3 ].options[ 0 ] = btn

		if object.options[ 'drive-type' ] == 'disk':
			self[ 2 ].hint = None
		elif object.options['drive-type'] == 'cdrom':
			if self.image_syntax._choices:
				msg = _( "If the required ISO image is not found it might be added by copying the file into the storage pool, e.g. to /var/lib/libvirt/images/ which is the directory of the storage pool <i>local directory</i>. After that go to the previous page an return to this one. The image should now be listed." )
			else:
				msg = _( "The list of available images is empty! To add an ISO image the file needs to be copied into the storage pool, e.g. to /var/lib/libvirt/images/ which is the directory of the storage pool <i>local directory</i>. After that go to the previous page an return to this one. The image should now be listed." )
			self[ 2 ].hint = msg
			self[ 2 ].description = ''
		else:
			raise Exception('Invalid drive-type "%s"' % object.options['drive-type'])

		return self[ self.current ]

	def _disk_type_text( self, disk_type ):
		if disk_type == 'disk':
			return _( 'hard drive' )
		if disk_type == 'cdrom':
			return _( 'CDROM drive' )
		else:
			return _('unknown')

	def next( self, object ):
		if self.current == 0: # which drive type?
			# initialize pool and image selection
			self.pool_selected( object )
			if object.options[ 'drive-type' ] == 'disk':
				self.current = 1
				object.options[ 'drive-pool' ] = 'default'
				object.options[ 'image-size' ] = '8 GB'
				if object.options.get( 'domain', 'NONE' ) != 'NONE':
					self.uvmm.next_drive_name( self.node_uri, object.options.get( 'domain' ), object )
			elif object.options['drive-type'] == 'cdrom':
				self.current = 2
		elif self.current == 1: # new or existing disk image?
			if object.options[ 'existing-or-new-disk' ] == 'disk-new':
				self.current = 3
				btn = self._create_pool_select_button( object.options, button = False )
				self[ 2 ].options[ 0 ] = btn
				self[ 3 ].options[ 0 ] = btn
			else:
				self.pool_selected( object )
				# btn = self._create_pool_select_button( object.options, button = True )
				self.current = 2
				if object.options[ 'drive-type' ] == 'disk':
					self[ self.current ].description = _( 'Each hard drive image is located within a so called storage pool, which might be a local directory, a device, an LVM volume or any type of share (e.g. mounted via iSCSI, NFS or CIFS). When selecting a storage pool the list of available images is updated.' )
				elif object.options['drive-type'] == 'cdrom':
					self[ self.current ].description = _( 'Each ISO image is located within a so called storage pool, which might be a local directory, a device, an LVM volume or any type of share (e.g. mounted via iSCSI, NFS or CIFS). When selecting a storage pool the list of available images is updated.' )
				else:
					raise Exception('Invalid drive-type "%s"' % object.options['drive-type'])
		elif self.current in ( 2, 3 ): # 2=create new, 3=select existing disk image
			pool_path = self._get_pool_path( object.options[ 'drive-pool' ] )
			if self.current == 2: # select existing disk image
				ud.debug( ud.ADMIN, ud.INFO, 'drive wizard: collect information about existing disk image: %s' % object.options[ 'drive-image' ] )
				drive_pool = object.options['drive-pool']
				drive_type = object.options['drive-type']
				drive_image = object.options['drive-image']
				vols = self.uvmm.storage_pool_volumes(self.node_uri, drive_pool, drive_type)
				for vol in vols:
					if os.path.basename(vol.source) == drive_image:
						ud.debug( ud.ADMIN, ud.INFO, 'drive wizard: set information about existing disk image: %s' % object.options[ 'drive-image' ] )
						object.options[ 'image-name' ] = drive_image
						object.options[ 'image-size' ] = MemorySize.num2str( vol.size )
						break
				else:
					ud.debug(ud.ADMIN, ud.INFO, 'Image not found: pool=%s type=%s image=%s vols=%s' % (drive_pool, drive_type, drive_image, map(str, vols)))
					return umcd.WizardResult(False, _('Image not found') ) # FIXME
			elif self.current == 3: # create new disk image
				object.options[ 'image-size' ] = MemorySize.str2str( object.options[ 'image-size' ], unit = 'MB' )
				# TODO: Bug #19281
				# vol_bytes = MemorySize.str2num( object.options[ 'image-size' ], unit = 'MB' )
				# pool_bytes = self._available_space( object.options[ 'drive-pool' ] )
				# if ( pool_bytes - vol_bytes ) < 0:
				# 	object.options[ 'image-size' ] = MemorySize.num2str( int( pool_bytes * 0.9 ) )
				# 	return umcd.WizardResult( False, _( 'There is not enough space left in the pool. The size is set to the maximum available space left.' ) )
			drive_path = os.path.join( pool_path, object.options[ 'image-name' ] )
			ud.debug( ud.ADMIN, ud.INFO, 'Check if image %s is already used' % drive_path )
			is_used = self.uvmm.is_image_used( self.node_uri, drive_path )
			if is_used in ( object.options.get( 'domain', '' ), object.options.get( 'name', '' ) ):
				return umcd.WizardResult( False, _( 'The selected image is already used by this virtual instance and therefor can not be used.' ) )
			if not drive_path in object.options.get( '_reuse_image', [] ) and object.options[ 'drive-type' ] == 'disk' and is_used:
				if '_reuse_image' in object.options:
					object.options[ '_reuse_image' ].append( drive_path )
				else:
					object.options[ '_reuse_image' ] = [ drive_path, ]
				return umcd.WizardResult( False, _( 'The selected image is already used by the virtual instance %(domain)s. It should be considered to choose another image. Continuing might cause problems.' ) % { 'domain' : is_used } )
			self.current = 4
			self[ self.current ].options = []
			conf = umcd.List()
			conf.add_row( [ umcd.HTML( '<i>%s</i>' % _( 'Drive type' ) ), self._disk_type_text( object.options[ 'drive-type' ] ) ] )
			conf.add_row( [ umcd.HTML( '<i>%s</i>' % _( 'Storage pool' ) ), _( 'path: %(path)s' ) % { 'path' : pool_path } ] )
			conf.add_row( [ umcd.HTML( '<i>%s</i>' % _( 'Image filename' ) ), object.options[ 'image-name' ] ] )
			conf.add_row( [ umcd.HTML( '<i>%s</i>' % _( 'Image size' ) ), object.options[ 'image-size' ] ] )
			self[ self.current ].options.append( conf )
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
			if object.options['drive-type' ]== 'disk' and object.options['existing-or-new-disk'] == 'disk-new':
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

	def _available_space( self, pool_name ):
		for pool in self.node.storages:
			if pool.name == pool_name:
				return pool.available

		return -1

	def finish( self, object ):
		# collect information about the drive
		disk = uvmmn.Disk()
		if object.options[ 'drive-type' ] == 'disk':
			disk.device = uvmmn.Disk.DEVICE_DISK
		elif object.options[ 'drive-type' ] == 'cdrom':
			disk.device = uvmmn.Disk.DEVICE_CDROM
		else:
			raise Exception('Invalid drive-type "%s"' % object.options['drive-type'])
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
		self.drive_wizard = DriveWizard( command )
		self.drive_wizard_active = False
		self.actions[ 'new-drive' ] = self.new_drive
		self.actions[ 'pool-selected' ] = self.drive_wizard.pool_selected # FIXME: KeyError 'drive-type'
		self.drives = []

		# page 0
		page = umcd.Page( self.title, _( 'By selecting a profile for the virtual instance most of the settings will be set to default values. In the following steps some of these values might be modified. After the creation of the virtual instance all parameters, extended settings und attached drives can be adjusted. It should be ensured that the profile is for the correct architecture as this option can not be changed afterwards.' ) )
		page.options.append( umcd.make( ( 'instance-profile', self.profile_syntax ) ) )
		self.append( page )

		# page 1
		page = umcd.Page( self.title, _( 'The following settings were read from the selected profile and can be modified now.' ) )
		page.options.append( umcd.make( ( 'name', umc.String( _( 'Name' ) ) ) ) )
		page.options.append( umcd.make( ( 'memory', umc.String( _( 'Memory (in MB)' ), regex = MemorySize.SIZE_REGEX ) ) ) )
		page.options.append( umcd.make( ( 'cpus', NumberSelect( _( 'CPUs' ) ) ) ) )
		page.options.append( umcd.make( ( 'vnc', umc.Boolean( _( 'Enable VNC remote access' ) ) ) ) )
		self.append( page )

		# page 2
		page = umcd.Page( self.title, umcd.HTML( _( 'The virtual instance will be created with the settings shown below. The button <i>Add drive</i> can be used to attach another drive.' ) ) )
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
		tech = self.node_uri[ : self.node_uri.find( ':' ) ]
		if self.current == None:
			profiles = [ item[ 'name' ] for item in self.udm.get_profiles(tech) if item[ 'arch' ] in self.archs ]
			profiles.sort()
			self.profile_syntax.update_choices( profiles )
		if self.current == 0:
			self.profile = self.udm.get_profile( object.options[ 'instance-profile' ], tech )
			ud.debug( ud.ADMIN, ud.INFO, 'drive wizard: next: profile boot drives: %s' % str( self.profile[ 'bootdev' ] ) )
			object.options[ 'name' ] = self.profile[ 'name_prefix' ]
			object.options[ 'arch' ] = self.profile[ 'arch' ]
			object.options[ 'type' ] = self.profile[ 'virttech' ]
			object.options[ 'memory' ] = self.profile[ 'ram' ]
			object.options[ 'cpus' ] = self.profile[ 'cpus' ]
			object.options[ 'bootdev' ] = self.profile[ 'bootdev' ]
			object.options[ 'vnc' ] = self.profile[ 'vnc' ]
			object.options[ 'kblayout' ] = self.profile[ 'kblayout' ]
			object.options[ 'interface' ] = self.profile[ 'interface' ]
			object.options[ 'kernel' ] = self.profile[ 'kernel' ]
			object.options[ 'cmdline' ] = self.profile[ 'kernel_parameter' ]
			object.options[ 'initrd' ] = self.profile[ 'initramfs' ]
		if self.current == 1:
			MAX_NAME_LENGTH = 30
			if object.options[ 'name' ] == self.profile[ 'name_prefix' ]:
				return umcd.WizardResult( False, _( 'The name of the virtual instance should be modified' ) )
			if len( object.options[ 'name' ] ) > MAX_NAME_LENGTH:
				object.options[ 'name' ] = object.options[ 'name' ][ : MAX_NAME_LENGTH ]
				return umcd.WizardResult( False, _( 'The name of a virtual instance may not be longer than %(maxlength)d characters!' ) % { 'maxlength' : MAX_NAME_LENGTH } )
			if not self.uvmm.is_domain_name_unique( self.node_uri, object.options[ 'name' ] ):
				return umcd.WizardResult( False, _( 'The chosen name for the virtual instance is not unique. Another one should be chosen.' ) )
			mem_size = MemorySize.str2num( object.options[ 'memory' ], unit = 'MB' )
			four_mb = MemorySize.str2num( '4', unit = 'MB' )
			if mem_size < four_mb:
				object.options[ 'memory' ] = '4 MB'
				return umcd.WizardResult( False, _( 'A virtual instance must at least have 4 MB memory.' ) )
			if mem_size > self.max_memory:
				object.options[ 'memory' ] = MemorySize.num2str( self.max_memory * 0.75 )
				return umcd.WizardResult( False, _( 'The physical server does not have that much memory. As a suggestion the a mount of memory was set to 75% of the available memory.' ) )
			self.uvmm.next_drive_name( self.node_uri, object.options[ 'domain' ], object )
			# activate drive wizard to add a first mandatory drive
			if not self.drives:
				self.drive_wizard.prev_first_page = True
				self.new_drive( object )
		return umcd.IWizard.next( self, object )

	def prev( self, object ):
		if self.drive_wizard_active:
			if self.drive_wizard.current == 0:
				self.drive_wizard_active = False
				self.drive_wizard.reset()
			else:
				return self.drive_wizard.prev( object )

		if self.current == 2:
			self.replace_title( _( 'Create a virtual instance (profile: %(profile)s)' ) % { 'profile' : object.options[ 'instance-profile' ] } )
		elif self.current == 1:
			del object.options[ 'name' ]
			self.replace_title( _( 'Create a virtual instance' ) )

		return umcd.IWizard.prev( self, object )

	def _list_domain_settings( self, object ):
		'''add list with domain settings to page 2'''
		rows = []
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
			# check configuration for para-virtualized machines
			if domain.os_type == 'xen':
				if self.profile[ 'advkernelconf' ] != 'TRUE': # use pyGrub
					domain.bootloader = '/usr/bin/pygrub'
					domain.bootloader_args = '-q' # Bug #19249: PyGrub timeout
				else:
					domain.kernel = object.options[ 'kernel' ]
					domain.cmdline = object.options[ 'cmdline' ]
					domain.initrd = object.options[ 'initrd' ]
			# memory
			domain.maxMem = MemorySize.str2num( object.options[ 'memory' ], unit = 'MB' )
			# CPUs
			domain.vcpus = object.options[ 'cpus' ]
			# boot devices
			if object.options[ 'bootdev' ] and object.options[ 'bootdev' ][ 0 ]:
				ud.debug( ud.ADMIN, ud.INFO, 'device wizard: boot drives: %s' % str( object.options[ 'bootdev' ] ) )
				domain.boot = object.options[ 'bootdev' ]
			# VNC
			if object.options[ 'vnc' ]:
				gfx = uvmmn.Graphic()
				gfx.listen = '0.0.0.0'
				gfx.keymap = object.options[ 'kblayout' ]
				domain.graphics = [ gfx, ]
			# drives
			domain.disks = self.drives
			self.uvmm._verify_device_files( domain )
			# on PV machines we should move the CDROM drive to first position
			if domain.os_type == 'xen':
				new_disks = []
				for dev in domain.disks:
					if dev.device == uvmmn.Disk.DEVICE_DISK:
						new_disks.append( dev )
					else:
						new_disks.insert( 0, dev )
				domain.disks = new_disks
			# network interface
			if object.options[ 'interface' ]:
				iface = uvmmn.Interface()
				iface.source = object.options[ 'interface' ]
				domain.interfaces = [ iface, ]
			self._result = domain

		return umcd.WizardResult()

	def new_drive( self, object, cancel = True ):
		# all next, prev and finished events must be redirected to the drive wizard
		self.drive_wizard_active = True
		self.drive_wizard_cancel = cancel
		# self.drive_number += 1
		# object.options[ 'image-name' ] = object.options[ 'name' ] + '-%d.img' % self.drive_number
		self.uvmm.next_drive_name( self.node_uri, object.options[ 'name' ], object, temp_drives = [ os.path.basename( drive.source ) for drive in self.drives ] )
		object.options[ 'image-size' ] = '8 GB'
		self.drive_wizard.replace_title( _( 'Add drive to <i>%(name)s</i>' ) % { 'name' : object.options[ 'name' ] } )
		return self.drive_wizard.action( object, ( self.node_uri, self.node ) )

	def setup( self, object, prev = None, next = None, finish = None, cancel = None ):
		if self.drive_wizard_active:
			return self.drive_wizard.setup( object, finish = _( 'Add' ), cancel = self.drive_wizard_cancel )
		return umcd.IWizard.setup( self, object )

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
		self.drive_wizard_active = False
		umcd.IWizard.reset( self )
