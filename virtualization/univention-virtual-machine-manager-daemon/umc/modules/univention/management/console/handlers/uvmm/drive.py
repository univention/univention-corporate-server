#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: management of virtualization servers
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

import univention.management.console.dialog as umcd
import univention.management.console.protocol as umcp
import univention.management.console as umc

import univention.uvmm.node as uvmmn

import univention.debug as ud

import copy
import os

from treeview import *
from tools import *

_ = umc.Translation('univention.management.console.handlers.uvmm').translate
_uvmm_locale = umc.Translation('univention.virtual.machine.manager').translate

class DriveCommands( object ):
	def uvmm_drive_create( self, object ):
		ud.debug( ud.ADMIN, ud.INFO, 'Drive create' )
		( success, res ) = TreeView.safely_get_tree( self.uvmm, object, ( 'group', 'node', 'domain' ) )
		if not success:
			self.finished(object.id(), res)
			return
		node_uri = self.uvmm.node_name2uri( object.options[ 'node' ] )
		if not node_uri:
			return self.uvmm_node_overview( object )
		node_info = self.uvmm.get_node_info( node_uri )

		ud.debug( ud.ADMIN, ud.INFO, 'Drive create: action: %s' % str( object.options.get( 'action' ) ) )
		# user cancelled the wizard
		if object.options.get( 'action' ) == 'cancel':
			self.drive_wizard.reset()
			del object.options[ 'action' ]
			self.uvmm_domain_overview( object )
			return

		# starting the wizard
		if not 'action' in object.options:
			domain_info = self.uvmm.get_domain_info( node_uri, object.options[ 'domain' ] )
			self.drive_wizard.reset()
			self.drive_wizard.drive_type_select.floppies = domain_info.os_type == 'hvm'
			self.drive_wizard.domain_name = object.options['domain']
			self.drive_wizard.domain_virttech( '%s-%s' % ( domain_info.domain_type, domain_info.os_type ) )
			self.drive_wizard.blacklist = [] # does query domains
			self.drive_wizard.set_node( node_uri, node_info )

		result = self.drive_wizard.action( object )

		# domain wizard finished?
		new_disk = self.drive_wizard.result()
		if new_disk:
			domain_info = self.uvmm.get_domain_info( node_uri, object.options[ 'domain' ] )
			domain_info.disks.append( new_disk )
			resp = self.uvmm.domain_configure( object.options[ 'node' ], domain_info )
			self.drive_wizard.reset()
			if self.uvmm.is_error( resp ):
				res = self.uvmm_domain_overview( object, finish = False )
				res.status( 301 )
				self.finished( object.id(), res, report = resp.msg )
			else:
				self.uvmm_domain_overview( object )
			return
		# navigating in the wizard ...
		page = self.drive_wizard.setup( object )
		res.dialog[ 0 ].set_dialog( page )
		if not result:
			res.status( 201 )
			report = result.text
		else:
			report = ''
		self.finished( object.id(), res, report = report )

	def uvmm_drive_remove( self, object ):
		ud.debug( ud.ADMIN, ud.INFO, 'Drive remove' )
		res = umcp.Response( object )

		if object.incomplete:
			( success, res ) = TreeView.safely_get_tree( self.uvmm, object, ( 'group', 'node', 'domain' ) )
			if not success:
				self.finished(object.id(), res)
				return
			# remove domain
			# if the attached drive could be removed successfully the user should be ask, if the image should be removed
			node_uri = self.uvmm.node_name2uri( object.options[ 'node' ] )
			if not node_uri:
				return self.uvmm_node_overview( object )
			node_info, domain_info = self.uvmm.get_domain_info_ext(node_uri, object.options['domain'])
			for disk in domain_info.disks:
				if disk.source == object.options['disk']:
					break
			is_shared_image = disk.device in ( uvmmn.Disk.DEVICE_CDROM, uvmmn.Disk.DEVICE_FLOPPY )
			lst = umcd.List( default_type = 'uvmm_table' )

			opts = copy.copy( object.options )
			overview = umcp.SimpleCommand( 'uvmm/domain/overview', options = opts )
			opts = copy.copy( object.options )
			opts[ 'drive-remove' ] = True
			remove = umcp.SimpleCommand( 'uvmm/drive/remove', options = opts )
			opts = copy.copy( object.options )
			opts[ 'drive-remove' ] = False
			detach = umcp.SimpleCommand( 'uvmm/drive/remove', options = opts )

			if disk.type != uvmmn.Disk.TYPE_BLOCK:
				lst.add_row( [ umcd.Cell( umcd.Text( _( 'The drive will be detached from the virtual instance. Additionally the associated image %(image)s may be deleted permanently. Should this be done also?' ) % { 'image' : object.options[ 'disk' ] } ), attributes = { 'colspan' : '3' } ) ] )
				no = umcd.Button(_('No'), actions=[umcd.Action(detach), umcd.Action(overview)], default=is_shared_image)
				yes = umcd.Button(_('Yes'), actions=[umcd.Action(remove), umcd.Action(overview)], default=not is_shared_image)
				lst.add_row( [ '' ] )
				lst.add_row( [ umcd.Cell( no, attributes = { 'align' : 'right', 'colspan' : '2' } ), umcd.Cell( yes, attributes = { 'align' : 'right' } ) ] )
			else:
				lst.add_row( [ umcd.Cell( umcd.Text( _( 'The drive will be detached from the virtual instance and the associated local device will be kept as is.' ) ), attributes = { 'colspan' : '3' } ) ] )
				lst.add_row( [ '' ], attributes = { 'colspan' : '3' } )
				btn_detach = umcd.Button( _( 'Detach' ), actions = [ umcd.Action( detach ), umcd.Action( overview ) ], default = True )
				btn_cancel = umcd.Button( _( 'Cancel' ), actions=[ umcd.Action( overview ) ] )
				lst.add_row( [ btn_cancel, '', umcd.Cell( btn_detach, attributes = { 'align' : 'right' } ) ] )

			res.dialog[ 0 ].set_dialog( lst )
			self.finished(object.id(), res)
		else:
			node_uri = self.uvmm.node_name2uri( object.options[ 'node' ] )
			if not node_uri:
				return self.uvmm_node_overview( object )
			domain_info = self.uvmm.get_domain_info( node_uri, object.options[ 'domain' ] )
			new_disks = []
			rm_disk = None
			for dev in domain_info.disks:
				if dev.source != object.options[ 'disk' ]:
					new_disks.append( dev )
				else:
					rm_disk = dev
			domain_info.disks = new_disks
			resp = self.uvmm.domain_configure( object.options[ 'node' ], domain_info )

			if rm_disk and rm_disk.type == uvmmn.Disk.TYPE_BLOCK:
				drive = object.options[ 'disk' ]
			else:
				drive = os.path.basename( object.options[ 'disk' ] )
			if self.uvmm.is_error( resp ):
				res.status( 301 )
				self.finished( object.id(), res, report = _( 'Detaching the drive <i>%(drive)s</i> failed' ) % { 'drive' : drive } )
				return

			if object.options.get( 'drive-remove', False ):
				resp = self.uvmm.storage_volumes_destroy( node_uri, [ object.options[ 'disk' ], ] )

				if not resp:
					res.status( 301 )
					self.finished( object.id(), res, report = _( 'Removing the image <i>%(disk)s</i> failed. It must be removed manually.' ) % { 'drive' : drive } )
					return
				res.status( 201 )
				self.finished( object.id(), res, report = _( 'The drive <i>%(drive)s</i> was detached and removed successfully' ) % { 'drive' : drive } )
			res.status( 201 )
			self.finished( object.id(), res, report = _( 'The drive <i>%(drive)s</i> was detached successfully' ) % { 'drive' : drive } )

	def uvmm_drive_edit( self, object ):
		ud.debug( ud.ADMIN, ud.INFO, 'Drive edit' )
		res = umcp.Response( object )

		node_uri = self.uvmm.node_name2uri( object.options[ 'node' ] )
		if not node_uri:
			return self.uvmm_node_overview( object )
		node_info, domain_info = self.uvmm.get_domain_info_ext( node_uri, object.options[ 'domain' ] )

		drive = None
		for disk in domain_info.disks:
			if disk.source == object.options[ 'disk' ]:
				drive = disk
				break

		if object.incomplete:
			( success, res ) = TreeView.safely_get_tree( self.uvmm, object, ( 'group', 'node', 'domain' ) )
			if not success:
				self.finished(object.id(), res)
				return
			conf = umcd.List( default_type = 'uvmm_table' )
			conf.add_row( [ umcd.HTML( _( 'All image files are stored in so-called storage pools. They can be stored in a local directory, an LVM partition or a share (e.g. using iSCSI, NFS or CIFS).'),  attributes = { 'colspan' : '3' } ) ] )
			conf.add_row( [ umcd.HTML( _( 'Hard drive images can be administrated in two ways on KVM systems; by default images are saved in the <i>Extended format (qcow2)</i>. This format supports copy-on-write which means that changes do not overwrite the original version, but store new versions in different locations. The internal references of the file administration are then updated to allow both access to the original and the new version. This technique is a prerequisite for efficiently managing snapshots of virtual machines. <p> Alternatively, you can also access a hard drive image in <i>Simple format (raw)</i>. Snapshots can only be created when using hard drive images in <i>Extended format</i>. Only the <i>Simple format</i> is available on Xen systems.' ), attributes = { 'colspan' : '3' } ) ] )
			conf.add_row( [ umcd.HTML( _( 'Paravirtualisation is a special variant of virtualisation in which the virtualised operating system is adapted to the underlying virtualisation technology. This improves the performance. Linux systems usually support paravirtualisation out of the box. For Windows systems additional support drivers need to be installed, see the <a href="http://wiki.univention.de/index.php?title=UVMM_Technische_Details"> Univention wiki </a> for details (currently only available in German).' ), attributes = { 'colspan' : '3' } ) ] )
			conf.add_row( [ umcd.HTML( '<i>%s</i>' % _( 'Drive type' ) ), self._drive_name( drive.device ) ] )
			if drive.type == uvmmn.Disk.TYPE_FILE:
				pool_name = ''
				dirname = os.path.dirname( drive.source )
				basename = os.path.basename( drive.source )
				for pool in self.uvmm.storage_pools( node_uri ):
					if pool.path.startswith( dirname ):
						pool_name = pool.name

				# detect the volume size
				for vol in self.uvmm.storage_pool_volumes(node_uri, pool_name):
					if vol.source == drive.source:
						drive.size = vol.size
						break

				if pool_name == 'default':
					pool_name = _( 'Local directory' )

				# show a more meaningful description
				# TODO: see wizards.py the description should be defined at one point
				if not drive.driver_type or drive.driver_type in ['aio', 'raw']:
					driver_type = _('Simple format (raw)')
				elif drive.driver_type == 'qcow2':
					driver_type = _('Extended format (qcow2)')
				elif drive.driver_type == 'qcow':
					driver_type = _('Extended format (qcow)')
				elif drive.driver_type == 'vmdk':
					driver_type = _('VMWare Disk')
				elif drive.driver_type == 'vhd':
					driver_type = _('Virtual Hard Disk')
				else:
					driver_type = drive.driver_type

				if drive.size:
					size = MemorySize.num2str( drive.size )
				else:
					size = _( 'unknown' )
				conf.add_row( [ umcd.HTML( '<i>%s</i>' % _( 'Storage pool' ) ), pool_name ] )
				conf.add_row( [ umcd.HTML( '<i>%s</i>' % _( 'Image filename' ) ), basename ] )
				conf.add_row( [ umcd.HTML( '<i>%s</i>' % _( 'Image format' ) ), driver_type ] )
				conf.add_row( [ umcd.HTML( '<i>%s</i>' % _( 'Image size' ) ), size ] )
			else:
				conf.add_row( [ umcd.HTML( '<i>%s</i>' % _( 'Device filename' ) ), drive.source ] )

			# editable options
			pv_default = drive.target_bus in ( 'xen', 'virtio' )
			paravirtual = umcd.make( ( 'drive-paravirtual', umc.Boolean( _( 'Paravirtual drive' ) ) ), default = pv_default )
			conf.add_row( [ umcd.Cell( paravirtual, attributes = { 'colspan' : '2' } ) ] )

			opts = copy.copy( object.options )
			opts[ 'drive-paravirtual-old' ] = pv_default
			save = umcp.SimpleCommand( 'uvmm/drive/edit', options = opts )
			overview = umcp.SimpleCommand( 'uvmm/domain/overview', options = copy.copy( object.options ) )

			btn_save = umcd.Button( _( 'Save' ), actions = [ umcd.Action( save, [ paravirtual.id() ] ), umcd.Action( overview ) ], default = True )
			btn_cancel = umcd.Button( _( 'Cancel' ), actions = [ umcd.Action( overview ) ] )
			conf.add_row( [ umcd.Fill( 2, '' ) ] )
			conf.add_row( [ btn_cancel, '', umcd.Cell( btn_save, attributes = { 'align' : 'right' } ) ] )

			res.dialog[ 0 ].set_dialog( umcd.Section( _( 'Edit drive' ), conf, hideable = False ) )
			self.finished(object.id(), res)
			return

		# save changes (if necessary)
		ud.debug( ud.ADMIN, ud.INFO, 'Drive edit: options: %s' % str( object.options ) )
		paravirtual = object.options[ 'drive-paravirtual' ]
		old_paravirtual = object.options[ 'drive-paravirtual-old' ]
		if paravirtual != old_paravirtual:
			for disk in domain_info.disks:
				if disk.source == object.options[ 'disk' ]:
					ud.debug( ud.ADMIN, ud.INFO, 'Drive edit: found disk' )
					disk.target_dev = ''
					if paravirtual:
						if node_uri.startswith( 'qemu' ):
							disk.target_bus = 'virtio'
						else:
							disk.target_bus = 'xen'
					else:
						disk.target_bus = 'ide'
					ud.debug( ud.ADMIN, ud.INFO, 'Drive edit: new target bus: %s' % disk.target_bus )
					break

		resp = self.uvmm.domain_configure( object.options[ 'node' ], domain_info )

		if self.uvmm.is_error( resp ):
			res.status( 301 )
			self.finished( object.id(), res, report = _( 'Saving the drive configuration has failed' ) )
			return

		self.finished( object.id(), res, report = _( 'The drive configuration has been saved successfully' ) )

	def uvmm_drive_bootdevice( self, object ):
		ud.debug( ud.ADMIN, ud.INFO, 'Drive boot device should be %s' % object.options[ 'disk' ] )
		res = umcp.Response( object )

		node_uri = self.uvmm.node_name2uri( object.options[ 'node' ] )
		if not node_uri:
			return self.uvmm_node_overview( object )
		domain_info = self.uvmm.get_domain_info( node_uri, object.options[ 'domain' ] )
		new_disks = []
		for dev in domain_info.disks:
			if dev.source != object.options[ 'disk' ]:
				new_disks.append( dev )
			else:
				ud.debug( ud.ADMIN, ud.INFO, 'found new boot device %s' % object.options[ 'disk' ] )
				new_disks.insert( 0, dev )
		domain_info.disks = new_disks
		resp = self.uvmm.domain_configure( object.options[ 'node' ], domain_info )

		if self.uvmm.is_error( resp ):
			res.status( 301 )
			self.finished( object.id(), res, report = _( 'Setting the drive <i>%(drive)s</i> as boot device as failed' ) % { 'drive' : os.path.basename( object.options[ 'disk' ] ) } )
		else:
			self.finished( object.id(), res )

