#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module modutils: handle kernel modules
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
import univention.management.console.handlers as umch
import univention.management.console.dialog as umcd
import univention.management.console.tools as umct

import os, re

import notifier.popen

import _revamp
import tools

import univention.debug as ud

_ = umc.Translation( 'univention.management.console.handlers.modutils' ).translate

name = 'modutils'
icon = 'modutils/module'
short_description = _( 'Kernel Modules' )
long_description = _( 'Load and Remove Kernel Modules' )
categories = [ 'all', 'system' ]

tools.get_kernel_version()
tools.get_kernel_categories()

class ModUtilsCategories( umc.StaticSelection ):
	def __init__( self ):
		umc.StaticSelection.__init__( self, _( 'Module Categories' ) )

	def choices( self ):
		lst = [ ( 'all', _( 'All' ) ) ]
		for cat in tools.get_kernel_categories():
			lst.append( ( cat, cat ) )
		return lst

class ModUtilsSearchKey( umc.StaticSelection ):
	def __init__( self ):
		umc.StaticSelection.__init__( self, _( 'Search Key' ) )
		self._choices = []

	def choices( self ):
		return ( ( 'name', _( 'Name' ) ),
				 ( 'description', _( 'Description' ) ) )

umcd.copy( umc.StaticSelection, ModUtilsCategories )
umcd.copy( umc.StaticSelection, ModUtilsSearchKey )

cats_type = ModUtilsCategories()
key_type = ModUtilsSearchKey()

command_description = {
	'modutils/search' : umch.command(
		short_description = _( 'Kernel Modules' ),
		method = 'modutils_search',
		values = { 'category': cats_type,
				   'key' : key_type,
				   'loaded' : umc.Boolean( _( 'Loaded modules only' ) ),
				   'pattern' : umc.String( _( 'Pattern' ) ) },
		startup = True,
	),
	'modutils/show' : umch.command(
		short_description = _( 'Load Kernel Modul' ),
		method = 'modutils_show',
		values = { 'module' : umc.String( _( 'Kernel Module' ) ),
				   'load' : umc.Boolean( '' ) },
	),
	'modutils/load' : umch.command(
		short_description = _( 'Load Kernel Modul' ),
		method = 'modutils_load',
		values = { 'module' : umc.String( _( 'Kernel Module' ) ),
				   'arguments' : umc.String( _( 'Modul Arguments' ), required = False ) },
	),
	'modutils/unload' : umch.command(
		short_description = _( 'Unload Kernel Modul' ),
		method = 'modutils_unload',
		values = { 'module' : umc.String( _( 'Kernel Module' ) ) },
	),
}

class handler( umch.simpleHandler, _revamp.Web ):
	def __init__( self ):
		global command_description
		umch.simpleHandler.__init__( self, command_description )

	def modutils_search( self, object ):
		if object.incomplete:
			self.finished( object.id(), None )
		else:
			ud.debug( ud.ADMIN, ud.INFO, "search for: %s" % object.options[ 'pattern' ] )
			mods = tools.get_kernel_modules( object.options[ 'category' ],
											 object.options[ 'pattern' ],
											 object.options[ 'loaded' ] )
			infos = tools.get_kernel_module_info( mods )
			self.finished( object.id(), infos )
	
	def modutils_show( self, object ):
		infos = tools.get_kernel_module_info( [ object.options[ 'module' ] ] )
		if infos:
			self.finished( object.id(), infos[ 0 ] ) 
		else:
			self.finished( object.id(), None ) 

	def modutils_load( self, object ):
		ud.debug( ud.ADMIN, ud.INFO, 'modprobe %s' % object.options[ 'module' ] )
		os.system( 'modprobe %s' % object.options[ 'module' ] )
		self.finished( object.id(), None )

	def modutils_unload( self, object ):
		ud.debug( ud.ADMIN, ud.INFO, 'rmmod -f %s' % object.options[ 'module' ] )
		os.system( 'rmmod -f %s' % object.options[ 'module' ] )
		self.finished( object.id(), None )

