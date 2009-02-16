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
	def __init__( self, system_versions = None ):
		umc.StaticSelection.__init__( self, '' )
		if system_versions:
			self._choices = system_versions
		else:
			self._choices = ( ( '1.3-0-0', '1.3-0-0' ),
							  ( '1.3-1-0', '1.3-1-0' ),
							  ( '1.3-2-0', '1.3-2-0' ),
							  ( '2.0-0-0', '2.0-0-0' ) )

	def choices( self ):
		return self._choices


class SoftMonStateSelected( umc.StaticSelection ):
	def __init__( self, system_versions = None ):
		umc.StaticSelection.__init__( self, '' )
		self._choices = ( ( 'key-1', _('Install') ),
						  ( 'key-2', _('Hold') ),
						  ( 'key-3', _('DeInstall') ),
						  ( 'key-4', _('Purge') ),
						  ( 'key-0', _('Unknown') )
						  )

	def choices( self ):
		return self._choices

class SoftMonStateInstalled( umc.StaticSelection ):
	def __init__( self, system_versions = None ):
		umc.StaticSelection.__init__( self, '' )
		self._choices = ( ( 'key-0', _('Ok') ),
						  ( 'key-1', _('ReInstReq') ),
						  ( 'key-2', _('Hold') ),
						  ( 'key-3', _('HoldReInstReq') )
						  )

	def choices( self ):
		return self._choices


class SoftMonStateCurrent( umc.StaticSelection ):
	def __init__( self, system_versions = None ):
		umc.StaticSelection.__init__( self, '' )
		self._choices = ( ( 'key-0', _('NotInstalled') ),
						  ( 'key-1', _('UnPacked') ),
						  ( 'key-2', _('HalfConfigured') ),
						  ( 'key-3', _('UnInstalled') ),
						  ( 'key-4', _('HalfInstalled') ),
						  ( 'key-5', _('ConfigFiles') ),
						  ( 'key-6', _('Installed') )
						  )

	def choices( self ):
		return self._choices


class SoftMonSystemSearchKey( umc.StaticSelection ):
	def __init__( self ):
		umc.StaticSelection.__init__( self, _( 'Search filter' ) )
		self._choices = []

	def choices( self ):
		return ( ( 'name', _( 'System name' ) ),
				 ( 'role', _( 'System role' ) ),
				 ( 'ucs_version', _( 'UCS version' ) ) )

class SoftMonPackageSearchKey( umc.StaticSelection ):
	def __init__( self ):
		umc.StaticSelection.__init__( self, _( 'Search filter' ) )
		self._choices = []

	def choices( self ):
		return ( ( 'pkg_name', _( 'Package name' ) ),
				 ( 'pkg_version', _( 'Package version' ) ),
				 ( 'selected_state', _( 'Package selection state' ) ),
				 ( 'installed_state', _( 'Installation state' ) ),
				 ( 'current_state', _( 'Current package state' ) ),
				 ( 'ucs_version', _( 'UCS version' ) ) )


system_filter_types = { 'name' : umc.String( _( 'Text' ) ),
						'role' : umc.SystemRoleSelection( _( 'System role' ) ),
						'ucs_version' : SoftMonSystemVersions() }

umcd.copy( umc.StaticSelection, SoftMonSystemSearchKey )
umcd.copy( umc.StaticSelection, SoftMonPackageSearchKey )
umcd.copy( umc.StaticSelection, SoftMonSearchOperator )
umcd.copy( umc.StaticSelection, SoftMonSystemVersions )
umcd.copy( umc.StaticSelection, SoftMonStateSelected )
umcd.copy( umc.StaticSelection, SoftMonStateInstalled )
umcd.copy( umc.StaticSelection, SoftMonStateCurrent )
