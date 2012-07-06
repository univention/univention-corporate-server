#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention Installer
#  helper function for retrieving and setting repository information
#
# Copyright 2009-2012 Univention GmbH
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

import os

def get_first_version():
	version = None
	ui = open( '/mnt/.univention_install' )
	for line in ui.readlines():
		if line.startswith( 'VERSION=' ):
			version = line[ line.find( '=' ) + 1 : ].strip()
			break

	ui.close()
	return version

def get_package_list( pkglist ):
	version = get_first_version()
	# old repository structure
	if os.path.isdir( '/mnt/packages' ):
		if os.path.exists('/mnt/packages/Packages'):
			fp = open('/mnt/packages/Packages', 'r')
			for line in fp.readlines():
				if line.startswith('Package: '):
					pkglist.append(line.split(' ')[1].strip('\r\n'))
			fp.close()
		else:
			pkglist = 'INVALID'
	elif os.path.isdir( '/mnt/mirror/%s/maintained/%s-0/' % ( version, version ) ):
		for arch in ( 'i386', 'amd64', 'all' ):
			filename = '/mnt/mirror/%s/maintained/%s-0/%s/Packages' % ( version, version, arch )
			if not os.path.isfile( filename ):
				continue
			fp = open( filename )
			for line in fp.readlines():
				if line.startswith('Package: '):
					pkglist.append(line.split(' ')[1].strip('\r\n'))
			fp.close()
	else:
		pkglist = 'INVALID'

def create_sources_list():
	srclist = open( '/etc/apt/sources.list', 'w' )
	lines = []
	# old repository structure
	if os.path.isdir( '/mnt/packages' ):
		lines.append( 'deb file:/mnt/packages/ ./' )
	else:
		version = get_first_version()
		for arch in ( 'i386', 'amd64', 'all' ):
			if os.path.exists( '/mnt/%s/maintained/%s-0/%s' % ( version, version, arch ) ):
				lines.append( 'deb file:/mnt/%s/maintained/ %s-0/%s/ ' % ( version, version, arch ) )

	srclist.write( '\n'.join( lines ) )
	srclist.close()
