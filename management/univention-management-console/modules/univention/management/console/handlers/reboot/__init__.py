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

import subprocess

import notifier.popen

import univention.config_registry as ucr
import univention.service_info as usi
import _revamp


_ = umc.Translation( 'univention.management.console.handlers.reboot' ).translate

name = 'reboot'
icon = 'reboot/exit'
short_description = _( 'Reboot' )
long_description = _( 'System reboot or shutdown' )
categories = [ 'system', 'all' ]

class Choice( umc.StaticSelection ):
	def __init__( self ):
		umc.StaticSelection.__init__( self, _( 'Action' ) )
	
	def choices( self ):
		return ( ('reboot', _( 'Reboot' ) ),('stop',  _( 'Stop' ) ) )

umcd.copy( umc.StaticSelection, Choice )

command_description = {
	'reboot/do': umch.command(
		short_description = _( 'System reboot or shutdown' ),
		method = 'reboot_do',
		values = { 'action': Choice(),'message': umc.String( _( 'Reason for this reboot/shutdown' ) ) },
		startup = True,
		),
}
class handler( umch.simpleHandler, _revamp.Web ):
	def __init__( self ):
		global command_description
		umch.simpleHandler.__init__( self, command_description )
	def reboot_do( self, object ):
		if not object.incomplete:
			do=""
			if object.options['action'] == "stop":
				do="h"
				target=_( 'The system is going down for system halt NOW with following message: ' )
			elif object.options['action'] == "reboot":
				do="r"
				target=_( 'The system is going down for reboot NOW with following message: ' )

			object.options['message']= target + object.options['message']
			# shellescaped_message = object.options['message'].replace('"', '\\"')

			self.finished( object.id(), object.options['message'] )
			ret = subprocess.call( ( 'logger', '-f', '/var/log/syslog', '-t', 'UMC', str(object.options[ 'message' ]) ) )
			if not ret:
				subprocess.call( ( 'shutdown', '-%s' % do, 'now', str(object.options[ 'message' ]) ) )

		else:	
			self.finished( object.id(), None)
