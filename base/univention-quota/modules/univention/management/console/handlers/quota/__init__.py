#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: manages quota support for locale hard drives
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
import univention.management.console.handlers as umch
import univention.management.console.dialog as umcd
import univention.management.console.tools as umct
import univention.management.console.protocol as umcp

import univention_baseconfig

import notifier.popen
import notifier.threads

import df
import fstab
import mtab
import tools
import partition
import user

import _revamp
import _types

import univention.debug as ud

_ = umc.Translation( 'univention.management.console.handlers.quota' ).translate

icon = 'quota/module'
short_description = _( 'Filesystem Quotas' )
long_description = _( 'Set, unset and modify filesystem quota' )
categories = [ 'all' ]

command_description = {
	'quota/list': umch.command(
		short_description = _( 'List Partitions' ),
		long_description = _( 'List available partitions' ),
		method = 'quota_list',
		values = {},
		startup = True,
		priority = 100
	),
	'quota/partition/show': umch.command(
		short_description = _( 'Show Partition' ),
		long_description = _( 'Show details to one selected partition'),
		method = 'quota_partition_show',
		values = { 'partition' : _types.partition },
	),
	'quota/partition/activate': umch.command(
		short_description = _( 'Activate Quota-Support' ),
		long_description = _( 'Activate quota support for a partition' ),
		method = 'quota_partition_activate',
		values = { 'partition' : _types.partition },
	),
	'quota/partition/deactivate': umch.command(
		short_description = _( 'Deactivate Quota-Support' ),
		long_description = _( 'Deactivate quota support for a partition' ),
		method = 'quota_partition_deactivate',
		values = { 'partition' : _types.partition },
	),
	'quota/user/set': umch.command(
		short_description = _( 'Set/Modify User Settings' ),
		long_description = _( 'Modify quota settings for a user' ),
		method = 'quota_user_set',
		values = { 'user' : _types.user,
				   'partition' : _types.partition,
				   'block_soft' : _types.bsoft,
				   'block_hard' : _types.bhard,
				   'file_soft' : _types.fsoft,
				   'file_hard' : _types.fhard },
	),
	'quota/user/remove': umch.command(
		short_description = _( "Delete User's Quota Settings" ),
		long_description = _( "Delete the user's quota settings for a specific partition" ),
		method = 'quota_user_remove',
		values = { 'user' : _types.user,
				   'partition' : _types.partition },
	),
	'quota/user/show': umch.command(
		short_description = _( 'User Settings' ),
		long_description = _( 'Show detailed quota information for a user' ),
		method = 'quota_user_show',
		values = { 'user' : _types.user,
				   'partition' : _types.partition },
	),
}

class Partition( object ):
	def __init__( self, params, quota_written, quota_used, mounted, size, free ):
		self.params = params
		self.quota_written = quota_written
		self.quota_used = quota_used
		self.mounted = mounted
		self.size = size
		self.free = free

class handler( umch.simpleHandler, _revamp.Web, partition.Commands,
			   user.Commands ):
	def __init__( self ):
		global command_description
		umch.simpleHandler.__init__( self, command_description )
		_revamp.Web.__init__( self )
		partition.Commands.__init__( self )
		user.Commands.__init__( self )

	def quota_list( self, object ):
		fs = fstab.File()
		mt = mtab.File()
		partitions = fs.get( [ 'xfs', 'ext3', 'ext2' ], False )

		result = []

		for part in partitions:
			mounted = mt.get( part.spec )
			written = ( 'usrquota' in part.options )
			if mounted:
				info = df.DeviceInfo( part.mount_point )
				size = tools.block2byte( info.size(), 1 )
				free = tools.block2byte( info.free(), 1 )
				used = ( 'usrquota' in mounted.options )
				ud.debug( ud.ADMIN, ud.INFO, "%s: used: %s, written: %s" % ( part.mount_point, used, written ) )
			else:
				size = '-'
				free = '-'
			result.append( Partition( part, written, used, mounted, size, free ) )

		self.finished( object.id(), result )
