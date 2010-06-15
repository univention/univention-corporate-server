#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: management of virtualization servers
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

class KBLayoutSelect( umc.StaticSelection ):
	def choices( self ):
		return ( ( 'de', _( 'German' ) ), ( 'en-us', _( 'American' ) ) )

class NumberSelect( umc.StaticSelection ):
	def __init__( self, label, max = 8, required = True, may_change = True ):
		self.max = max
		umc.StaticSelection.__init__( self, label, required = required, may_change = may_change )
		
	def choices( self ):
		return map( lambda x: ( str( x ), str( x ) ), range( 1, self.max + 1 ) )

class DriveTypSelect( umc.StaticSelection ):
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
umcd.copy( umc.StaticSelection, KBLayoutSelect )
umcd.copy( umc.StaticSelection, NumberSelect )
umcd.copy( umc.StaticSelection, DriveTypSelect )
umcd.copy( umc.StaticSelection, NodeSelect )
umcd.copy( umc.StaticSelection, DiskSelect )
