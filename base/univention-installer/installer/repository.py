#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Installer
#  helper function for retrieving and setting repository information
#
# Copyright (C) 2009-2009 Univention GmbH
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

def get_first_version():
	version = None
	ui = open( '/mnt/.univention_install' )
	for line in ui.readlines():
		if line.startswith( 'VERSION=' ):
			version = line[ line.find( '=' ) + 1 : ].split( '.' )
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
	elif os.path.isdir( '/mnt/%s/maintained/%s-0/' % ( version, version ) ):
		for arch in ( 'i386', 'amd64', 'all' ):
			filename = '/mnt/%s/maintained/%s-0/%s/Packages' % ( version, version, arch )
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
