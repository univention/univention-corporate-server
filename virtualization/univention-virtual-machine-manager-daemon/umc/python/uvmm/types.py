#!/usr/bin/python2.6
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

import copy
import operator

import univention.management.console as umc
import univention.management.console.dialog as umcd
from uvmmd import Client

_ = umc.Translation('univention.management.console.handlers.uvmm').translate

class DynamicSelect( umc.StaticSelection ):
	"""List, which is updateable during run-time."""
	def __init__( self, label, required = True, may_change = True ):
		self._choices = []
		umc.StaticSelection.__init__( self, label, required = required, may_change = may_change )

	def choices( self ):
		choices = []
		if self._choices and isinstance( self._choices[ 0 ], ( list, tuple ) ):
			return self._choices
		return map( lambda x: ( x, x ), self._choices )

	def update_choices( self, types ):
		self._choices = types

class VirtTechSelect( umc.StaticSelection ):
	"""List of virtualization techs."""
	MAPPING = {
		'kvm-hvm' : _( 'Full virtualization (KVM)' ),
		'xen-hvm' : _( 'Full virtualization (XEN)' ),
		'xen-xen' : _( 'Paravirtualization (XEN)' ) ,
		}
	def __init__( self, label, required = True, may_change = True ):
		self._choices = []
		umc.StaticSelection.__init__( self, label, required = required, may_change = may_change )

	def choices( self ):
		return map( lambda x: ( x, VirtTechSelect.MAPPING[ x ] ), self._choices )

	def update_choices( self, types ):
		self._choices = types

class ArchSelect( umc.StaticSelection ):
	"""List of architectures."""
	MAPPING = {
		'i686' : '32 Bit',
		'x86_64' : '64 Bit',
		}
	def __init__( self, label, required = True, may_change = True ):
		self._choices = []
		umc.StaticSelection.__init__( self, label, required = required, may_change = may_change )

	def choices( self ):
		return map( lambda x: ( x, ArchSelect.MAPPING[ x ] ), self._choices )

	def update_choices( self, types ):
		self._choices = types

class SearchOptions( umc.StaticSelection ):
	"""List of search options."""
	def choices( self ):
		return ( ( 'all', _( 'All' ) ), ( 'nodes', _( 'Physical servers' ) ), ( 'domains', _( 'Instance names' ) ), ( 'contacts', _( 'Contact information' ) ), ( 'descriptions', _( 'Descriptions' ) ) )

class KBLayoutSelect( umc.StaticSelection ):
	"""List of keyboard layouts."""
	def choices( self ):
		return (
				('ar', _('Arabic')),
				('da', _('Danish')),
				('de', _('German')),
				('de-ch', _('German-Switzerland')),
				('en-gb', _('English-Britain')),
				('en-us', _('English-America')),
				('es', _('Spanish')),
				('et', _('Estonian')),
				('fi', _('Finnish')),
				('fo', _('Faroese')),
				('fr', _('French')),
				('fr-be', _('French-Belgium')),
				('fr-ca', _('French-Canada')),
				('fr-ch', _('French-Switzerland')),
				('hr', _('Croatian')),
				('hu', _('Hungarian')),
				('is', _('Icelandic')),
				('it', _('Italian')),
				('ja', _('Japanese')),
				('lt', _('Lithuanian')),
				('lv', _('Latvian')),
				('mk', _('Macedonian')),
				('nl', _('Dutch')),
				('nl-be', _('Dutch-Belgium')),
				('no', _('Norwegian')),
				('pl', _('Polish')),
				('pt', _('Portuguese')),
				('pt-br', _('Portuguese-Brasil')),
				('ru', _('Russian')),
				('sl', _('Slovene')),
				('sv', _('Swedish')),
				('th', _('Thai')),
				('tr', _('Turkish')),
				)

class BootDeviceSelect( umc.StaticSelection ):
	"""List of devices to boot from."""
	def __init__( self ):
		umc.StaticSelection.__init__( self, _( 'Boot order' ) )
		self._choices = ( ( 'hd', _( 'Hard drive' ) ), ( 'cdrom', _( 'CDROM drive' ) ), ( 'network', _( 'Network' ) ) )

	def choices( self ):
		return self._choices

class NumberSelect( umc.StaticSelection ):
	"""List of numbers."""
	def __init__( self, label, max = 8, required = True, may_change = True ):
		self.max = max
		umc.StaticSelection.__init__( self, label, required = required, may_change = may_change )

	def choices( self ):
		return map( lambda x: ( str( x ), str( x ) ), range( 1, self.max + 1 ) )

class DriveTypeSelect( umc.StaticSelection ):
	"""List of block device types."""
	def __init__( self ):
		self.floppies = True
		self._types = ( ( 'disk', _( 'Hard drive' ) ), ( 'cdrom', _( 'CD/DVD-ROM' ) ) )
		umc.StaticSelection.__init__( self, _( 'Type of drive' ) )

	def choices( self ):
		if self.floppies:
			return self._types + ( ( 'floppy', _( 'Floppy drive' ) ), )

		return self._types

class NIC_DriverSelect( umc.StaticSelection ):
	"""List of network interface drivers."""
	def __init__( self, virttech = None ):
		umc.StaticSelection.__init__( self, _( 'Driver' ) )
		self.virttech = virttech
		self._list = ( ( 'rtl8139', _( 'Default (RealTek RTL-8139)' ) ),
					   ( 'e1000', 'Intel PRO/1000' ),
					   )
		self._xen = ( ( 'netfront', _( 'Paravirtual device (xen)' ) ), )
		self._kvm = ( ( 'virtio', _( 'Paravirtual device (virtio)' ) ), )
		self._all = self._kvm + self._xen + self._list

	def description( self, key ):
		return dict( self._all ).get( key, _( 'Unknown' ) )

	def choices( self ):
		if self.virttech == 'xen':
			return self._xen + self._list
		elif self.virttech in ( 'kvm', 'qemu' ):
			return self._kvm + self._list
		return ()

class DiskSelect( umc.StaticSelection ):
	"""Select between creating a new, reusing an existing image or integrating a local block device."""
	def __init__( self ):
		umc.StaticSelection.__init__(self, '' )
		self._default = [
				('disk-new', _('Create a new image')),
				('disk-exists', _('Choose existing image')),
				('disk-block', _('Use a local device')),
				('disk-empty', _('No media')),
				]
		self._choices = None
		self.set_choices()

	def set_choices( self, with_new = True ):
		if with_new:
			self._choices = self._default[0:3]
		else:
			self._choices = self._default[1:4]

	def choices( self ):
		return self._choices

class NodeSelect( umc.StaticSelection ):
	"""List of known nodes."""
	def __init__( self, label, required = True, may_change = True ):
		self._choices = []
		umc.StaticSelection.__init__( self, label, required = required, may_change = may_change )

	def choices( self ):
		return sorted([(uri, Client._uri2name(uri)) for uri in self._choices], key=operator.itemgetter(1))

	def update_choices(self, nodes):
		self._choices = nodes

class RtcOffsetSelect(umc.StaticSelection):
	"""List of RTC offsets."""
	def choices(self):
		return (
				('utc', _('Coordinated Universal Time')),
				('localtime', _('Local time zone')),
				)

# Copy factory method for widget creation
umcd.copy( umc.StaticSelection, SearchOptions )
umcd.copy( umc.StaticSelection, DynamicSelect )
umcd.copy( umc.StaticSelection, VirtTechSelect )
umcd.copy( umc.StaticSelection, KBLayoutSelect )
umcd.copy( umc.StaticSelection, BootDeviceSelect )
umcd.copy( umc.StaticSelection, NumberSelect )
umcd.copy( umc.StaticSelection, DriveTypeSelect )
umcd.copy( umc.StaticSelection, NodeSelect )
umcd.copy( umc.StaticSelection, DiskSelect )
umcd.copy( umc.StaticSelection, ArchSelect )
umcd.copy( umc.StaticSelection, NIC_DriverSelect )
umcd.copy(umc.StaticSelection, RtcOffsetSelect)
