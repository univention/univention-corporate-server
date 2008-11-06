#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: manages a CUPS server
#
# Copyright (C) 2006, 2007 Univention GmbH
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
import univention.management.console.categories as umcc
import univention.management.console.protocol as umcp
import univention.management.console.handlers as umch
import univention.management.console.dialog as umcd
import univention.management.console.tools as umct

import univention.debug as ud

import notifier.popen

import _job
import _printer
import _revamp
import _types
import tools

_ = umc.Translation( 'univention.management.console.handlers.cups' ).translate

icon = 'cups/module'
short_description = _( 'Printer Administration' )
long_description = _( 'Manages printers controlled by the CUPS server' )
categories = [ 'all' ]

command_description = {
	'cups/list': umch.command(
		short_description = _( 'List Printers' ),
		long_description = _( 'Lists all available printers' ),
		method = 'cups_list',
		values = { 'key' : _types.searchkey,
				   'filter' : _types.filter },
		startup = True,
		priority = 100,
		caching = True
	),
	'cups/printer/show': umch.command(
		short_description = _( 'Show Printer' ),
		method = 'cups_printer_show',
		values = { 'printer' : _types.printername },
	),
	'cups/printer/quota/list': umch.command(
		short_description = _( 'Printer Quotas' ),
		long_description = _( 'Show Printer Quotas' ),
		method = 'cups_printer_quota_list',
		values = { 'printer' : _types.printername },
	),
	'cups/printer/quota/show': umch.command(
		short_description = _( 'Show Quota' ),
		method = 'cups_printer_quota_show',
		values = { 'printer' : _types.printername },
	),
	'cups/printer/disable': umch.command(
		short_description = _( 'Deactivates Printers' ),
		method = 'cups_printer_disable',
		values = { 'printers' : _types.printers },
	),
	'cups/printer/enable': umch.command(
		short_description = _( 'Activates Printers' ),
		method = 'cups_printer_enable',
		values = { 'printers' : _types.printers }
	),
	'cups/quota/user/show': umch.command(
		short_description = _( 'User Print Quota Settings' ),
		long_description = _( 'Show print quota settings for a user' ),
		method = 'cups_quota_user_show',
		values = { 'user' : _types.user,
					'printer' : _types.printername },
	),
	'cups/quota/user/set': umch.command(
		short_description = _( 'Set/Modify User Print Quota' ),
		long_description = _( 'Modify printer quota settings for a user' ),
		method = 'cups_quota_user_set',
		values = { 'user' : _types.user,
					'printer' : _types.printername,
					'softlimit' : _types.pagesoftlimit,
					'hardlimit' : _types.pagehardlimit },
	),
	'cups/quota/user/reset': umch.command(
		short_description = _( 'Reset User Print Quota' ),
		long_description = _( 'reset printer quota for a user' ),
		method = 'cups_quota_user_reset',
		values = { 'user' : _types.user,
					'printer': _types.printername },
	),
	'cups/job/cancel': umch.command(
		short_description = _( 'Cancel Print Jobs' ),
		long_description = _( 'Cancels all given print jobs.' ),
		method = 'cups_job_cancel',
		values = { 'jobs' : _types.jobs }
	),
	'cups/job/move': umch.command(
		short_description = _( 'Move Print Jobs' ),
		long_description = _( 'Moves a list of print jobs from one printer to another.' ),
		method = 'cups_job_move',
		values = { 'source': _types.printername,
					'jobs' : _types.jobs,
					'destination' : _types.printername }
	),
}

class handler( umch.simpleHandler, _revamp.Web, _printer.Commands,
				 _job.Commands ):
	def __init__( self ):
		global command_description
		umch.simpleHandler.__init__( self, command_description )
		_revamp.Web.__init__( self )
		_printer.Commands.__init__( self )
		_job.Commands.__init__( self )

	def cups_list( self, object ):
		proc = notifier.popen.RunIt( '/usr/bin/lpstat -l -p', stdout = True )
		cb = notifier.Callback( self._cups_list_return, object )
		proc.signal_connect( 'finished', cb )
		proc.start()

	def _cups_list_return( self, pid, status, buffer, object ):
		filter = object.options.get( 'filter', '*' )
		key = object.options.get( 'key', 'printer' )
		printers = tools.parse_lpstat_l( buffer, filter, key )

		proc = notifier.popen.RunIt( '/usr/bin/lpstat -v', stdout = True )
		cb = notifier.Callback( self._cups_list_return2, object, filter, key, printers )
		proc.signal_connect( 'finished', cb )
		proc.start()

# root@master30:/usr/share/univention-management-console/www# lpstat -v
# device for fooprn: cupspykota:parallel:/dev/lp0
# device for tintenkleckser: parallel:/dev/lp0

	def _cups_list_return2( self, pid, status, buffer, object, filter, key, printers ):
		printers = tools.parse_lpstat_v( buffer, printers )
		self.finished( object.id(), ( filter, key, printers ) )
