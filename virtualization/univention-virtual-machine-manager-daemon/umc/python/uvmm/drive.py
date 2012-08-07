# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: management of virtualization servers
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

import univention.management.console.dialog as umcd
import univention.management.console.protocol as umcp
import univention.management.console as umc

import univention.uvmm.node as uvmmn

import univention.debug as ud

import copy
import os.path

from treeview import *
from tools import *
from uvmmd import UvmmError
from xml.sax.saxutils import escape as xml_escape

_ = umc.Translation('univention.management.console.handlers.uvmm').translate
_uvmm_locale = umc.Translation('univention.virtual.machine.manager').translate

class DriveCommands( object ):
	def uvmm_drive_create( self, object ):
		"""Create new drive using a wizard."""
		ud.debug(ud.ADMIN, ud.INFO, 'UVMM.drive_create(action=%(action)s)' % ddict(object.options))
		tv = TreeView(self.uvmm, object)
		try:
			res = tv.get_tree_response(TreeView.LEVEL_DOMAIN)
			node_uri = tv.node_uri
			domain_info = tv.domain_info
			node_info = tv.node_info
		except (uvmmd.UvmmError, KeyError), e:
			ud.debug(ud.ADMIN, ud.INFO, 'UVMM.drive_create: node %(node)s#%(domains)s not found' % request.options)
			return self.uvmm_node_overview( object )

		# user cancelled the wizard
		if object.options.get( 'action' ) == 'cancel':
			self.drive_wizard.reset()
			del object.options[ 'action' ]
			self.uvmm_domain_overview( object )
			return

		# starting the wizard
		if not 'action' in object.options:
			self.drive_wizard.reset()
			self.drive_wizard.drive_type_select.floppies = domain_info.os_type == 'hvm'
			self.drive_wizard.domain_name = object.options['domain']
			self.drive_wizard.domain_virttech( '%s-%s' % ( domain_info.domain_type, domain_info.os_type ) )
			self.drive_wizard.blacklist = [] # does query domains
			self.drive_wizard.set_node( node_uri, node_info )

		result = self.drive_wizard.action( object )

		# wizard finished?
		new_disk = self.drive_wizard.result()
		if new_disk:
			domain_info.disks.append( new_disk )
			try:
				resp = self.uvmm.domain_configure(node_uri, domain_info )
				self.drive_wizard.reset()
				self.uvmm_domain_overview( object )
			except UvmmError, e:
				self.drive_wizard.reset()
				res = self.uvmm_domain_overview( object, finish = False )
				res.status( 301 )
				self.finished(object.id(), res, report=str(e))
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
		"""Remove drive from domain and optionally delete used image."""
		ud.debug(ud.ADMIN, ud.INFO, 'UVMM.drive_remove(%(disk)s)' % ddict(object.options))

		tv = TreeView(self.uvmm, object)
		if object.incomplete:
			try:
				res = tv.get_tree_response(TreeView.LEVEL_DOMAIN)
			except UvmmError, e:
				res = tv.get_failure_response(e)
				self.finished(object.id(), res)
				return
		else:
			res = umcp.Response( object )

		try:
			node_uri = tv.node_uri
			domain_info = tv.domain_info
		except UvmmError, e:
			ud.debug(ud.ADMIN, ud.INFO, 'UVMM.drive_remove: node %(node)s#%(domain)s not found' % object.options)
			return self.uvmm_node_overview(object)

		# find disk to remove and collect others to keep
		target_dev = object.options['disk']
		new_disks = []
		rm_disk = None
		for disk in domain_info.disks:
			if disk.target_dev == target_dev:
				rm_disk = disk
			else:
				new_disks.append(disk)
		if rm_disk is None:
			ud.debug(ud.ADMIN, ud.INFO, 'UVMM.drive_remove: failed to find %(disk)s' % object.options)
			return self.finished(object.id(), res)

		if object.incomplete:
			# remove domain
			# if the attached drive could be removed successfully the user should be ask, if the image should be removed
			try:
				do_delete = self._is_disk_deleteable(rm_disk, tv)
			except (TypeError, ValueError), e:
				do_delete = False
			lst = umcd.List( default_type = 'uvmm_table' )

			opts = copy.copy( object.options )
			overview = umcp.SimpleCommand( 'uvmm/domain/overview', options = opts )
			opts = copy.copy( object.options )
			opts[ 'drive-remove' ] = True
			remove = umcp.SimpleCommand( 'uvmm/drive/remove', options = opts )
			opts = copy.copy( object.options )
			opts[ 'drive-remove' ] = False
			detach = umcp.SimpleCommand( 'uvmm/drive/remove', options = opts )

			if rm_disk.source and rm_disk.type != uvmmn.Disk.TYPE_BLOCK:
				lst.add_row([umcd.Cell(umcd.HTML(_('The drive will be detached from the virtual instance.<br/>Additionally the associated image <i>%(image)s</i> may be deleted permanently.') % {'image': xml_escape(rm_disk.source)}), attributes={'colspan': '3'})])
				btn_cancel = umcd.Button(_('Cancel'), actions=[umcd.Action(overview)])
				btn_detach = umcd.Button(_('Detach'), actions=[umcd.Action(detach), umcd.Action(overview)], default=not do_delete)
				btn_delete = umcd.Button(_('Delete'), actions=[umcd.Action(remove), umcd.Action(overview)], default=do_delete)
				lst.add_row( [ '' ] )
				lst.add_row([btn_cancel, '', umcd.Cell(btn_detach, attributes={'align': 'right', 'colspan': '2'}), umcd.Cell(btn_delete, attributes={'align': 'right'})])
			else:
				if rm_disk.source:
					msg = _('The drive will be detached from the virtual instance and the associated local device will be kept as is.')
				else:
					msg = _('The drive will be detached from the virtual instance.')
				lst.add_row([umcd.Cell(umcd.Text(msg), attributes={'colspan': '3'})])
				lst.add_row( [ '' ], attributes = { 'colspan' : '3' } )
				btn_detach = umcd.Button( _( 'Detach' ), actions = [ umcd.Action( detach ), umcd.Action( overview ) ], default = True )
				btn_cancel = umcd.Button( _( 'Cancel' ), actions=[ umcd.Action( overview ) ] )
				lst.add_row( [ btn_cancel, '', umcd.Cell( btn_detach, attributes = { 'align' : 'right' } ) ] )

			res.dialog[ 0 ].set_dialog( lst )
			self.finished(object.id(), res)
		else:
			domain_info.disks = new_disks
			try:
				resp = self.uvmm.domain_configure(node_uri, domain_info )
			except UvmmError, e:
				res.status( 301 )
				self.finished(object.id(), res, report=_('Detaching the drive <i>%(drive)s</i> failed') % {'drive': xml_escape(target_dev)})
				return

			if rm_disk.source and object.options.get('drive-remove', False):
				try:
					self.uvmm.storage_volumes_destroy(node_uri, [rm_disk.source,])
				except UvmmError, e:
					res.status( 301 )
					self.finished(object.id(), res, report=_('The drive <i>%(drive)s</i> was detached successfully, but removing the image <i>%(image)s</i> failed. It must be removed manually.') % {'drive': xml_escape(target_dev), 'image': xml_escape(rm_disk.source)})
					return
				res.status( 201 )
				self.finished(object.id(), res, report=_('The drive <i>%(drive)s</i> was detached and image <i>%(image)s</i> removed successfully.') % {'drive': xml_escape(target_dev), 'image': xml_escape(rm_disk.source)})
			res.status( 201 )
			self.finished(object.id(), res, report=_('The drive <i>%(drive)s</i> was detached successfully.') % {'drive': xml_escape(target_dev)})

	def uvmm_drive_edit( self, object ):
		"""Edit drive: chnage use of VirtIO / PV."""
		ud.debug(ud.ADMIN, ud.INFO, 'UVMM.drive_edit(%s)' % object.options)
		res = umcp.Response( object )

		tv = TreeView(self.uvmm, object)
		try:
			node_uri = tv.node_uri
			domain_info = tv.domain_info
		except (uvmmd.UvmmError, KeyError), e:
			ud.debug(ud.ADMIN, ud.INFO, 'UVMM.drive_edit: node %(node)s#%(somain)s not found' % request.options)
			return self.uvmm_node_overview( object )

		drive = None
		for disk in domain_info.disks:
			if disk.target_dev == object.options[ 'disk' ]:
				drive = disk
				break
		else:
			ud.debug(ud.ADMIN, ud.INFO, 'UVMM.drive_edit: failed to find %(disk)s' % object.options)
			return self.finished(object.id(), res)

		if object.incomplete:
			try:
				res = tv.get_tree_response(TreeView.LEVEL_DOMAIN)
			except UvmmError, e:
				res = tv.get_failure_response(e)
				self.finished(object.id(), res)
				return
			conf = umcd.List( default_type = 'uvmm_table' )
			conf.add_row( [ umcd.HTML( _( 'All image files are stored in so-called storage pools. They can be stored in a local directory, an LVM partition or a share (e.g. using iSCSI, NFS or CIFS).'),  attributes = { 'colspan' : '3' } ) ] )
			conf.add_row( [ umcd.HTML( _( 'Hard drive images can be administrated in two ways on KVM systems; by default images are saved in the <i>Extended format (qcow2)</i>. This format supports copy-on-write which means that changes do not overwrite the original version, but store new versions in different locations. The internal references of the file administration are then updated to allow both access to the original and the new version. This technique is a prerequisite for efficiently managing snapshots of virtual machines. <p> Alternatively, you can also access a hard drive image in <i>Simple format (raw)</i>. Snapshots can only be created when using hard drive images in <i>Extended format</i>. Only the <i>Simple format</i> is available on Xen systems.' ), attributes = { 'colspan' : '3' } ) ] )
			conf.add_row( [ umcd.HTML( _( 'Paravirtualization is a special variant of virtualization in which the virtualized operating system is adapted to the underlying virtualization technology. This improves the performance. Linux systems usually support paravirtualization out of the box. For Windows systems additional support drivers need to be installed, see the <a href="http://wiki.univention.de/index.php?title=UVMM_Technische_Details">Univention wiki</a> for details (currently only available in German).' ), attributes = { 'colspan' : '3' } ) ] )
			conf.add_row( [ umcd.HTML( '<i>%s</i>' % _( 'Drive type' ) ), self._drive_name( drive.device ) ] )

			dirname = os.path.dirname(drive.source)
			basename = os.path.basename(drive.source)
			try:
				pools = self.uvmm.storage_pools(node_uri)
			except UvmmError, e:
				pools = ()
			for pool in pools:
				if pool.path.startswith(dirname):
					# detect the volume size
					try:
						volumes = self.uvmm.storage_pool_volumes(node_uri, pool.name)
					except UvmmError, e:
						volumes = ()
					for vol in volumes:
						if vol.source == drive.source:
							drive.size = vol.size
							break
					if drive.size:
						size = MemorySize.num2str( drive.size )
					else:
						size = _( 'unknown' )

					if pool.name == 'default':
						pool_name = _( 'Local directory' )
					else:
						pool_name = pool.name

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

					conf.add_row([umcd.HTML('<i>%s</i>' % _('Storage pool')), pool_name])
					if len(basename) > 60:
						conf.add_row([umcd.HTML('<i>%s</i>' % _('Image filename')), umcd.HTML('<p title="%s">%s...</p>' %(xml_escape(basename), xml_escape(basename[0:60])))])
					else:
						conf.add_row([umcd.HTML('<i>%s</i>' % _('Image filename')), basename])
					conf.add_row([umcd.HTML('<i>%s</i>' % _('Image format')), driver_type])
					conf.add_row([umcd.HTML('<i>%s</i>' % _('Image size')), size])

					break
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
		paravirtual = object.options[ 'drive-paravirtual' ]
		old_paravirtual = object.options[ 'drive-paravirtual-old' ]
		if paravirtual != old_paravirtual:
			for disk in domain_info.disks:
				if disk.target_dev == object.options[ 'disk' ]:
					ud.debug(ud.ADMIN, ud.INFO, 'UVMM.drive_edit: found disk')
					disk.target_dev = '' # this is the unique identifier for a disk, which must be changed to match the new bus. Bad things might happen...
					if paravirtual:
						if node_uri.startswith('qemu'):
							disk.target_bus = 'virtio'
						elif node_uri.startswith('xen'):
							disk.target_bus = 'xen'
						else:
							ud.debug(ud.ADMIN, ud.WARNING, 'UVMM.drive_edit: unknown PV type: %s' % node_uri)
					else:
						disk.target_bus = 'ide'
					ud.debug(ud.ADMIN, ud.INFO, 'UVMM.drive_edit: new target bus: %s' % disk.target_bus)
					break

		try:
			resp = self.uvmm.domain_configure(node_uri, domain_info)
		except UvmmError, e:
			res.status( 301 )
			self.finished( object.id(), res, report = _( 'Saving the drive configuration has failed' ) )
			return

		self.finished( object.id(), res, report = _( 'The drive configuration has been saved successfully' ) )

	def uvmm_drive_bootdevice( self, object ):
		"""Change boot device for Xen-PV."""
		ud.debug(ud.ADMIN, ud.INFO, 'UVMM.drive_bootdevice(%(disk)s)' % object.options)
		res = umcp.Response( object )

		try:
			node_uri, node_name = self.uvmm.node_uri_name(object.options['node'])
			node_info, domain_info = self.uvmm.get_domain_info_ext(node_uri, object.options['domain'])
		except UvmmError, e:
			ud.debug(ud.ADMIN, ud.INFO, 'UVMM.drive_bootdevice: node %(node)s#%(domain)s not found' % request.options)
			return self.uvmm_node_overview( object )
		try:
			new_disks = []
			for disk in domain_info.disks:
				if disk.target_dev != object.options[ 'disk' ]:
					new_disks.append(disk)
				else:
					ud.debug(ud.ADMIN, ud.INFO, 'UVMM.drive_bootdevice: new found')
					new_disks.insert(0, disk)
			domain_info.disks = new_disks
			resp = self.uvmm.domain_configure(node_uri, domain_info)
			self.finished( object.id(), res )
		except UvmmError, e:
			res.status( 301 )
			self.finished(object.id(), res, report=_('Setting the drive <i>%(drive)s</i> as boot device as failed') % {'drive': xml_escape(object.options['disk'])})

	def uvmm_drive_media_change(self, request):
		"""Eject or change media from device"""
		ud.debug(ud.ADMIN, ud.INFO, 'UVMM.drive_media_change(%(target_dev)s of domain %(domain)s on node %(node)s; action=%(action)s)' % ddict(request.options))

		# user cancelled the wizard
		if action == 'cancel':
			self.media_wizard.reset()
			del request.options['action']
			return self.uvmm_domain_overview(request)

		action = request.options.get('action')
		try:
			node_uri, node_name = self.uvmm.node_uri_name(object.options['node'])
			node_info, domain_info = self.uvmm.get_domain_info_ext(node_uri, domain_name)
		except UvmmError, e:
			ud.debug(ud.ADMIN, ud.INFO, 'UVMM.drive_media_change: node %(node)s#%(domain)s not found' % request.options)
			return self.uvmm_node_overview(request)
		domain_name = request.options['domain']
		target_dev = request.options['target_dev']

		# Find disk...
		for disk in domain_info.disks:
			if disk.target_dev == target_dev:
				break
		else:
			ud.debug(ud.ADMIN, ud.INFO, 'UVMM.drive_media_change: Target device %(taregt_dev)s not found in domain %(domain)s' % request.options)
			return self.uvmm_node_overview(request)

		assert disk.device in (uvmmn.Disk.DEVICE_CDROM, uvmmn.Disk.DEVICE_FLOPPY)

		# Show selection for new image
		if action is None:
			self.media_wizard.reset()
			request.options['existing-or-new-disk'] = 'disk-exists'
			self.media_wizard.current = self.media_wizard.PAGE_INIT
			self.media_wizard.drive_type_select.floppies = domain_info.os_type == 'hvm'
			self.media_wizard.domain_name = domain_name
			self.media_wizard.domain_virttech('%s-%s' % (domain_info.domain_type, domain_info.os_type))
			self.media_wizard.blacklist = [] # does query domains
			self.media_wizard.set_node(node_uri, node_info)

		result = self.media_wizard.action(request)

		# wizard finished?
		new_disk = self.media_wizard.result()
		if new_disk:
			ud.debug(ud.ADMIN, ud.INFO, 'UVMM.drive_media_change: Change media from %s:%s to %s:%s' % (disk.type, disk.source, new_disk.type, new_disk.source))
			if (disk.type, disk.source) != (new_disk.type, new_disk.source):
				disk.type = new_disk.type # FILE | BLOCK
				disk.source = new_disk.source
				disk.driver = new_disk.driver # file | qemu | tap2
				try:
					resp = self.uvmm.domain_configure(node_uri, domain_info)
					self.media_wizard.reset()
				except UvmmError, e:
					self.media_wizard.reset()
					res = self.uvmm_domain_overview(request, finish=False)
					res.status(301)
					return self.finished(request.id(), res, report=str(e).strip()) # BUG: the report is not shown if it has a trailing \r\n ?
			return self.uvmm_domain_overview(request)

		# navigating in the wizard ...
		page = self.media_wizard.setup(request)
		res = self.uvmm_domain_overview(request, finish=False)
		res.dialog[0].set_dialog(page)
		if not result:
			res.status(201)
			report = result.text
		else:
			report = ''
		self.finished(request.id(), res, report=report)

	def _is_disk_deleteable(self, disk, tv):
		"""
		Check if disk is shared.
		Raises ValueError if technically impossible (missing functionality)
		Raises TypeError if policy incompatible.
		Returns False if images is shared.
		"""
		if not disk.source:
			raise ValueError('no source')
		if getattr(disk, 'pool', None) is None:
			raise ValueError('no pool')
		if disk.type != uvmmn.Disk.TYPE_FILE: # FIXME: block-devices should work also as long as they are in a pool than can handle this
			raise TypeError('not a file')
		if disk.device != uvmmn.Disk.DEVICE_DISK:
			raise TypeError('not a disk')
		for (group_name2, nodes_infos2) in tv.node_tree.items():
			for (node_uri2, node_info2) in nodes_infos2.items():
				for (domain_uuid2, domain_info2) in node_info2.domains.items():
					if (tv.node_uri, tv.domain_uuid) == (node_uri2, domain_uuid2):
						continue # skip self
					for disk2 in domain_info2.disks:
						if disk.source == disk2.source:
							return False
		return True
