#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  quota module: show quota information for a user
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

import os
import re

import tools
import fstab

import notifier

import univention.management.console as umc
import univention.management.console.dialog as umcd
import univention.management.console.protocol as umcp

import univention.debug as ud

_ = umc.Translation( 'univention.management.console.handlers.quota' ).translate

class Commands( object ):
	def quota_user_show( self, object ):
		if object.options.has_key( 'partition' ) and \
		   object.options.has_key( 'user' ):
			tools.repquota( object.options[ 'partition' ],
							notifier.Callback( self._quota_user_show, object ),
							object.options[ 'user' ] )
		else:
			self._quota_user_show( 0, 0, None, object )

	def _quota_user_show( self, pid, status, result, object ):
		devs = fstab.File()
		lst = umcd.List()

		# check user and partition option for existance
		username = None
		if object.options.has_key( 'user' ) and object.options[ 'user' ]:
			username = object.options[ 'user' ]
		device = None
		if object.options.has_key( 'partition' ) and \
			   object.options[ 'partition' ]:
			device = devs.find( spec = object.options[ 'partition' ] )

		# quota options
		result = tools.repquota_parse( device, result )
		if not result:
			user_quota = tools.UserQuota( device, username, '0', '0', '0', None,
											'0', '0', '0', None  )
		else:
			user_quota = result[ 0 ]

		self.finished( object.id(), user_quota )

	def quota_user_set( self, object ):
		ud.debug( ud.ADMIN, ud.INFO, "quota_user_set: %s" % str( object.options ) )
		tools.setquota( object.options[ 'partition' ], object.options[ 'user' ],
						tools.byte2block( object.options[ 'block_soft' ] ),
						tools.byte2block( object.options[ 'block_hard' ] ),
						object.options[ 'file_soft' ], object.options[ 'file_hard' ],
						notifier.Callback( self._quota_user_set, object ) )

	def _quota_user_set( self, pid, status, result, object ):
		if not status:
			text = _( 'Successfully set quota settings' )
			self.finished( object.id(), [], report = text, success = True )
		else:
			text = _( 'Failed to modify quota settings for user %(user)s on partition %(partition)s' ) % \
				   object.options
			self.finished( object.id(), [], report = text, success = False )

	def quota_user_remove( self, object ):
		if object.options[ 'user' ]:
			user = object.options[ 'user' ].pop( 0 )
			tools.setquota( object.options[ 'partition' ], user, 0, 0, 0, 0,
							notifier.Callback( self._quota_user_remove, object ) )
		else:
			self.finished( object.id(), [] )

	def _quota_user_remove( self, pid, status, result, object ):
		if not status:
			if object.options[ 'user' ]:
				user = object.options[ 'user' ].pop( 0 )
				tools.setquota( object.options[ 'partition' ], user,
								0, 0, 0, 0, notifier.Callback( self._quota_user_remove, object ) )
				return
			text = _( 'Successfully removed quota settings' )
			self.finished( object.id(), [], report = text, success = True )
		else:
			text = _( 'Failed to remove quota settings for user %(user)s on partition %(partition)s' ) % \
				   object.options
			self.finished( object.id(), [], report = text, success = False )
