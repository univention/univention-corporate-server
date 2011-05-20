#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: manages a CUPS server
#
# Copyright 2006-2011 Univention GmbH
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
short_description = _( 'Printer administration' )
long_description = _( 'Manages printers controlled by the CUPS server' )
categories = [ 'all' ]

command_description = {
	'cups/list': umch.command(
		short_description = _( 'List printers' ),
		long_description = _( 'Lists all available printers' ),
		method = 'cups_list',
		values = { 'key' : _types.searchkey,
				   'filter' : _types.filter },
		startup = True,
		priority = 100,
		caching = True
	),
	'cups/printer/show': umch.command(
		short_description = _( 'Show printer' ),
		method = 'cups_printer_show',
		values = { 'printer' : _types.printername },
	),
	'cups/printer/quota/list': umch.command(
		short_description = _( 'Printer quotas' ),
		long_description = _( 'Show printer quotas' ),
		method = 'cups_printer_quota_list',
		values = { 'printer' : _types.printername },
	),
	'cups/printer/quota/show': umch.command(
		short_description = _( 'Show quota' ),
		method = 'cups_printer_quota_show',
		values = { 'printer' : _types.printername },
	),
	'cups/printer/disable': umch.command(
		short_description = _( 'Deactivates printers' ),
		method = 'cups_printer_disable',
		values = { 'printers' : _types.printers },
	),
	'cups/printer/enable': umch.command(
		short_description = _( 'Activates printers' ),
		method = 'cups_printer_enable',
		values = { 'printers' : _types.printers }
	),
	'cups/quota/user/show': umch.command(
		short_description = _( 'User print quota settings' ),
		long_description = _( 'Show print quota settings for a user' ),
		method = 'cups_quota_user_show',
		values = { 'user' : _types.user,
					'printer' : _types.printername },
	),
	'cups/quota/user/set': umch.command(
		short_description = _( 'Set/modify user print quota' ),
		long_description = _( 'Modify printer quota settings for a user' ),
		method = 'cups_quota_user_set',
		values = { 'user' : _types.user,
					'printer' : _types.printername,
					'softlimit' : _types.pagesoftlimit,
					'hardlimit' : _types.pagehardlimit },
	),
	'cups/quota/user/reset': umch.command(
		short_description = _( 'Reset user print quota' ),
		long_description = _( 'Reset printer quota for a user' ),
		method = 'cups_quota_user_reset',
		values = { 'user' : _types.user,
					'printer': _types.printername },
	),
	'cups/job/cancel': umch.command(
		short_description = _( 'Cancel print jobs' ),
		long_description = _( 'Cancels all given print jobs.' ),
		method = 'cups_job_cancel',
		values = { 'jobs' : _types.jobs }
	),
	'cups/job/move': umch.command(
		short_description = _( 'Move print jobs' ),
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
		presult = umct.run_process( '/usr/bin/lpstat -l -p', timeout = 10000, shell = True, output = True )
		buffer = presult['stdout'].readlines()
		ud.debug( ud.ADMIN, ud.INFO, 'CUPS.list: buffer1: %s' % buffer )

		filter = object.options.get( 'filter', '*' )
		key = object.options.get( 'key', 'printer' )
		printers = tools.parse_lpstat_l( buffer, filter, key )

		presult = umct.run_process( '/usr/bin/lpstat -v', timeout = 10000, shell = True, output = True )
		buffer = presult['stdout'].readlines()
		ud.debug( ud.ADMIN, ud.INFO, 'CUPS.list: buffer2: %s' % buffer )

		printers = tools.parse_lpstat_v( buffer, printers )
		self.finished( object.id(), ( filter, key, printers ) )

# root@master30:/usr/share/univention-management-console/www# lpstat -v
# device for fooprn: cupspykota:parallel:/dev/lp0
# device for tintenkleckser: parallel:/dev/lp0

