#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  cups module: helper functions for print job management
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
