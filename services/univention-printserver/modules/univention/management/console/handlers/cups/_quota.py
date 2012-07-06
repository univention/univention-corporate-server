#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  cups module: helper functions for print job management
#
# Copyright 2006-2012 Univention GmbH
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
import univention.management.console.dialog as umcd
import univention.management.console.protocol as umcp

import univention.debug as ud

import notifier.popen

import tools

_ = umc.Translation( 'univention.management.console.handlers.cups' ).translate

class Commands( object ):
	def cups_printer_quota_show( self, object ):
		if object.incomplete:
			self.finished( object.id(), [] )
			return

		cmd = '/usr/bin/lpstat -o %s' % object.options[ 'printer' ]
		ud.debug( ud.ADMIN, ud.INFO, 'CUPS.show: command: %s' % cmd )
		proc = notifier.popen.Shell( cmd, stdout = True )
		cb = notifier.Callback( self._cups_printer_show_return, object )
		proc.signal_connect( 'finished', cb )
		proc.start()

	def _cups_printer_show_return( self, pid, status, buffer, object ):
		jobs = tools.parse_lpstat_o( buffer )
		self.finished( object.id(), jobs )

	def cups_printer_enable( self, object ):
		cmd = '/usr/bin/univention-cups-enable %s' % ' '.join( object.options[ 'printers' ] )
		ud.debug( ud.ADMIN, ud.INFO, 'CUPS.enable: command: %s' % cmd )
		proc = notifier.popen.Shell( cmd, stdout = False )
		cb = notifier.Callback( self._cups_printer_enable_return, object )
		proc.signal_connect( 'finished', cb )
		proc.start()

	def _cups_printer_enable_return( self, pid, status, object ):
		self.finished( object.id(), [] )

	def cups_printer_disable( self, object ):
		cmd = '/usr/bin/univention-cups-disable %s' % \
			  ' '.join( object.options[ 'printers' ] )
		ud.debug( ud.ADMIN, ud.INFO, 'CUPS.enable: command: %s' % cmd )
		proc = notifier.popen.Shell( cmd, stdout = False )
		cb = notifier.Callback( self._cups_printer_disable_return, object )
		proc.signal_connect( 'finished', cb )
		proc.start()

	def _cups_printer_disable_return( self, pid, status, object ):
		self.finished( object.id(), [] )
