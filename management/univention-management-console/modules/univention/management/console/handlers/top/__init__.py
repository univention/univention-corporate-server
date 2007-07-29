#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: like top
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

import os

import notifier.popen

import _revamp
import tools

_ = umc.Translation( 'univention.management.console.handlers.top' ).translate

name = 'top'
icon = 'top/module'
short_description = _( 'Process Overview' )
long_description = _( 'Process Overview and Control' )
categories = [ 'all', 'system' ]

class TOP_Sort( umc.StaticSelection ):
	def __init__( self ):
		umc.StaticSelection.__init__( self, _( 'Sort Processes' ) )

	def choices( self ):
		return ( ( 'cpu', _( 'CPU Usage' ) ),
				 ( 'user', _( 'Username' ) ),
				 ( 'rssize', _( 'Resident Set Size' ) ),
				 ( 'vsize', _( 'Virtual Size' ) ),
				 ( 'pid', _( 'Process ID' ) ) )

class TOP_Count( umc.StaticSelection ):
	def __init__( self ):
		umc.StaticSelection.__init__( self, _( 'Number of Processes' ) )

	def choices( self ):
		return ( ( 'all', _( 'all' ) ), ( '10', '10' ), ( '20', '20' ), ( '50', '50' ) )

class TOP_Kill( umc.StaticSelection ):
	def __init__( self ):
		umc.StaticSelection.__init__( self, _( 'Kill Signal' ) )

	def choices( self ):
		return ( ( 'kill', _( 'Force Kill' ) ), ( 'term', _( 'Terminate' ) ) )

umcd.copy( umc.StaticSelection, TOP_Sort )
umcd.copy( umc.StaticSelection, TOP_Kill )
umcd.copy( umc.StaticSelection, TOP_Count )

sort_type = TOP_Sort()
kill_type = TOP_Kill()
count_type = TOP_Count()
pids_type = umc.IntegerList( _( 'Process IDs' ) )

command_description = {
	'top/view' : umch.command(
		short_description = _( 'Process Overview' ),
		method = 'top_view',
		values = { 'sort': sort_type,
				   'count' : count_type },
		startup = True,
	),
	'top/kill' : umch.command(
		short_description = _( 'Kill Processes' ),
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
			tools.run_ps( notifier.Callback( self._top_view, object ), 'cpu' )
		else:
			tools.run_ps( notifier.Callback( self._top_view, object ), object.options[ 'sort' ],
						  object.options[ 'count' ] )

	def _top_view( self, pid, status, result, object ):
		self.finished( object.id(), tools.parse_ps( result ) )

	def top_kill( self, object ):
		if not self.permitted( 'top/kill', options = object.options ):
			self.finished( object.id(), {},
						   report = _( 'You are not permitted to run this command.' ),
						   success = False )
			return
		cmd = 'kill '
		if object.options[ 'signal' ] == 'kill':
			cmd += '-9 '
		else:
			cmd += '-15 '

		for pid in object.options[ 'pid' ]:
			cmd += '%d ' % pid

		os.system( cmd )
		self.finished( object.id(), None )
