#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: join into the domain
#
# Copyright 2007-2010 Univention GmbH
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
import univention.management.console.handlers as umch
import univention.management.console.dialog as umcd
import univention.management.console.tools as umct

import os

_join_dir = '/usr/lib/univention-install'
_join_index = '.index.txt'

class Script( object ):
	def __init__( self, filename, current_version = None, success = None ):
		self.filename = filename
		self.current_version = current_version
		self.last_version = None
		self.success = success

def _read_script( script ):
	fd = open( os.path.join( _join_dir, script.filename ), 'r' )
	for line in fd:
		if line.startswith( 'VERSION' ):
			v = line.split( '=', 1 )
			if len( v ) == 2:
				curversion = v[ 1 ].strip(' \r\n\t\'"')
				if curversion.isdigit():
					script.current_version = curversion
					break
	fd.close()

def _read_index( scripts ):
	global _join_dir, _join_index

	if not os.path.exists( os.path.join( _join_dir, _join_index ) ):
		return 
	fd = open( os.path.join( _join_dir, _join_index ), 'r' )
	for line in fd:
		args = line[ : -1 ].split( ' ', 2 )

		name = args[ 0 ]
		script = None
		for s in scripts:
			if s.filename.endswith( '%s.inst' % name ):
				script = s
				break
		if not script:
			continue
		# old index line?
		if len( args ) == 2:
			status = args[ 1 ]
			script.last_version = ''
		elif len( args ) == 3:
			script.last_version = args[ 1 ][ 1 : ]
			status = args[ 2 ]
		if status == 'successful':
			script.success = True
		else:
			script.success = False

def read_status():
	global _join_dir, _join_index

	scripts = []
	files = os.listdir( _join_dir )
	files.sort()
	for item in files:
		if item == _join_index or not item.endswith( '.inst' ):
			continue
		script = Script( item )
		_read_script( script )
		scripts.append( script )

	_read_index( scripts )

	return ( os.path.isfile( '/var/univention-join/joined' ), scripts )
