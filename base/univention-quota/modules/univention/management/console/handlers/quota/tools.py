#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  quota module: modify quota settings
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
import math

import notifier.popen
import univention.debug as ud
import univention.management.console as umc

import fstab

_ = umc.Translation( 'univention.management.console.handlers.quota' ).translate

class UserQuota( object ):
	def __init__( self, partition, user, bused, bsoft, bhard, btime,
				  fused, fsoft, fhard, ftime ):
		self.partition = partition
		self.user = user
		self.bused = bused
		self.bsoft = bsoft
		self.bhard = bhard

		self.fused = fused
		self.fsoft = fsoft
		self.fhard = fhard

		self.set_time( 'btime', btime )
		self.set_time( 'ftime', ftime )

	def set_time( self, time, value ):
		if not value:
			self.__dict__[ time ] = '-'
		elif value == 'none':
			self.__dict__[ time ] = _( 'Expired' )
		elif value.endswith( 'days' ):
			self.__dict__[ time ] = _( '%s Days' ) % value[ : -4 ]
		elif ':' in value:
			self.__dict__[ time ] = value

def repquota( partition, callback, user = None ):
	args = ''

	# find filesystem type
	fs = fstab.File()
	part = fs.find( spec = partition )
	if part.type == 'xfs':
		args += '-F xfs '

	# grep a single user
	if user:
		args += "| /bin/grep '^%s '" % user
	# -C == do not try to resolve all users at once
	# -v == verbose
	cmd = '/usr/sbin/repquota -C -v %s %s' % ( partition, args )
	ud.debug( ud.ADMIN, ud.PROCESS, 'run: %s' % cmd )
	proc = notifier.popen.Shell( cmd, stdout = True )
	proc.signal_connect( 'finished', callback )
	proc.start()

def repquota_parse( partition, output ):
	result = []
	if not output:
		return result

	regex = re.compile( '(?P<user>[^ ]*) *[-+]+ *(?P<bused>[0-9]*) *(?P<bsoft>[0-9]*) *(?P<bhard>[0-9]*) *((?P<btime>([0-9]*days|none|[0-9]{2}:[0-9]{2})))? *(?P<fused>[0-9]*) *(?P<fsoft>[0-9]*) *(?P<fhard>[0-9]*) *((?P<ftime>([0-9]*days|none|[0-9]{2}:[0-9]{2})))?' )
	for line in output:
		matches = regex.match( line )
		if not matches:
			break
		grp = matches.groupdict()
		if not grp[ 'user' ] or grp[ 'user' ] == 'root':
			continue
		info = UserQuota( partition, grp[ 'user' ], grp[ 'bused' ], grp[ 'bsoft' ],
						  grp[ 'bhard' ], grp[ 'btime' ], grp[ 'fused' ], grp[ 'fsoft' ],
						  grp[ 'fhard' ], grp[ 'ftime' ] )
		result.append( info )
	return result

def setquota( partition, user, bsoft, bhard, fsoft, fhard, callback ):
	cmd = '/usr/sbin/setquota -u %s %d %d %d %d %s' % ( user, int( bsoft ), int( bhard ),
														int( fsoft ), int( fhard ), partition )
	ud.debug( ud.ADMIN, ud.PROCESS, 'run: %s' % cmd )
	proc = notifier.popen.RunIt( cmd )
	proc.signal_connect( 'finished', callback )
	proc.start()

def activate_quota( partition, activate, callback ):
	if not isinstance( partition, list ):
		partitions = [ partition ]
	else:
		partitions = partition
	func = notifier.Callback( _do_activate_quota, partitions, activate )
	thread = notifier.threads.Simple( 'quota', func, callback )
	thread.run()

def _do_activate_quota( partitions, activate ):
	fs = fstab.File()
	failed = {}
	for device in partitions:
		part = fs.find( spec = device )
		if not part:
			failed[ device ] = ( False, _( 'Device could not be found' ) )
			continue
		if activate:
			if not 'usrquota' in part.options:
				part.options.append( 'usrquota' )
				fs.save()
			else:
				# operation successful: nothing to be done
				continue
			if part.type == 'xfs':
				status, text = _activate_quota_xfs( part )
			elif part.type in ( 'ext2', 'ext3' ):
				status, text = _activate_quota_ext( part, True )
			failed[ device ] = ( status, text )
		else:
			if not 'usrquota' in part.options:
				continue
			else:
				part.options.remove( 'usrquota' )
				fs.save()
			if part.type == 'xfs':
				status, text = _activate_quota_xfs( part )
			elif part.type in ( 'ext2', 'ext3' ):
				status, text = _activate_quota_ext( part, True )
			failed[ device ] = ( status, text )

	return failed

def _activate_quota_xfs( partition ):
	if os.system( 'umount %s' % partition.spec ):
		return ( False, _( 'Unmounting the partition has failed' ) )
	if os.system( 'mount %s' % partition.spec ):
		return ( False, _( 'Mounting the partition has failed' ) )
	if os.system( '/etc/init.d/quota restart' ):
		return ( False, _( 'Restarting the quota services has failed' ) )

	return ( True, _( 'Operation was successful' ) )

def _activate_quota_ext( partition, create ):
	if os.system( 'mount -o remount %s' % partition.spec ):
		return ( False, _( 'Remounting the partition has failed' ) )
	if create:
		if os.system( '/sbin/quotacheck -u %s' % partition.mount_point ):
			return ( False,
					 _( 'Generating the quota information file failed' ) )
	if os.system( '/etc/init.d/quota restart' ):
		return ( False, _( 'Restarting the quota services has failed' ) )

	return ( True, _( 'Operation was successful' ) )

_units = ( 'B', 'KB', 'MB', 'GB', 'TB' )
_size_regex = re.compile( '(?P<size>[0-9.]+)(?P<unit>(B|KB|MB|GB|TB))?' )

def block2byte( size, block_size = 1024 ):
	global _units
	size = long( size ) * float( block_size )
	unit = 0
	while size > 1024.0 and unit < ( len( _units ) - 1 ) :
		size /= 1024.0
		unit += 1

	return '%.1f%s' % ( size, _units[ unit ] )

def byte2block( size, block_size = 1024 ):
	global _units, _size_regex

	match = _size_regex.match( size )
	if not match:
		return ''

	grp = match.groupdict()

	size = float( grp[ 'size' ] )
	factor = 0
	if grp.has_key( 'unit' ) and grp[ 'unit' ] in _units:
		while _units[ factor ] != grp[ 'unit' ]:
			factor +=1
	size = size * math.pow( 1024, factor )

	return long( size / float( block_size ) )
