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
		self.driver_syntax = DynamicSelect(_('Image format'))
		self.actions[ 'pool-selected' ] = self.pool_selected
		self.actions['type-selected'] = self.type_selected
		self.uvmm = uvmmd.Client( auto_connect = False )
		self.reset()

		# page 0: Select HD or ROM
		page = umcd.Page( self.title, _( 'What type of drive should be created?' ) )
		page.options.append( umcd.make( ( 'drive-type', DriveTypeSelect( _( 'Type of drive' ) ) ) ) )
		self.append( page )

		# page 1: [Only HD] Select existing or new
		page = umcd.Page( self.title, _( 'For the hard drive a new image can be created or an existing one can be chosen. An existing image should only be used by one virtual instance at a time.' ) )
		page.options.append( umcd.make( ( 'existing-or-new-disk', DiskSelect( '' ) ) ) )
		self.append( page )

		# page 2: Select existing image
		page = umcd.Page( self.title )
		page.options.append( umcd.Text( '' ) ) # will be replaced with pool selection button
		page.options.append( umcd.make( ( 'drive-image', self.image_syntax ) ) )
		self.append( page )

		# page 3: [Only new HD] Select name and size
		page = umcd.Page( self.title, _( 'Each hard drive image is located within a so called storage pool, which might be a local directory, a device, an LVM volume or any type of share (e.g. mounted via iSCSI, NFS or CIFS). The newly create image will have the specified name and size provided by the following settings. Currently these was been set to default images. It has to be ensured that there is enough space left in the defined storage pool.' ) )
		page.options.append( umcd.Text( '' ) ) # will be replaced with pool selection button
		page.options.append(umcd.Text('')) # will be replaced with driver type selection button
		page.options.append( umcd.make( ( 'image-name', umc.String( _( 'Filename' ) ) ) ) )
		page.options.append( umcd.make( ( 'image-size', umc.String( _( 'Size (default unit MB)' ), regex = MemorySize.SIZE_REGEX ) ) ) )
		self.append( page )

		# page 4: Show summary
		page = umcd.Page( self.title, _( 'The following drive will be created:' ) )
		self.append( page )

	def _create_pool_select_button(self, options):
		choices = []
		ud.debug( ud.ADMIN, ud.INFO, 'DRIVE-POOL: %s' % options.get( 'drive-pool', 'NOT SET' ) )
		opts = copy.deepcopy( options )
		opts[ 'action' ] = 'pool-selected'
		action = umcd.Action( umcp.SimpleCommand( self.command, options = opts ) )
		for storage in self.storage_pools.values():
			if not storage.active:
				continue
			if storage.name == 'default':
				descr = _( 'Local directory' )
			else:
				descr = storage.name
			choices.append( ( storage.name, descr ) )
		ud.debug( ud.ADMIN, ud.INFO, 'DRIVE-POOL: %s' % options.get( 'drive-pool', 'NOT SET' ) )
		return umcd.SimpleSelectButton(_('Pool'), option='drive-pool', choices=choices, actions=[action], attributes={'width': '300px'}, default=options.get('drive-pool'))

	def _create_type_select_button(self, options, items):
		"""Create list to select driver-type allowed by current driver-pool."""
		# FIXME: items are ignored for some unknown reason
		opts = copy.deepcopy(options)
		opts['action'] = 'type-selected'
		action = umcd.Action(umcp.SimpleCommand(self.command, options=opts), items)
		choices = (
				('RAW', _('Raw format')),
				)
		try:
			drive_pool = options['drive-pool']
			ud.debug(ud.ADMIN, ud.ALL, 'DRIVER-FORMAT: pool=%s' % drive_pool)
			if self._is_file_pool(drive_pool):
				if self.node_uri.startswith('qemu'):
					choices = (
							#('qcow', _('Qemu copy-on-write')),
							('qcow2', _('Qemu copy-on-write 2')),
							#('vmdk', _('VMWare Disk')),
							('raw', _('Raw format')),
							)
				elif self.node_uri.startswith('xen'):
					choices = (
							('raw', _('Raw format')),
							#('qcow2', _('Qemu copy-on-write 2')),
							#('vhd', _('Virtual Hard Disk')),
							#('vmdk', _('VMWare Disk')),
							)
		except LookupError, e:
			ud.debug(ud.ADMIN, ud.ALL, 'DRIVER-FORMAT: pool exception=%s' % e)
		try: # validate current setting
			default = options['driver-type']
			ud.debug(ud.ADMIN, ud.ALL, 'DRIVER-FORMAT: default=%s' % default)
			dict(choices)[default]
		except LookupError, e:
			ud.debug(ud.ADMIN, ud.ALL, 'DRIVER-FORMAT: default exception=%s' % e)
			default = choices[0][0]
		options['driver-type'] = default
		return umcd.SimpleSelectButton(_('Image format'), option='driver-type', choices=choices, actions=[action], attributes={'width': '300px'}, default=default)

	def reset( self ):
		self.replace_title( self.title )
		self.prev_first_page = False
		self.domain_name = None
		self.blacklist = []
		umcd.IWizard.reset( self )

	def setup( self, object, prev = None, next = None, finish = None, cancel = None ):
		ud.debug( ud.ADMIN, ud.INFO, 'drive wizard: setup! (current: %s, prev_first_page: %s)' % ( str( self.current ), self.prev_first_page ) )
		if self.current == 0 and self.prev_first_page:
			return umcd.IWizard.setup( self, object, prev = True, next = next, finish = finish, cancel = cancel )
		return umcd.IWizard.setup( self, object, prev = prev, next = next, finish = finish, cancel = cancel )

	def action( self, object, data ):
		ud.debug( ud.ADMIN, ud.INFO, 'drive wizard: action! (current: %s)' % str( self.current ) )
		self.node_uri, self.node_info = data # node_info is None for new domains!
		if self.current == None:
			# read pool
			ud.debug( ud.ADMIN, ud.INFO, 'drive wizard: node storage pools: %s' % self.node_uri)
			object.options[ 'drive-pool' ] = 'default'
			object.options['driver-type'] = None
			object.options[ 'image-size' ] = '8 GB'
			object.options['image-name'] = None
		return umcd.IWizard.action( self, object )

	def pool_selected( self, object ):
		"""Update list of known images in pool."""
		ud.debug( ud.ADMIN, ud.INFO, 'drive wizard: node storage volumes: %s' % self.node_uri)
		drive_pool = object.options.get('drive-pool', 'default')
		drive_type = object.options['drive-type']
		vols = self.uvmm.storage_pool_volumes(self.node_uri, drive_pool, drive_type)
		ud.debug( ud.ADMIN, ud.INFO, 'drive wizard: node storage volumes: %s' % map(str, vols))
		choices = []
		for vol in vols:
			basename = os.path.basename( vol.source )
			if '.' in basename:
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
		# recreate driver-type button
		items = [self[3].options[2].id(), self[3].options[3].id()]
		btn = self._create_type_select_button(object.options, items)
		self[3].options[1] = btn

		if drive_type == 'disk':
			self[ 2 ].hint = None
		elif drive_type == 'cdrom':
			if self.image_syntax._choices:
				msg = _( "If the required ISO image is not found it might be added by copying the file into the storage pool, e.g. to /var/lib/libvirt/images/ which is the directory of the storage pool <i>local directory</i>. After that go to the previous page an return to this one. The image should now be listed." )
			else:
				msg = _( "The list of available images is empty! To add an ISO image the file needs to be copied into the storage pool, e.g. to /var/lib/libvirt/images/ which is the directory of the storage pool <i>local directory</i>. After that go to the previous page an return to this one. The image should now be listed." )
			self[ 2 ].hint = msg
			self[ 2 ].description = ''
		else:
			raise Exception('Invalid drive-type "%s"' % drive_type)

		return self.type_selected(object)

	def type_selected(self, object):
		"""Update list of allowed driver types."""
		driver_type = object.options['driver-type']
		image_name = object.options.get('image-name', None)
		ud.debug(ud.ADMIN, ud.INFO, 'drive wizard: type=%s name=%s' % (driver_type, image_name))
		if image_name: # reuse existing image name
			base_name = image_name.split('.', 1)[0]
			if driver_type == 'RAW':
				image_name = '%s' % base_name
			else:
				image_name = '%s.%s' % (base_name, driver_type)
		else: # generate new image name
			if driver_type == 'RAW':
				suffix = ''
			else:
				suffix = '.%s' % driver_type
			image_name = self.uvmm.next_drive_name(self.node_uri, self.domain_name, suffix=suffix, temp_drives=self.blacklist)
		object.options['image-name'] = image_name
		return self[self.current]

	def _disk_type_text( self, disk_type ):
		"""Return translated Disk.TYPE as string."""
		if disk_type == 'disk':
			return _( 'hard drive' )
		elif disk_type == 'cdrom':
			return _( 'CDROM drive' )
		else:
			return _('unknown')

	def next( self, object ):
		"""Switch wizard to next page based on current state.
		                       —[cdrom]→                 [2]sp+img           ⬎
		[None]Start→[0]cdrom|hd                   —[old]⬏                     [4]summary
		                       —[hd]———→[1]old|new—[new]→[3]sp+name+type+size⬏
		"""
		if self.current == 0: # which drive type?
			# initialize pool and image selection
			self.pool_selected( object )
			self.type_selected(object)
			if object.options[ 'drive-type' ] == 'disk':
				self.current = 1
			elif object.options['drive-type'] == 'cdrom':
				self.current = 2
			else:
				raise Exception('Invalid drive-type "%s"' % object.options['drive-type'])
		elif self.current == 1: # new or existing disk image?
			if object.options[ 'existing-or-new-disk' ] == 'disk-new':
				self.current = 3
				btn = self._create_pool_select_button(object.options)
				self[ 2 ].options[ 0 ] = btn
				self[ 3 ].options[ 0 ] = btn
				items = [self[3].options[2].id(), self[3].options[3].id()]
				btn = self._create_type_select_button(object.options, items)
				self[3].options[1] = btn
			else:
				self.pool_selected(object)
				self.type_selected(object)
				self.current = 2
				if object.options[ 'drive-type' ] == 'disk':
					self[ self.current ].description = _( 'Each hard drive image is located within a so called storage pool, which might be a local directory, a device, an LVM volume or any type of share (e.g. mounted via iSCSI, NFS or CIFS). When selecting a storage pool the list of available images is updated.' )
				elif object.options['drive-type'] == 'cdrom':
					self[ self.current ].description = _( 'Each ISO image is located within a so called storage pool, which might be a local directory, a device, an LVM volume or any type of share (e.g. mounted via iSCSI, NFS or CIFS). When selecting a storage pool the list of available images is updated.' )
				else:
					raise Exception('Invalid drive-type "%s"' % object.options['drive-type'])
		elif self.current in ( 2, 3 ): # 2=select existing disk image, 3=create new
			drive_type = object.options['drive-type']
			drive_pool = object.options['drive-pool']
			pool_path = self._get_pool_path(drive_pool)
			if self.current == 2: # select existing disk image
				drive_image = object.options['drive-image']
				ud.debug(ud.ADMIN, ud.INFO, 'drive wizard: collect information about existing disk image: %s' % drive_image)
				vols = self.uvmm.storage_pool_volumes(self.node_uri, drive_pool, drive_type)
				for vol in vols:
					if os.path.basename(vol.source) == drive_image:
						ud.debug(ud.ADMIN, ud.INFO, 'drive wizard: set information about existing disk image: %s' % drive_image)
						object.options[ 'image-name' ] = drive_image
						if vol.driver_type:
							object.options['driver-type'] = vol.driver_type
						else:
							object.options['driver-type'] = 'RAW'
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

			image_name = object.options['image-name']
			drive_path = os.path.join(pool_path, image_name)
			ud.debug( ud.ADMIN, ud.INFO, 'Check if image %s is already used' % drive_path )

			if image_name in self.blacklist:
				is_used = self.domain_name
			elif drive_type == 'cdrom':
				is_used = None # read-only-volumes can be shared
			else:
				is_used = self.uvmm.is_image_used( self.node_uri, drive_path )

			if is_used in ( object.options.get( 'domain', '' ), object.options.get( 'name', '' ) ):
				return umcd.WizardResult( False, _( 'The selected image is already used by this virtual instance and therefor can not be used.' ) )

			if self.current == 2: # select existing disk image (part 2)
				reuse_image = object.options.setdefault('_reuse_image', [])
				if is_used and drive_path not in reuse_image:
					reuse_image.append(drive_path)
					msg = _('The selected image is already used by the virtual instance %(domain)s. It should be considered to choose another image. Continuing might cause problems.')
					return umcd.WizardResult(False, msg % {'domain': is_used})
			elif self.current == 3: # create new disk image (part 2)
				volumes = self.uvmm.storage_pool_volumes(self.node_uri, drive_pool)
				for volume in volumes:
					if volume.source == drive_path:
						if is_used:
							msg = _('An image with this name already exists and is used by virtual instance %(domain)s. The name must be unique for a new image.')
						else:
							msg = _('An unused image with this name already exists. The name must be unique for a new image.')
						return umcd.WizardResult(False, msg % {'domain': is_used})

			self.current = 4
			self[ self.current ].options = []
			conf = umcd.List()
			conf.add_row( [ umcd.HTML( '<i>%s</i>' % _( 'Drive type' ) ), self._disk_type_text(drive_type) ] )
			conf.add_row( [ umcd.HTML( '<i>%s</i>' % _( 'Storage pool' ) ), _( 'path: %(path)s' ) % { 'path' : pool_path } ] )
			conf.add_row( [ umcd.HTML( '<i>%s</i>' % _( 'Image filename' ) ), object.options[ 'image-name' ] ] )
			conf.add_row([umcd.HTML('<i>%s</i>' % _('Image format')), object.options['driver-type']])
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
			if object.options['drive-type'] == 'disk' and object.options['existing-or-new-disk'] == 'disk-new':
				self.current = 3
			else:
				self.current = 2
		else:
			return umcd.IWizard.prev( self, object )

		return umcd.WizardResult()

	def _get_pool_path( self, pool_name ):
		"""Return local path of pool."""
		try:
			return self.storage_pools[pool_name].path
		except KeyError:
			return ''

	def _available_space( self, pool_name ):
		"""Return available space of pool."""
		try:
			return self.storage_pools[pool_name].available
		except KeyError:
			return -1

	def _is_file_pool(self, pool_name):
		"""Return if pool conatains files."""
		try:
			return self.storage_pools[pool_name].type in ('dir', 'netfs')
		except KeyError:
			return False

	def finish( self, object ):
		# collect information about the drive
		drive_type = object.options['drive-type']
		drive_pool = object.options['drive-pool']
		image_name = object.options['image-name']
		image_size = object.options['image-size']
		driver_type = object.options['driver-type'].lower()

		disk = uvmmn.Disk()
		if drive_type == 'disk':
			disk.device = uvmmn.Disk.DEVICE_DISK
		elif drive_type == 'cdrom':
			disk.device = uvmmn.Disk.DEVICE_CDROM
			driver_type = 'raw' # ISOs need driver/@type='raw'
		else:
			raise Exception('Invalid drive-type "%s"' % drive_type)

		is_file_pool = self._is_file_pool(drive_pool)
		if is_file_pool:
			disk.type = uvmmn.Disk.TYPE_FILE
		else:
			disk.type = uvmmn.Disk.TYPE_BLOCK

		if self.node_uri.startswith('qemu'):
			disk.driver = 'qemu'
			disk.driver_type = driver_type.lower()
		elif self.node_uri.startswith('xen4FIXME'): # FIXME
			if is_file_pool:
				disk.driver = 'tap2'
				if driver_type == 'raw':
					disk.driver_type = 'aio'
				else: # qcow vhd
					disk.driver_type = driver_type
			else:
				disk.driver = 'block'
		elif self.node_uri.startswith('xen3FIXME'): # FIXME
			if is_file_pool:
				disk.driver = 'tap'
				if driver_type == 'raw':
					disk.driver_type = 'aio'
				else: # qcow qcow2 vmdk vhd
					disk.driver_type = driver_type
			else:
				disk.driver = 'block'
		elif self.node_uri.startswith('xen'):
			if is_file_pool:
				disk.driver = 'file'
				disk.driver_type = None # only raw support
			else:
				disk.driver = 'block'
		else:
			raise Exception('Unknown virt-tech "%s"' % self.node_uri)

		disk.size = MemorySize.str2num(image_size, unit='MB')
		disk.source = os.path.join(self._get_pool_path(drive_pool), image_name)

		self._result = disk
		return umcd.WizardResult()

	@property
	def storage_pools(self):
		"""Get storage-pools of node indexed by name."""
		# FIXME: same as InstanceWizard.storage_pools
		try:
			return self._storage_pools
		except AttributeError:
			storage_pools = self.uvmm.storage_pools(self.node_uri)
			self._storage_pools = dict([(p.name, p) for p in storage_pools])
			return self._storage_pools

class InstanceWizard( umcd.IWizard ):
	def __init__( self, command ):
		umcd.IWizard.__init__( self, command )
		self.title = _( 'Create new virtual instance' )
		self.udm = udm.Client()
		self.uvmm = uvmmd.Client( auto_connect = False )
		self.node_info = None
		self.profile_syntax = DynamicSelect( _( 'Profiles' ) )
		self.drive_wizard = DriveWizard( command )
		self.drive_wizard_active = False
		self.actions[ 'new-drive' ] = self.new_drive
		self.actions[ 'pool-selected' ] = self.drive_wizard.pool_selected # FIXME: KeyError 'drive-type'
		self.actions['type-selected'] = self.drive_wizard.type_selected
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

	def action( self, object, data ):
		self.node_uri, self.node_info = data
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
			try:
				profiles = [ item[ 'name' ] for item in self.udm.get_profiles(tech) if item[ 'arch' ] in self.archs ]
			except udm.LDAP_ConnectionError:
				umcd.IWizard.next( self, object )
				self.profile_syntax.update_choices( [] )
				return umcd.WizardResult( False, _( 'No profiles could be found! These are required to create new virtual instances. Ensure that the LDAP server can be reached.' ) )
			profiles.sort()
			self.profile_syntax.update_choices( profiles )
		if self.current == 0:
			try:
				self.profile = self.udm.get_profile( object.options[ 'instance-profile' ], tech )
			except udm.LDAP_ConnectionError:
				del object.options[ 'instance-profile' ]
				umcd.IWizard.next( self, object )
				# reset current page to this one
				self.current = 0
				return umcd.WizardResult( False, _( 'The selected profile could not be read! Without the information the new virtual instance can not be created. Ensure that the LDAP server can be reached.' ) )

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
			MAX_NAME_LENGTH = 25
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
			for pool in self.drive_wizard.storage_pools.values():
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
			domain_info = uvmmp.Data_Domain()
			domain_info.name = object.options[ 'name' ]
			domain_info.arch = object.options[ 'arch' ]
			domain_info.domain_type, domain_info.os_type = object.options['type'].split('-')
			# check configuration for para-virtualized machines
			if domain_info.os_type == 'xen':
				if self.profile[ 'advkernelconf' ] != 'TRUE': # use pyGrub
					domain_info.bootloader = '/usr/bin/pygrub'
					domain_info.bootloader_args = '-q' # Bug #19249: PyGrub timeout
				else:
					domain_info.kernel = object.options['kernel']
					domain_info.cmdline = object.options['cmdline']
					domain_info.initrd = object.options['initrd']
			# memory
			domain_info.maxMem = MemorySize.str2num(object.options['memory'], unit='MB')
			# CPUs
			domain_info.vcpus = object.options['cpus']
			# boot devices
			if object.options[ 'bootdev' ] and object.options[ 'bootdev' ][ 0 ]:
				ud.debug( ud.ADMIN, ud.INFO, 'device wizard: boot drives: %s' % str( object.options[ 'bootdev' ] ) )
				domain_info.boot = object.options['bootdev']
			# VNC
			if object.options[ 'vnc' ]:
				gfx = uvmmn.Graphic()
				gfx.listen = '0.0.0.0'
				gfx.keymap = object.options[ 'kblayout' ]
				domain_info.graphics = [gfx,]
			# drives
			domain_info.disks = self.drives
			self.uvmm._verify_device_files(domain_info)
			# on PV machines we should move the CDROM drive to first position
			if domain_info.os_type == 'xen':
				non_disks, disks = [], []
				for dev in domain_info.disks:
					if dev.device == uvmmn.Disk.DEVICE_DISK:
						disks.append(dev)
					else:
						non_disks.append(dev)
				domain_info.disks = non_disks + disks
			# network interface
			if object.options[ 'interface' ]:
				iface = uvmmn.Interface()
				iface.source = object.options[ 'interface' ]
				domain_info.interfaces = [iface,]
			self._result = domain_info

		return umcd.WizardResult()

	def new_drive( self, object, cancel = True ):
		# all next, prev and finished events must be redirected to the drive wizard
		name = object.options['name']
		self.drive_wizard_active = True
		self.drive_wizard_cancel = cancel
		self.drive_wizard.replace_title(_('Add drive to <i>%(name)s</i>') % {'name': name})
		self.drive_wizard.domain_name = name
		self.drive_wizard.blacklist = [os.path.basename(drive.source) for drive in self.drives]
		ud.debug(ud.ADMIN, ud.INFO, 'NEW DRIVE: bl=%s' % self.drive_wizard.blacklist)
		return self.drive_wizard.action( object, ( self.node_uri, self.node_info ) )

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
