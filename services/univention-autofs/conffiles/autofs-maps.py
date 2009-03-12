#!/usr/bin/python
#
# Univention AutoFS
#  creates autofs maps
#
# Copyright (C) 2008-2009 Univention GmbH
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

import univention.config_registry as ucr

configRegistry = ucr.ConfigRegistry()
configRegistry.load()
maps = configRegistry.get( 'autofs/maps', '' )
if maps:
	known_shares = []
	for map in maps.split( ' ' ):
		prefix = 'autofs/%s/' % map
		fd = open( '/etc/auto.%s' % map, 'w' )
		for key in configRegistry.keys():
			# no relevant autofs key
			if not key.startswith( prefix ):
				continue
			share = key[ len( prefix ) : ]
			# ignore global options
			if share.startswith( 'options/' ):
				continue
			# get share name
			if share.find( '/' ) > -1:
				share = share[ : share.find( '/' ) ]
			# share already known
			if share in known_shares:
				continue

			share_prefix = '%s%s/' % ( prefix, share )
			dir = configRegistry.get( '%sdirectory' % share_prefix, None )
			opt = configRegistry.get( '%soptions' % share_prefix, None )
			src = configRegistry.get( '%ssource' % share_prefix, None )
			if not dir or not opt or not src:
				continue

			# share definition complete
			fd.write( '%s\t-%s\t%s\n' % ( dir, opt, src ) )

			known_shares.append( share )
		fd.close
