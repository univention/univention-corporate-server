#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: like top
#
# Copyright 2007-2010 Univention GmbH
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

import subprocess

import notifier.popen

import _revamp
import tools

_ = umc.Translation( 'univention.management.console.handlers.top' ).translate

name = 'top'
icon = 'top/module'
short_description = _( 'Process overview' )
long_description = _( 'Process overview and control' )
categories = [ 'all', 'system' ]

class TOP_Sort( umc.StaticSelection ):
	def __init__( self ):
		umc.StaticSelection.__init__( self, _( 'Sort processes' ) )

	def choices( self ):
		return ( ( 'cpu', _( 'CPU usage' ) ),
				 ( 'user', _( 'User name' ) ),
				 ( 'rssize', _( 'Resident set size' ) ),
				 ( 'vsize', _( 'Virtual size' ) ),
				 ( 'pid', _( 'Process ID' ) ) )

class TOP_Count( umc.StaticSelection ):
	def __init__( self ):
		umc.StaticSelection.__init__( self, _( 'Number of processes' ) )

	def choices( self ):
		return ( ( 'all', _( 'All' ) ), ( '10', '10' ), ( '20', '20' ), ( '50', '50' ) )

class TOP_Kill( umc.StaticSelection ):
	def __init__( self ):
		umc.StaticSelection.__init__( self, _( 'Kill signal' ) )

	def choices( self ):
		return ( ( 'kill', _( 'Force kill' ) ), ( 'term', _( 'Terminate' ) ) )

umcd.copy( umc.StaticSelection, TOP_Sort )
umcd.copy( umc.StaticSelection, TOP_Kill )
umcd.copy( umc.StaticSelection, TOP_Count )

sort_type = TOP_Sort()
kill_type = TOP_Kill()
count_type = TOP_Count()
pids_type = umc.IntegerList( _( 'Process IDs' ) )

command_description = {
	'top/view' : umch.command(
		short_description = _( 'Process overview' ),
		method = 'top_view',
		values = { 'sort': sort_type,
				   'count' : count_type },
		startup = True,
	),
	'top/kill' : umch.command(
		short_description = _( 'Kill processes' ),
		method = 'top_kill',
		values = { 'pid' : pids_type,
				   'signal' : kill_type },
	),
}

class handler( umch.simpleHandler, _revamp.Web ):
	def __init__( self ):
		global command_description
		umch.simpleHandler.__init__( self, command_description )

	def top_view( self, object ):
		if not self.permitted( 'top/view', options = object.options ):
			self.finished( object.id(), {},
						   report = _( 'You are not permitted to run this command.' ),
						   success = False )
			return

		if object.incomplete:
			result = tools.run_ps( 'cpu' )
		else:
			result = tools.run_ps( object.options[ 'sort' ], object.options[ 'count' ] )

		self.finished( object.id(), result )

	def top_kill( self, object ):
		if not self.permitted( 'top/kill', options = object.options ):
			self.finished( object.id(), {},
						   report = _( 'You are not permitted to run this command.' ),
						   success = False )
			return
		cmd = [ 'kill' ]
		if object.options[ 'signal' ] == 'kill':
			cmd.append( '-9' )
		else:
			cmd.append( '-15' )

		for pid in object.options[ 'pid' ]:
			cmd.append( str( pid ) )

		subprocess.call( cmd )
		self.finished( object.id(), None )
