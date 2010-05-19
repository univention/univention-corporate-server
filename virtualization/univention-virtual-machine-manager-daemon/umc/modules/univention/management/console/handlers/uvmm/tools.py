#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: management of virtualization servers
#
# Copyright (C) 2010 Univention GmbH
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

import re
import math

import univention.management.console.dialog as umcd

def percentage( percent, label = None, width = 100 ):
	return umcd.Progressbar( percent, label = label, attributes = { 'width' : '%dpx' % width } )

UNITS = ( 'B', 'KB', 'MB', 'GB', 'TB' )
SIZE_REGEX = re.compile( '(?P<size>[0-9.]+)(?P<unit>(%s))?' % '|'.join( UNITS ) )

def block2byte( size, block_size = 1 ):
	global UNITS
	size = long( size ) * float( block_size )
	unit = 0
	while size > 1024.0 and unit < ( len( UNITS ) - 1 ):
		size /= 1024.0
		unit += 1

	return '%.1f%s' % ( size, UNITS[ unit ] )

def byte2block( size, block_size = 1 ):
	global UNITS, SIZE_REGEX

	match = SIZE_REGEX.match( size )
	if not match:
		return 0

	grp = match.groupdict()

	size = float( grp[ 'size' ] )
	factor = 0
	if grp.has_key( 'unit' ) and grp[ 'unit' ] in UNITS:
		while UNITS[ factor ] != grp[ 'unit' ]:
			factor +=1
	size = size * math.pow( 1024, factor )

	return long( size / float( block_size ) )

