#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module softmon: softeare monitor
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
import _syntax

import univention.debug as ud

_ = umc.Translation( 'univention.management.console.handlers.softmon' ).translate

name = 'softmon'
icon = 'softmon/module'
short_description = _( 'Software Monitor' )
long_description = _( 'Monitor Software Status on all Your Systems' )
categories = [ 'all', 'system' ]

filter_type = umc.MultiDictValue( _( 'Search Filters' ),
								  syntax = { 'key' : _syntax.SoftMonSystemSearchKey(),
											 'op' : _syntax.SoftMonSearchOperator(),
											 'pattern' : umc.String( '' ) } )
command_description = {
	'softmon/system/search' : umch.command(
		short_description = _( 'Search Systems' ),
		method = 'softmon_system_search',
		values = { 'filter' : filter_type },
		startup = True,
	),
	'softmon/package/search' : umch.command(
		short_description = _( 'Search Packages' ),
		method = 'softmon_package_search',
		values = { 'pattern' : umc.Boolean( _( 'Loaded modules only' ) ),
				    },
		startup = True,
	),
}

class handler( umch.simpleHandler, _revamp.Web ):
	def __init__( self ):
		global command_description
		umch.simpleHandler.__init__( self, command_description )

	def softmon_system_search( self, object ):
		if object.incomplete:
			self.finished( object.id(), None )
		else:
			ud.debug( ud.ADMIN, ud.INFO, "search for: %s" % object.options[ 'pattern' ] )
			self.finished( object.id(), [] )
