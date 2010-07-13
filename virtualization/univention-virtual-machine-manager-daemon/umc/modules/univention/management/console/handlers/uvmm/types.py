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

import univention.management.console as umc
import univention.management.console.dialog as umcd

_ = umc.Translation('univention.management.console.handlers.uvmm').translate

class DynamicSelect( umc.StaticSelection ):
	def __init__( self, label, required = True, may_change = True ):
		self._choices = []
		umc.StaticSelection.__init__( self, label, required = required, may_change = may_change )

	def choices( self ):
		return map( lambda x: ( x, x ), self._choices )

	def update_choices( self, types ):
		self._choices = types

class VirtTechSelect( umc.StaticSelection ):
	MAPPING = { 'hvm' : _( 'Full virtualization' ),
				'xen' : _( 'Paravirtualization' ) ,
				}
	def __init__( self, label, required = True, may_change = True ):
		self._choices = []
		umc.StaticSelection.__init__( self, label, required = required, may_change = may_change )

	def choices( self ):
		return map( lambda x: ( x, VirtTechSelect.MAPPING[ x ] ), self._choices )

	def update_choices( self, types ):
		self._choices = types

class KBLayoutSelect( umc.StaticSelection ):
	def choices( self ):
		return ( ( 'de', _( 'German' ) ), ( 'en-us', _( 'American' ) ) )

class BootDeviceSelect( umc.StaticSelection ):
	CHOICES = ( ( 'fd', _( 'Floppy disk' ) ), ( 'hd', _( 'Hard drive' ) ), ( 'cdrom', _( 'CDROM drive' ) ), ( 'network', _( 'Network' ) ) )

	def choices( self ):
		return BootDeviceSelect.CHOICES

class NumberSelect( umc.StaticSelection ):
	def __init__( self, label, max = 8, required = True, may_change = True ):
		self.max = max
		umc.StaticSelection.__init__( self, label, required = required, may_change = may_change )

	def choices( self ):
		return map( lambda x: ( str( x ), str( x ) ), range( 1, self.max + 1 ) )

class DriveTypeSelect( umc.StaticSelection ):
	def choices( self ):
		return ( ( 'disk', _( 'Hard drive' ) ), ( 'cdrom', _( 'CD/DVD-ROM' ) ) )

class DiskSelect( umc.StaticSelection ):
	def choices( self ):
		return ( ( 'disk-new', _( 'Create a new image' ) ), ( 'disk-exists', _( 'Choose existing image' ) ) )

class NodeSelect( umc.StaticSelection ):
	def __init__( self, label, required = True, may_change = True ):
		self._choices = []
		umc.StaticSelection.__init__( self, label, required = required, may_change = may_change )

	def choices( self ):
		return map( lambda x: ( x, x ), self._choices )

	def update_choices( self, nodes, ignore ):
		self._choices = nodes
		if ignore in self._choices:
			self._choices.remove( ignore )

umcd.copy( umc.StaticSelection, DynamicSelect )
umcd.copy( umc.StaticSelection, VirtTechSelect )
umcd.copy( umc.StaticSelection, KBLayoutSelect )
umcd.copy( umc.StaticSelection, BootDeviceSelect )
umcd.copy( umc.StaticSelection, NumberSelect )
umcd.copy( umc.StaticSelection, DriveTypeSelect )
umcd.copy( umc.StaticSelection, NodeSelect )
umcd.copy( umc.StaticSelection, DiskSelect )
