#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  quota module: handles partition related commands
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

# external
import notifier
import re

# univention
import univention.management.console as umc
import univention.management.console.dialog as umcd
import univention.management.console.protocol as umcp

# internal
import tools
import fstab
import mtab

_ = umc.Translation( 'univention.management.console.handlers.quota' ).translate

import univention.debug as ud

class Commands( object ):
	def quota_partition_show( self, object ):
		if object.incomplete:
			self.finished( object.id(), ( None, None ) )
			return

		fs = fstab.File()
		mt = mtab.File()
		part = fs.find( spec = object.options[ 'partition' ] )
		mounted = mt.get( part.spec )

		if mounted and 'usrquota' in mounted.options:
			cb = notifier.Callback( self._quota_partition_show, object.id(),
									object.options[ 'partition' ] )
			tools.repquota( object.options[ 'partition' ], cb )
		else:
			self.finished( object.id(), ( part, [] ) )

	def _quota_partition_show( self, pid, status, result, id, partition ):
		'''This function is invoked when a repquota process has died and
		there is output to parse that is restructured as UMC Dialog'''

		# general information
		devs = fstab.File()
		part = devs.find( spec = partition )

		# skip header
		try:
			header = 0
			while not result[ header ].startswith( '----' ):
				header += 1
		except:
			pass

		quotas = tools.repquota_parse( partition, result[ header + 1 : ] )

		self.finished( id, ( part, quotas ) )

	def quota_partition_activate( self, object ):
		cb = notifier.Callback( self._quota_partition_activate, object )
		tools.activate_quota( object.options[ 'partition' ], True, cb )

	def _quota_partition_activate( self, thread, result, object ):
		messages = []
		failed = False
		ud.debug( ud.ADMIN, ud.INFO, "_quota_partition_activate: %s" % str( result ) )
		for dev, info in result.items():
			success, message = info
			if not success:
				messages.append( _( 'Activating Quota for device %(device)s failed: %(message)s' ) % \
								 { 'device' : dev, 'message' : message } )
				failed = True
			else:
				messages.append( _( 'Quota-Support successfully activated for device %s' % dev ) )
		report = '\n'.join( messages )
		self.finished( object.id(), [], report, success = not failed )

	def quota_partition_deactivate( self, object ):
		cb = notifier.Callback( self._quota_partition_deactivate, object )
		tools.activate_quota( object.options[ 'partition' ], False, cb )

	def _quota_partition_deactivate( self, thread, result, object ):
		messages = []
		failed = False
		for dev, info in result.items():
			success, message = info
			if not success:
				messages.append( _( 'Deactivating Quota for device %(device)s failed: %(message)s' ) % \
								 { 'device' : dev, 'message' : message } )
				failed = True
			else:
				messages.append( _( 'Quota-Support successfully deactivated for device %s' % dev ) )
		report = '\n'.join( messages )
		self.finished( object.id(), [], report, success = not failed )
