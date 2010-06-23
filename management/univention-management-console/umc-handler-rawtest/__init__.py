#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: system stop/reboot
#
# Copyright 2008-2010 Univention GmbH
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
import univention.management.console.handlers as umch
import univention.management.console.dialog as umcd
import univention.management.console.tools as umct

import univention.debug as ud

import os

import notifier.popen

import univention.config_registry as ucr
import univention.service_info as usi
import _revamp


_ = umc.Translation( 'univention.management.console.handlers.reboot' ).translate

name = 'raw'
icon = 'raw/exit'
short_description = _( 'RAW DATA TEST' )
long_description = _( 'RAW DATA TEST' )
categories = [ 'system', 'all' ]

class Choice( umc.StaticSelection ):
	def __init__( self ):
		umc.StaticSelection.__init__( self, _( 'Choice' ) )
	
	def choices( self ):
		return ( ('reboot', _( 'Reboot' ) ),('stop',  _( 'Stop' ) ) )

umcd.copy( umc.StaticSelection, Choice )

command_description = {
	'raw/test/cmd': umch.command(
		short_description = _( 'Return specific file' ),
		method = 'raw_do',
		values = { 'file': umc.String( _( 'Filename' ) ),
				   'type': umc.String( _( 'Filetype' ) )},
		startup = False,
		),
	'raw/test/startup': umch.command(
		short_description = _( 'Return specific file' ),
		method = 'raw_startup',
		values = { 'file': umc.String( _( 'Filename' ) ),
				   'type': umc.String( _( 'Filetype' ) )},
		startup = True,
		),
}

class handler( umch.simpleHandler, _revamp.Web ):
	def __init__( self ):
		global command_description
		umch.simpleHandler.__init__( self, command_description )
	def raw_do( self, object ):
		self.finished( object.id(), None)
	def raw_startup( self, object ):
		self.finished( object.id(), None)
