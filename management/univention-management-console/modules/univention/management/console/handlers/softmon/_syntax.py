#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module softmon: software monitor syntax definitions
#
# Copyright (C) 2007 Univention GmbH
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

_ = umc.Translation( 'univention.management.console.handlers.softmon' ).translate

class SoftMonSearchOperator( umc.StaticSelection ):
	def __init__( self ):
		umc.StaticSelection.__init__( self, _( 'Operator' ) )
		self._choices = []

	def choices( self ):
		return ( ( 'eq', _( 'equal' ) ),
				 ( 'ne', _( 'not equal' ) ),
				 ( 'gt', _( 'greater than' ) ),
				 ( 'lt', _( 'less than' ) ),
				 ( 'ge', _( 'greater equal' ) ),
				 ( 'le', _( 'less equal' ) ) )

class SoftMonSystemVersions( umc.StaticSelection ):
	def __init__( self ):
		umc.StaticSelection.__init__( self, _( 'Operator' ) )
		self._choices = []

	def choices( self ):
		return ( ( '1.3-0-0', '1.3-0-0' ),
				 ( '1.3-1-0', _( '1.3-1-0' ) ),
				 ( '1.3-2-0', _( '1.3-2-0' ) ),
				 ( '2.0-0-0', _( '2.0-0-0' ) ) )

class SoftMonSystemSearchKey( umc.StaticSelection ):
	def __init__( self ):
		umc.StaticSelection.__init__( self, _( 'Search Key' ) )
		self._choices = []

	def choices( self ):
		return ( ( 'name', _( 'System Name' ) ),
				 ( 'role', _( 'System Role' ) ),
				 ( 'ucs_version', _( 'UCS Version' ) ) )

class SoftMonPackageSearchKey( umc.StaticSelection ):
	def __init__( self ):
		umc.StaticSelection.__init__( self, _( 'Search Key' ) )
		self._choices = []

	def choices( self ):
		return ( ( 'name', _( 'Package Name' ) ),
				 ( 'pkg_version', _( 'Package Version' ) ),
				 ( 'selected_status', _( 'Selected Status' ) ),
				 ( 'installed_status', _( 'Installation Status' ) ),
				 ( 'current_status', _( 'Current Status' ) ),
				 ( 'ucs_version', _( 'UCS Version' ) ) )

system_filter_types = { 'name' : umc.String( _( 'Text' ) ),
						'role' : umc.SystemRoleSelection( _( 'System Role' ) ),
						'ucs_version' : SoftMonSystemVersions() }

umcd.copy( umc.StaticSelection, SoftMonSystemSearchKey )
umcd.copy( umc.StaticSelection, SoftMonPackageSearchKey )
umcd.copy( umc.StaticSelection, SoftMonSearchOperator )
umcd.copy( umc.StaticSelection, SoftMonSystemVersions )
