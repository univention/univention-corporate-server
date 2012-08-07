# -*- coding: utf-8 -*-
#
# UCS Virtual Machine Manager
#  module: wizards for devices and virtual instances
#
# Copyright 2010-2012 Univention GmbH
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
import univention.management.console.tools as umct
import univention.management.console.protocol as umcp

import univention.debug as ud
import univention.config_registry as ucr

import univention.uvmm.node as uvmmn
import univention.uvmm.protocol as uvmmp

from types import *
from tools import *
import udm
import uvmmd
from xml.sax.saxutils import escape as xml_escape

_ = umc.Translation('univention.management.console.handlers.uvmm').translate

class DriveWizard( umcd.IWizard ):
	PAGE_INIT, PAGE_HD, PAGE_OLD, PAGE_NEW, PAGE_MANUAL, PAGE_SUMMARY = range(6)
	"""
	[0=INIT]:   <HD→1rw|CD→1ro|Floppy→1ro>
	[1rw=HD]:   <New→3|Old→2|Local→4        >
	[1ro=HD]:   <      Old→2|Local→4|Empty→5>
	[2=OLD]:    Pool,Image,→5
	[3=NEW]:    Pool,Format,Name,Size,→5
	[4=MANUAL]: Name,→5
	[5=SUMMARY]:
	"""

	def __init__(self, command, change=False): #, show_paravirtual = False
		umcd.IWizard.__init__( self, command )
		if change:
			self.title = _('Change media')
		else:
			self.title = _('Add drive')
		self.change = change
		self.pool_syntax = DynamicSelect( _( 'Storage pool' ) )
		self.image_syntax = DynamicSelect( _( 'Drive image' ) )
		self.driver_syntax = DynamicSelect( _( 'Image format' ) )
		self.drive_type_select = DriveTypeSelect()
		self.disk_select = DiskSelect()
		self.actions[ 'pool-selected' ] = self.pool_selected
		self.actions['type-selected'] = self.type_selected
		self.uvmm = uvmmd.Client( auto_connect = False )
		self.domain_name = None
		self.domain_virttech = VirtTech()
		self.node_uri = None
		self.node_info = None
		self.reset()

		# PAGE_INIT=0: Select HD or ROM
		page = umcd.Page( self.title, _( 'What type of drive should be created?' ) )
		page.options.append( umcd.make( ( 'drive-type', self.drive_type_select ) ) )
		self.append( page )

		# PAGE_HD=1: Select (new or) existing image or block device
		if change:
			page = umcd.Page(self.title, _('Choose between using an existing image or using a local device.'))
		else:
			page = umcd.Page(self.title, _('For the drive a new image can be created or an existing one can be chosen. An existing image should only be used by one virtual instance at a time.'))
		page.options.append( umcd.make( ( 'existing-or-new-disk', self.disk_select ) ) )
		self.append( page )

		# PAGE_OLD=2: Select existing image
		page = umcd.Page( self.title )
		page.options.append( umcd.Text( '' ) ) # will be replaced with pool selection button
		page.options.append( umcd.make( ( 'vol-name-old', self.image_syntax ) ) )
		self.append( page )

		# PAGE_NEW=3: [Only new HD] Select name and size
		page = umcd.Page( self.title, _( 'Each hard drive image is located within a so called storage pool, which might be a local directory, a device, an LVM volume or any type of share (e.g. mounted via iSCSI, NFS or CIFS). The newly create image will have the specified name and size provided by the following settings. Currently these was been set to default images. It has to be ensured that there is enough space left in the defined storage pool.' ) )
		page.options.append( umcd.Text( '' ) ) # will be replaced with pool selection button
		page.options.append(umcd.Text('')) # will be replaced with driver type selection button
		page.options.append( umcd.make( ( 'vol-name-new', umc.String( _( 'Filename' ) ) ) ) )
		page.options.append( umcd.make( ( 'image-size', umc.String( _( 'Size (default unit MB)' ), regex = MemorySize.SIZE_REGEX ) ) ) )
		self.append( page )

		# PAGE_MANUAL=4: Enter block device
		page = umcd.Page( self.title, _( 'To bind the drive to a local device the filename of the associated block device must be specified.' ) )
		page.options.append( umcd.make( ( 'vol-name-dev', umc.String( _( 'Device filename' ) ) ) ) )
		self.append( page )

		# PAGE_SUMMARY=5: Show summary
		if change:
			page = umcd.Page(self.title, _('The following drive will be updated:'))
		else:
			page = umcd.Page(self.title, _('The following drive will be created:'))
		self.append( page )

		# self.show_paravirtual( show_paravirtual )

	def set_node(self, uri, info):
		"""Associate this wizard with node."""
		self.node_uri = uri
		self.node_info = info

	def _create_pool_select_button(self, options):
		choices = []
		ud.debug(ud.ADMIN, ud.INFO, 'UVMM.DW.ps(pool-name=%(pool-name)s)' % ddict(options))
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
		ud.debug(ud.ADMIN, ud.INFO, 'UVMM.DW.ps pool-name=%(pool-name)s' % ddict(options))
		return umcd.SimpleSelectButton(_('Pool'), option='pool-name', choices=choices, actions=[action], attributes={'width': '300px'}, default=options.get('pool-name'))

	def _create_type_select_button(self, options, items):
		"""Create list to select driver-type allowed by current driver-pool."""
		# FIXME: items are ignored for some unknown reason
		opts = copy.deepcopy(options)
		opts['action'] = 'type-selected'
		action = umcd.Action(umcp.SimpleCommand(self.command, options=opts), items)
		choices = (
				('RAW', _('Simple format (raw)')),
				)
		try:
			pool_name = options['pool-name']
			ud.debug(ud.ADMIN, ud.ALL, 'UVMM.DW.ts(pool-name=%s)' % pool_name)
			if self._is_file_pool(pool_name):
				if self.node_uri.startswith('qemu'):
					choices = (
							#('qcow', _('Extended format (qcow)')),
							('qcow2', _('Extended format (qcow2)')),
							#('vmdk', _('VMWare Disk')),
							('raw', _('Simple format (raw)')),
							)
				elif self.node_uri.startswith('xen'):
					choices = (
							('raw', _('Simple format (raw)')),
							#('qcow2', _('Qemu copy-on-write 2')),
							#('vhd', _('Virtual Hard Disk')),
							#('vmdk', _('VMWare Disk')),
							)
		except LookupError, e:
			ud.debug(ud.ADMIN, ud.ALL, 'UVMM.DW.ts exception=%s' % e)
		try: # validate current setting
			default = options['driver-type']
			ud.debug(ud.ADMIN, ud.ALL, 'UVMM.DW.ts default=%s' % default)
			dict(choices)[default]
		except LookupError, e:
			ud.debug(ud.ADMIN, ud.ALL, 'UVMM.DW.ts default exception=%s' % e)
			default = choices[0][0]
		options['driver-type'] = default
		return umcd.SimpleSelectButton(_('Image format'), option='driver-type', choices=choices, actions=[action], attributes={'width': '300px'}, default=default)

	def reset( self ):
		self.replace_title( self.title )
		self.prev_first_page = False
		self.domain_name = None
		self.domain_virttech( None )
		self.blacklist = []
		try: # delete cached list of storage pools
			del self._storage_pools
		except AttributeError, e:
			pass
		umcd.IWizard.reset( self )

	def setup( self, object, prev = None, next = None, finish = None, cancel = None ):
		"""Setup page self.current and render it to UMC primitives."""
		ud.debug(ud.ADMIN, ud.INFO, 'UVMM.DW.setup(current=%s, prev_first_page=%s)' % (str(self.current), self.prev_first_page))
		page = self[self.current] # this page we're going to present

		if self.current == DriveWizard.PAGE_INIT and self.prev_first_page:
			prev = True
		if self.change and self.current <= DriveWizard.PAGE_HD:
			prev = False

		if self.current == DriveWizard.PAGE_HD:
			drive_type = object.options['drive-type']
			if drive_type == 'disk':
				self.disk_select.set_choices()
			elif drive_type in ('cdrom', 'floppy'):
				self.disk_select.set_choices(with_new=False)
			else:
				raise ValueError('Invalid drive-type "%(drive-type)s"' % object.options)

		if self.current == DriveWizard.PAGE_OLD:
			drive_type = object.options['drive-type']
			self.pool_selected(object)
			self.type_selected(object)
			if drive_type == 'disk':
				page.description = _('Each hard drive image is located within a so called storage pool, which might be a local directory, a device, an LVM volume or any type of share (e.g. mounted via iSCSI, NFS or CIFS). When selecting a storage pool the list of available images is updated.')
			elif drive_type in ('cdrom', 'floppy'):
				page.description = _('Each image is located within a so called storage pool, which might be a local directory, a device, an LVM volume or any type of share (e.g. mounted via iSCSI, NFS or CIFS). When selecting a storage pool the list of available images is updated.')
			else:
				raise ValueError('Invalid drive-type "%s"' % drive_type)

		if self.current == DriveWizard.PAGE_NEW:
			self.pool_selected(object)
			self.type_selected(object)

		if self.current == DriveWizard.PAGE_SUMMARY:
			r = self.request_data(object)

			page.options = options = []
			conf = umcd.List()
			conf.add_row([umcd.HTML('<i>%s</i>' % _('Drive type')), self._disk_type_text(r.drive_type)])
			if r.pool_path:
				conf.add_row([umcd.HTML('<i>%s</i>' % _('Storage pool')), _('path: %(path)s') % {'path': r.pool_path}])
				if len(r.vol_path) > 60:
					conf.add_row([umcd.HTML('<i>%s</i>' % _('Image filename')), umcd.HTML('<p title="%s">%s...</p>' %(xml_escape(r.vol_path), xml_escape(r.vol_path[0:60])))])
				else:
					conf.add_row([umcd.HTML('<i>%s</i>' % _('Image filename')), r.vol_path])
				conf.add_row([umcd.HTML('<i>%s</i>' % _('Image format')), r.driver_type])
				conf.add_row([umcd.HTML('<i>%s</i>' % _('Image size')), r.vol_size])
			elif r.vol_path:
				conf.add_row([umcd.HTML('<i>%s</i>' % _('Device filename')), r.vol_path])
			else:
				conf.add_row([umcd.HTML('<i>%s</i>' % _('Device filename')), '-'])
			options.append(conf)

		return umcd.IWizard.setup( self, object, prev = prev, next = next, finish = finish, cancel = cancel )

	def set_defaults( self, object ):
		# Do not reset these values to reduce click count on mass install sessions
		#for opt in ( 'existing-or-new-disk', 'drive-type' ):
		#	if opt in object.options:
		#		del object.options[ opt ]
		#object.options[ 'pool-name' ] = 'default'
		if object.options.get('diskspace'):
			object.options[ 'image-size' ] = object.options['diskspace'] # use the diskspace value from profile
		else:
			object.options[ 'image-size' ] = '12GB' # default
		object.options['vol-name-old'] = None
		object.options['vol-name-new'] = None
		object.options['vol-name-dev'] = None

	def action( self, object ):
		ud.debug(ud.ADMIN, ud.INFO, 'UVMM.DW.action(current: %s)' % str( self.current ) )
		if self.current is None:
			# read pool
			ud.debug( ud.ADMIN, ud.INFO, 'UVMM.DW.action: node storage pools: %s' % self.node_uri)
			self.set_defaults( object )
		return umcd.IWizard.action( self, object )

	def pool_selected( self, object ):
		"""Update list of known images in pool."""
		ud.debug( ud.ADMIN, ud.INFO, 'UVMM.DW.ps(node_uri=%s)' % self.node_uri)
		pool_name = object.options.get('pool-name')
		if not pool_name:
			pool_name = object.options['pool-name'] = 'default'
		drive_type = object.options['drive-type']
		try:
			if drive_type == 'cdrom':
				vols = self.uvmm.storage_pool_volumes(self.node_uri, pool_name, 'cdrom')
			else:
				vols = self.uvmm.storage_pool_volumes(self.node_uri, pool_name, 'disk' )
		except uvmmd.UvmmError, e:
			vols = ()
		ud.debug(ud.ADMIN, ud.INFO, 'UVMM.DW.ps: volumes=%s' % map(str, vols))
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
		self[DriveWizard.PAGE_OLD].options[0] = btn
		self[DriveWizard.PAGE_NEW].options[0] = btn
		# recreate driver-type button
		items = [self[DriveWizard.PAGE_NEW].options[2].id(), self[DriveWizard.PAGE_NEW].options[3].id()]
		btn = self._create_type_select_button(object.options, items)
		self[DriveWizard.PAGE_NEW].options[1] = btn

		if drive_type == 'disk':
			self[DriveWizard.PAGE_OLD].hint = None
		elif drive_type in ( 'cdrom', 'floppy' ):
			if self.image_syntax._choices:
				msg = _( "If the required image is not found it might be added by copying the file into the storage pool, e.g. to /var/lib/libvirt/images/ which is the directory of the storage pool <i>local directory</i>. After that go to the previous page and return to this one. The image should now be listed." )
			else:
				msg = _( "The list of available images is empty! To add an image the file needs to be copied into the storage pool, e.g. to /var/lib/libvirt/images/ which is the directory of the storage pool <i>local directory</i>. After that go to the previous page and return to this one. The image should now be listed." )
			self[DriveWizard.PAGE_OLD].hint = msg
			self[DriveWizard.PAGE_OLD].description = ''
		else:
			raise ValueError('Invalid drive-type "%s"' % drive_type)

		return self.type_selected(object)

	def type_selected(self, object):
		"""Update list of allowed driver types."""
		driver_type = object.options['driver-type']
		vol_name = object.options.get('vol-name-new', None)
		ud.debug(ud.ADMIN, ud.INFO, 'UVMM.DW.ts(type=%s name=%s)' % (driver_type, vol_name))
		if vol_name: # reuse existing image name
			base_name = vol_name.split('.', 1)[0]
			if driver_type == 'RAW':
				vol_name = '%s' % base_name
			else:
				vol_name = '%s.%s' % (base_name, driver_type)
		else: # generate new image name
			if driver_type == 'RAW':
				suffix = ''
			else:
				suffix = '.%s' % driver_type
			try:
				vol_name = self.uvmm.next_drive_name(self.node_uri, self.domain_name, suffix=suffix, temp_drives=self.blacklist)
			except uvmmd.UvmmError, e:
				vol_name = 'ERROR'
		object.options['vol-name-new'] = vol_name
		return self[self.current]

	def _disk_type_text( self, disk_type ):
		"""Return translated Disk.TYPE as string."""
		if disk_type == 'disk':
			return _( 'hard drive' )
		elif disk_type == 'cdrom':
			return _( 'CDROM drive' )
		elif disk_type == 'floppy':
			return _( 'floppy drive' )
		else:
			return _('unknown')

	def request_data(self, request):
		"""Read values from request and normalize to local variables."""
		class d:
			mode = request.options['existing-or-new-disk']
			drive_type = request.options['drive-type']
			pool_name = None
			pool_path = None
			vol_name = None
			vol_path = None
			vol_size = None
			driver_type = 'RAW'
			if mode == 'disk-new':
				assert drive_type == 'disk'
				pool_name = request.options['pool-name']
				pool_path = self._get_pool_path(pool_name)
				vol_name = request.options['vol-name-new']
				vol_path = os.path.join(pool_path, vol_name)
				vol_size = request.options['image-size']
				driver_type = request.options['driver-type']
			elif mode == 'disk-exists':
				pool_name = request.options['pool-name']
				pool_path = self._get_pool_path(pool_name)
				vol_name = request.options['vol-name-old']
				vol_path = os.path.join(pool_path, vol_name)
				vol_size = request.options['image-size']
				driver_type = request.options['driver-type']
			elif mode == 'disk-block':
				vol_path = request.options['vol-name-dev']
			elif mode == 'disk-empty':
				pass
			else:
				raise ValueError('Invalid selection "%s"' % mode)
		return d

	def next( self, object ):
		"""Validate current page, pre-fill state, switch to next page."""
		ud.debug(ud.ADMIN, ud.INFO, 'UVMM.DW.next(pool-name=%(pool-name)s drive-type=%(drive-type)s vol-name-old=%(vol-name-old)s -new=%(vol-name-new)s -dev=%(vol-name-dev)s)' % ddict(object.options))
		# by default no paravirtual drive:
		object.options.setdefault('drive-paravirtual', False)
		object.options.setdefault('cdrom-paravirtual', False)

		if self.current == DriveWizard.PAGE_INIT: # which drive type?
			# initialize pool and image selection
			self.current = DriveWizard.PAGE_HD

		elif self.current == DriveWizard.PAGE_HD: # new or existing disk image?
			mode = object.options['existing-or-new-disk']
			if mode == 'disk-new':
				self.current = DriveWizard.PAGE_NEW
			elif mode == 'disk-exists':
				self.current = DriveWizard.PAGE_OLD
			elif mode == 'disk-block':
				self.current = DriveWizard.PAGE_MANUAL
				drive_type = object.options['drive-type']
				if drive_type == 'disk':
					object.options['vol-name-dev'] = '/dev/'
				elif drive_type == 'cdrom':
					object.options['vol-name-dev'] = '/dev/cdrom'
				elif drive_type == 'floppy':
					object.options['vol-name-dev'] = '/dev/fd0'
			elif mode == 'disk-empty':
				self.current = DriveWizard.PAGE_SUMMARY
			else:
				raise ValueError('Invalid selection "%s"' % mode)

		elif self.current == DriveWizard.PAGE_OLD: # select existing disk image
			drive_type = object.options['drive-type']
			pool_name = object.options['pool-name']
			pool_path = self._get_pool_path(pool_name)
			vol_name = object.options['vol-name-old']
			try:
				if drive_type == 'cdrom':
					vols = self.uvmm.storage_pool_volumes(self.node_uri, pool_name, 'cdrom')
				else:
					vols = self.uvmm.storage_pool_volumes(self.node_uri, pool_name, 'disk')
			except uvmmd.UvmmError, e:
				vols = ()

			for vol in vols:
				if os.path.basename(vol.source) == vol_name:
					break
			else:
				ud.debug(ud.ADMIN, ud.INFO, 'UVMM.DW.next: Image not found: pool=%s type=%s image=%s vols=%s' % (pool_name, drive_type, vol_name, map(str, vols)))
				return umcd.WizardResult(False, _('Image not found')) # FIXME
			vol_path = vol.source

			# disk images from a pool MUST NOT be shared
			if drive_type not in ('cdrom', 'floppy') and pool_path:
				if vol_name in self.blacklist:
					is_used = self.domain_name
				else:
					try:
						is_used = self.uvmm.is_image_used(self.node_uri, vol_path)
					except uvmmd.UvmmError, e:
						is_used = self.domain_name # FIXME: need proper error handling
				if is_used in (object.options.get('domain', ''), object.options.get('name', '')):
					msg = _('The selected image is already used by this virtual instance and therefore can not be used.')
					return umcd.WizardResult(False, msg)
				reuse_image = object.options.setdefault('_reuse_image', [])
				if is_used and vol_path not in reuse_image:
					reuse_image.append(vol_path)
					msg = _('The selected image is already used by the virtual instance %(domain)s. It should be considered to choose another image. Continuing might cause problems.')
					return umcd.WizardResult(False, msg % {'domain': is_used})

			object.options['driver-type'] = vol.driver_type or 'RAW'
			object.options['image-size'] = MemorySize.num2str(vol.size)
			object.options['vol-path'] = vol_path
			self.current = DriveWizard.PAGE_SUMMARY

		elif self.current == DriveWizard.PAGE_NEW: # create new disk image
			pool_name = object.options['pool-name']
			pool_path = self._get_pool_path(pool_name)
			vol_name = object.options['vol-name-new']
			vol_path = os.path.join(pool_path, vol_name)
			# TODO: Bug #19281
			# vol_bytes = MemorySize.str2num(object.options['image-size'], unit='MB')
			# pool_bytes = self._available_space(object.options['pool-name'])
			# if (pool_bytes - vol_bytes) < 0:
			# 	object.options['image-size'] = MemorySize.num2str(int(pool_bytes * 0.9))
			# 	return umcd.WizardResult(False, _('There is not enough space left in the pool. The size is set to the maximum available space left.'))

			# disk images from a pool MUST be new and NOT be shared
			if vol_name in self.blacklist:
				is_used = self.domain_name
			else:
				try:
					is_used = self.uvmm.is_image_used(self.node_uri, vol_path)
				except uvmmd.UvmmError, e:
					is_used = self.domain_name # FIXME: need proper error handling
			if is_used in (object.options.get('domain', ''), object.options.get('name', '')):
				msg = _('The selected image is already used by this virtual instance and therefor can not be used.')
				return umcd.WizardResult(False, msg)
			try:
				volumes = self.uvmm.storage_pool_volumes(self.node_uri, pool_name)
			except uvmmd.UvmmError, e:
				volumes = ()
			for volume in volumes:
				if volume.source == vol_path:
					if is_used:
						msg = _('An image with this name already exists and is used by virtual instance %(domain)s. The name must be unique for a new image.')
					else:
						msg = _('An unused image with this name already exists. The name must be unique for a new image.')
					return umcd.WizardResult(False, msg % {'domain': is_used})

			object.options['image-size'] = MemorySize.str2str(object.options['image-size'], unit='MB')
			object.options['vol-path'] = vol_path
			self.current = DriveWizard.PAGE_SUMMARY

		elif self.current == DriveWizard.PAGE_MANUAL: # local-device
			vol_name = object.options['vol-name-dev']
			if vol_name.startswith('/'):
				vol_path = vol_name
			else:
				vol_path = '/dev/' + vol_name
			object.options['pool-name'] = None
			object.options['vol-path'] = vol_path
			object.options['driver-type'] = 'RAW'
			self.current = DriveWizard.PAGE_SUMMARY

		else:
			if self.current is None:
				self.current = 0
			else:
				self.current += 1

		return umcd.WizardResult()

	def prev( self, object ):
		if self.current in (DriveWizard.PAGE_OLD, DriveWizard.PAGE_NEW, DriveWizard.PAGE_MANUAL):
			self.current = DriveWizard.PAGE_HD
		elif self.current == DriveWizard.PAGE_SUMMARY:
			if object.options['drive-type'] == 'disk' and object.options['existing-or-new-disk'] == 'disk-new':
				self.current = DriveWizard.PAGE_NEW
			elif object.options['existing-or-new-disk'] == 'disk-exists':
				self.current = DriveWizard.PAGE_OLD
			elif object.options['existing-or-new-disk'] == 'disk-empty':
				self.current = DriveWizard.PAGE_INIT
			else:
				self.current = DriveWizard.PAGE_MANUAL
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
			return self.storage_pools[pool_name].type in ('dir', 'fs', 'netfs')
		except KeyError:
			return False

	def finish( self, object ):
		ud.debug(ud.ADMIN, ud.INFO, 'UVMM.DW.finish(%r)' % ddict(object.options))
		# collect information about the drive
		r = self.request_data(object)
		r.driver_type = r.driver_type.lower()

		disk = uvmmp.Disk()
		disk.source = r.vol_path

		is_file_pool = self._is_file_pool(r.pool_name)
		if is_file_pool:
			disk.type = uvmmp.Disk.TYPE_FILE
		else:
			disk.type = uvmmp.Disk.TYPE_BLOCK
			disk.target_bus = 'ide'

		if r.drive_type == 'disk':
			disk.device = uvmmp.Disk.DEVICE_DISK
			driver_pv = object.options[ 'drive-paravirtual' ]
		elif r.drive_type == 'cdrom':
			disk.device = uvmmp.Disk.DEVICE_CDROM
			r.driver_type = 'raw' # ISOs need driver/@type='raw'
			driver_pv = object.options[ 'cdrom-paravirtual' ]
		elif r.drive_type == 'floppy':
			disk.device = uvmmp.Disk.DEVICE_FLOPPY
			disk.target_bus = 'fdc'
			driver_pv = None
		else:
			raise ValueError('Invalid drive-type "%s"' % r.drive_type)

		if self.node_uri.startswith('qemu'):
			disk.driver = 'qemu'
			disk.driver_type = r.driver_type
			if driver_pv and r.drive_type != 'floppy' and disk.type != uvmmn.Disk.TYPE_BLOCK:
				disk.target_bus = 'virtio'
		elif self.node_uri.startswith('xen'):
			if driver_pv and r.drive_type != 'floppy' and disk.type != uvmmn.Disk.TYPE_BLOCK:
				disk.target_bus = 'xen'
			elif self.domain_virttech.pv() and not driver_pv:
				# explicitly set ide bus
				disk.target_bus = 'ide'
			# block devices of para-virtual xen instances must use bus xen
			if self.domain_virttech.pv() and disk.type == uvmmn.Disk.TYPE_BLOCK:
				disk.target_bus = 'xen'
			# Since UCS 2.4-2 Xen 3.4.3 contains the blktab2 driver
			# from Xen 4.0.1
			if is_file_pool:
				configRegistry = ucr.ConfigRegistry()
				configRegistry.load()
				# Use tapdisk2 by default, but not for empty CDROM drives
				if r.vol_path is not None and configRegistry.is_true('uvmm/xen/images/tap2', True):
					disk.driver = 'tap2'
					if r.driver_type == 'raw':
						disk.driver_type = 'aio'
					else: # qcow vhd
						disk.driver_type = r.driver_type
				else:
					disk.driver = 'file'
					disk.driver_type = None # only raw support
			else:
				disk.driver = 'phy'
		else:
			raise ValueError('Unknown virt-tech "%s"' % self.node_uri)

		if r.vol_size:
			disk.size = MemorySize.str2num(r.vol_size, unit='MB')

		self._result = disk
		return umcd.WizardResult()

	@property
	def storage_pools(self):
		"""Get storage-pools of node indexed by name."""
		# FIXME: same as InstanceWizard.storage_pools
		try:
			return self._storage_pools
		except AttributeError:
			try:
				storage_pools = self.uvmm.storage_pools(self.node_uri)
			except uvmmd.UvmmError, e:
				storage_pools = ()
			self._storage_pools = dict([(p.name, p) for p in storage_pools])
			return self._storage_pools

class InstanceWizard( umcd.IWizard ):
	PAGE_INIT, PAGE_BASIC, PAGE_SUMMARY = range(3)

	def __init__( self, command ):
		umcd.IWizard.__init__( self, command )
		self.title = _( 'Create new virtual instance' )
		self.udm = udm.Client()
		self.uvmm = uvmmd.Client( auto_connect = False )
		self.node_info = None
		self.profile_syntax = DynamicSelect( _( 'Profiles' ) )
		self.drive_wizard = DriveWizard(command)
		self.drive_wizard_active = False
		self.actions[ 'new-drive' ] = self.new_drive
		self.actions[ 'pool-selected' ] = self.drive_wizard.pool_selected # FIXME: KeyError 'drive-type'
		self.actions['type-selected'] = self.drive_wizard.type_selected
		self.drives = []

		# PAGE_INIT=0
		page = umcd.Page( self.title, _( 'By selecting a profile for the virtual instance most of the settings will be set to default values. In the following steps some of these values might be modified. After the creation of the virtual instance all parameters, extended settings und attached drives can be adjusted. It should be ensured that the profile is for the correct architecture as this option can not be changed afterwards.' ) )
		page.options.append( umcd.make( ( 'instance-profile', self.profile_syntax ) ) )
		self.append( page )

		# PAGE_BASIC=1
		page = umcd.Page( self.title, _( 'The following settings were read from the selected profile and can be modified now.' ) )
		page.options.append( umcd.make( ( 'name', umc.String( _( 'Name' ) ) ) ) )
		page.options.append( umcd.make( ( 'description', umc.String( _( 'Description' ), required = False ) ) ) )
		page.options.append( umcd.make( ( 'memory', umc.String( _( 'Memory (in MB)' ), regex = MemorySize.SIZE_REGEX ) ) ) )
		page.options.append( umcd.make( ( 'cpus', NumberSelect( _( 'CPUs' ) ) ) ) )
		page.options.append( umcd.make( ( 'vnc', umc.Boolean( _( 'Enable direct access' ) ) ) ) )
		self.append( page )

		# PAGE_SUMMARY=2
		page = umcd.Page( self.title, umcd.HTML( _( 'The virtual instance will be created with the settings shown below. The button <i>Add drive</i> can be used to attach another drive.' ) ) )
		page.options.append( umcd.HTML( '' ) )
		add_cmd = umcp.SimpleCommand(command, options={'action': 'new-drive'})
		add_act = umcd.Action(add_cmd)
		add_btn = umcd.LinkButton(_('Add drive'), 'uvmm/add', actions=(add_act,))
		add_btn.set_size(umct.SIZE_SMALL)
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
				self.replace_title(_('Create a virtual instance (profile: %(profile)s)') % {'profile': xml_escape(object.options['instance-profile'])})
			else:
				self.replace_title(_('Create a virtual instance <i>%(name)s</i>') % {'name': xml_escape(object.options['name'])})
		tech = self.node_uri[ : self.node_uri.find( ':' ) ]
		if self.current is None:

			tech_types = []
			for template in self.node_info.capabilities:
				template_tech = '%s-%s' % ( template.domain_type, template.os_type )
				if not template_tech in VirtTechSelect.MAPPING:
					continue
				if not template_tech in tech_types:
					tech_types.append( template_tech )
			
			if 'xen-xen' in tech_types and not 'xen-hvm' in tech_types:
				# Set tech to xen-xen because the CPU extensions is not available
				tech = 'xen-xen'

			try:
				profiles = [ item[ 'name' ] for item in self.udm.get_profiles(tech) if item[ 'arch' ] in self.archs or item[ 'arch' ] == 'automatic' ]
				ud.debug( ud.ADMIN, ud.INFO, 'PROFILE: profiles: %s' % profiles)
			except udm.LDAP_ConnectionError:
				umcd.IWizard.next( self, object )
				self.profile_syntax.update_choices( [] )
				return umcd.WizardResult( False, _( 'No profiles could be found! These are required to create new virtual instances. Ensure that the LDAP server can be reached.' ) )

			profiles.sort()
			self.profile_syntax.update_choices( profiles )

			if tech == 'xen-xen':
				# Only paravirtualization 
				umcd.IWizard.next( self, object )
				return umcd.WizardResult( False, _( 'The server does not have the virtualization extension (Intel VT or AMD-V). Only profiles using paravirtualization will work.' ) )
			elif len(tech_types) == 0:
				# KVM is installed and the CPU extension is missing
				umcd.IWizard.next( self, object )
				return umcd.WizardResult( False, _( 'The server does not have the virtualization extension (Intel VT or AMD-V). For virtualization with KVM this extension is required.' ) )
			elif len(profiles) == 0:
				# Hmm ...
				umcd.IWizard.next( self, object )
				return umcd.WizardResult( False, _( 'No profiles could be found! Please check your installation and run all join scripts, e.g. using univention-run-join-scripts.' ) )

		if self.current == InstanceWizard.PAGE_INIT:
			try:
				self.profile = self.udm.get_profile( object.options[ 'instance-profile' ], tech )
			except udm.LDAP_ConnectionError:
				del object.options[ 'instance-profile' ]
				umcd.IWizard.next( self, object )
				# reset current page to this one
				self.current = InstanceWizard.PAGE_INIT
				return umcd.WizardResult( False, _( 'The selected profile could not be read! Without the information the new virtual instance can not be created. Ensure that the LDAP server can be reached.' ) )

			ud.debug( ud.ADMIN, ud.INFO, 'drive wizard: next: profile: %s' % str( dict( self.profile ) ) )
			object.options[ 'name' ] = self.profile[ 'name_prefix' ]
			object.options[ 'os' ] = self.profile[ 'os' ]
			if self.profile[ 'arch' ] == 'automatic':
				if 'x86_64' in self.archs:
					object.options[ 'arch' ] = 'x86_64'
				else:
					object.options[ 'arch' ] = 'i686'
			else:
				object.options[ 'arch' ] = self.profile[ 'arch' ]
			object.options[ 'type' ] = self.profile[ 'virttech' ]
			object.options[ 'memory' ] = self.profile[ 'ram' ]
			object.options[ 'diskspace' ] = self.profile[ 'diskspace' ]
			object.options[ 'cpus' ] = self.profile[ 'cpus' ]
			object.options[ 'bootdev' ] = self.profile[ 'bootdev' ]
			object.options[ 'vnc' ] = self.profile[ 'vnc' ]
			object.options[ 'kblayout' ] = self.profile[ 'kblayout' ]
			object.options[ 'interface' ] = self.profile[ 'interface' ]
			object.options[ 'kernel' ] = self.profile[ 'kernel' ]
			object.options[ 'cmdline' ] = self.profile[ 'kernel_parameter' ]
			object.options[ 'initrd' ] = self.profile[ 'initramfs' ]
			object.options[ 'pvdisk' ] = self.profile[ 'pvdisk' ]
			object.options[ 'pvcdrom' ] = self.profile[ 'pvcdrom' ]
			object.options[ 'pvinterface' ] = self.profile[ 'pvinterface' ]
			object.options['rtc_offset'] = self.profile['rtcoffset']
		if self.current == InstanceWizard.PAGE_BASIC:
			MAX_NAME_LENGTH = 25
			if object.options[ 'name' ] == self.profile[ 'name_prefix' ]:
				return umcd.WizardResult( False, _( 'The name of the virtual instance should be modified' ) )
			if len( object.options[ 'name' ] ) > MAX_NAME_LENGTH:
				object.options[ 'name' ] = object.options[ 'name' ][ : MAX_NAME_LENGTH ]
				return umcd.WizardResult( False, _( 'The name of a virtual instance may not be longer than %(maxlength)d characters!' ) % { 'maxlength' : MAX_NAME_LENGTH } )
			try:
				if not self.uvmm.is_domain_name_unique( self.node_uri, object.options[ 'name' ] ):
					return umcd.WizardResult( False, _( 'The chosen name for the virtual instance is not unique. Please choose another name.' ) )
			except uvmmd.UvmmError, e:
				return umcd.WizardResult(False, _('The chosen name for the virtual instance could not be checked for uniqueness.'))
			mem_size = MemorySize.str2num( object.options[ 'memory' ], unit = 'MB' )
			four_mb = MemorySize.str2num( '4', unit = 'MB' )
			if mem_size < four_mb:
				object.options[ 'memory' ] = '4 MB'
				return umcd.WizardResult( False, _( 'A virtual instance must at least have 4 MB memory.' ) )
			elif mem_size > self.max_memory:
				object.options[ 'memory' ] = MemorySize.num2str( self.max_memory * 0.75 )
				return umcd.WizardResult( False, _( 'The physical server does not have that much memory. As a suggestion the amount of memory was set to 75% of the available memory.' ) )
			else:
				object.options[ 'memory' ] = MemorySize.num2str( mem_size )
			# activate drive wizard to add a first mandatory drive
			if not self.drives:
				self.drive_wizard.prev_first_page = True
				self.drive_wizard.drive_type_select.floppies = self.profile[ 'virttech' ].endswith( '-hvm' )
				# self.drive_wizard.show_paravirtual( self.profile[ 'virttech' ].endswith( '-hvm' ) )
				object.options[ 'drive-paravirtual' ] = object.options[ 'pvdisk' ] == '1'
				object.options[ 'cdrom-paravirtual' ] = object.options[ 'pvcdrom' ] == '1'
				self.new_drive( object )
		return umcd.IWizard.next( self, object )

	def prev( self, object ):
		if self.drive_wizard_active:
			if self.drive_wizard.current == InstanceWizard.PAGE_INIT:
				self.drive_wizard_active = False
				self.drive_wizard.reset()
			else:
				return self.drive_wizard.prev( object )

		if self.current == InstanceWizard.PAGE_SUMMARY:
			self.replace_title( _( 'Create a virtual instance (profile: %(profile)s)' ) % { 'profile' : object.options[ 'instance-profile' ] } )
		elif self.current == InstanceWizard.PAGE_BASIC:
			del object.options[ 'name' ]
			self.replace_title( _( 'Create a virtual instance' ) )

		return umcd.IWizard.prev( self, object )

	def _list_domain_settings( self, object ):
		'''add list with domain settings to page 2'''
		rows = []
		settings = umcd.List()
		for text, key in ( ( _( 'Name' ), 'name' ), ( _( 'Description' ), 'description' ), ( _( 'CPUs' ), 'cpus' ), ( _( 'Memory' ), 'memory' ) ):
			if object.options.get( key ):
				settings.add_row( [ umcd.HTML( '<i>%s</i>' % text ), object.options.get( key, '' ) ] )
			else:
				settings.add_row( [ umcd.HTML( '<i>%s</i>' % text ) ] )
		if object.options.get( 'vnc' ):
			value = _( 'activated' )
		else:
			value = _( 'deactivated' )
		settings.add_row( [ umcd.HTML( '<i>%s</i>' % _( 'Direct access' ) ), value ] )
		rows.append( [ settings ] )

		rows.append( [ umcd.HTML( '<b>%s</b><br>' % _( 'Attached drives' ) ), ] )

		html = '<ul class="umc_listing">'
		for dev in self.drives:
			values = {}
			if dev.device == uvmmp.Disk.DEVICE_DISK:
				values[ 'type' ] = _( 'hard drive' )
			elif dev.device == uvmmp.Disk.DEVICE_CDROM:
				values[ 'type' ] = _( 'CDROM drive' )
			elif dev.device == uvmmp.Disk.DEVICE_FLOPPY:
				values[ 'type' ] = _( 'floppy drive' )
			else:
				values[ 'type' ] = _( 'unknown' )

			if dev.source:
				dir = os.path.dirname(dev.source)
				for pool in self.drive_wizard.storage_pools.values():
					if pool.path == dir:
						values['size'] = MemorySize.num2str(dev.size)
						if len(os.path.basename(dev.source)) > 40:
							values['image'] = xml_escape("%s..." % os.path.basename(dev.source)[0:40])
						else:
							values['image'] = xml_escape(os.path.basename(dev.source))
						values['pool'] = xml_escape(pool.name)
						html += _('<li>%(type)s: %(size)s (image file %(image)s in pool %(pool)s)</li>') % values
						break
				else:
					values['device'] = dev.source
					html += _('<li>%(type)s: local device %(device)s</li>') % values
			else:
				html += _('<li>%(type)s: empty device</li>') % values
		html += '</ul>'
		rows.append( [ umcd.HTML( html ) ] )
		self[InstanceWizard.PAGE_SUMMARY].options[0] = umcd.List( content = rows )

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
			if domain_info.os_type in ( 'linux', 'xen' ):
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
			domain_info.vcpus = int(object.options['cpus'])
			# boot devices
			if object.options[ 'bootdev' ] and object.options[ 'bootdev' ][ 0 ]:
				ud.debug( ud.ADMIN, ud.INFO, 'device wizard: boot drives: %s' % str( object.options[ 'bootdev' ] ) )
				domain_info.boot = object.options['bootdev']
			# VNC
			if object.options[ 'vnc' ]:
				gfx = uvmmp.Graphic()
				gfx.listen = '0.0.0.0'
				gfx.keymap = object.options[ 'kblayout' ]
				domain_info.graphics = [gfx,]
			# annotations
			domain_info.annotations[ 'os' ] = object.options[ 'os' ]
			domain_info.annotations[ 'description' ] = object.options[ 'description' ]
			# RTC offset
			domain_info.rtc_offset = object.options['rtc_offset']
			# drives
			domain_info.disks = self.drives
			self.uvmm._verify_device_files(domain_info)
			# on PV machines we should move the CDROM drive to first position
			if domain_info.os_type in ( 'linux', 'xen' ):
				non_disks, disks = [], []
				for dev in domain_info.disks:
					if dev.device == uvmmp.Disk.DEVICE_DISK:
						disks.append(dev)
					else:
						non_disks.append(dev)
				domain_info.disks = non_disks + disks
			# network interface
			if object.options[ 'interface' ]:
				iface = uvmmp.Interface()
				iface.source = object.options[ 'interface' ]
				if object.options[ 'pvinterface' ] == '1' and domain_info.os_type == 'hvm':
					if domain_info.domain_type == 'xen':
						iface.model = 'netfront'
					elif domain_info.domain_type in ( 'kvm', 'qemu' ):
						iface.model = 'virtio'
				domain_info.interfaces = [iface,]

			self._result = domain_info

		return umcd.WizardResult()

	def new_drive( self, object, cancel = True ):
		# all next, prev and finished events must be redirected to the drive wizard
		name = object.options['name']
		self.drive_wizard_active = True
		self.drive_wizard_cancel = cancel
		self.drive_wizard.replace_title(_('Add drive to <i>%(name)s</i>') % {'name': xml_escape(name)})
		self.drive_wizard.domain_name = name
		self.drive_wizard.domain_virttech( object.options['type'] )
		self.drive_wizard.blacklist = [os.path.basename(drive.source) for drive in self.drives if drive.source]
		ud.debug(ud.ADMIN, ud.INFO, 'NEW DRIVE: bl=%s' % self.drive_wizard.blacklist)
		self.drive_wizard.set_node( self.node_uri, self.node_info )
		return self.drive_wizard.action( object )

	def setup( self, object, prev = None, next = None, finish = None, cancel = None ):
		if self.drive_wizard_active:
			return self.drive_wizard.setup( object, finish = _( 'Add' ), cancel = self.drive_wizard_cancel )
		return umcd.IWizard.setup( self, object )

	def cancel( self, object ):
		if self.drive_wizard_active:
			self.drive_wizard_active = False
			# fall back to instance overview
			self.current = InstanceWizard.PAGE_SUMMARY
			self.drive_wizard.reset()

		return umcd.WizardResult()

	def reset( self ):
		self.drives = []
		self.drive_number = 0
		self.drive_wizard.reset()
		self.drive_wizard_active = False
		umcd.IWizard.reset( self )
