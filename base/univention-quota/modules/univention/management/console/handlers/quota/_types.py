#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: manages quota support for locale hard drives
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
import univention.management.console.dialog as umcd

_ = umc.Translation( 'univention.management.console.handlers.quota' ).translate

class ByteSize( umc.String ):
	def __init__( self, name ):
		umc.String.__init__( self, name, regex = '^[0-9.,]*(B|KB|MB|GB|TB)?$' )

	def is_valid( self, value ):
		check = umc.String.is_valid( self, value )
		if not check:
			self.error = _( 'Value is not a valid size.' )
		return check

umcd.copy( umc.String, ByteSize )

user = umc.String( _( 'User' ) )
partition = umc.String( _( 'Partition' ), regex = '^/dev/[a-z0-9/]+$' )
partitions = umc.StringList( _( 'Partitions' ) )
bsoft = ByteSize( _( 'Data Size Soft-Limit' ) )
bhard = ByteSize( _( 'Data Size Hard-Limit' ) )
fsoft = umc.Integer( _( 'Files Soft-Limit' ) )
fhard = umc.Integer( _( 'Files Hard-Limit' ) )
