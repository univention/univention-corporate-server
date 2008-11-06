#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  quota module: reads /etc/mtab
#
# Copyright (C) 2006 Univention GmbH
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

class File( list ):
	def __init__( self, file = '/etc/mtab' ):
		list.__init__( self )
		self.__file = file
		self.load()

	def load( self ):
		fd = open( self.__file, 'r' )
		for line in fd.readlines():
			self.append( self.__parse( line ) )
		fd.close()

	def get( self, partition ):
		for entry in self:
			if entry.spec == partition:
				return entry

		return None

	def __parse( self, line ):
		fields = line.split( None, 5 )
		entry = Entry( *fields )

		return entry


class Entry( object ):
	def __init__( self, spec, mount_point, type, options,
				  dump = 0, passno = 0, comment = '' ):
		self.spec = spec.strip()
		self.mount_point = mount_point.strip()
		self.type = type.strip()
		self.options = options.split( ',' )
		self.dump = int( dump )
		self.passno = int( passno )

	def __str__( self ):
		return '%s\t%s\t%s\t%s\t%d\t%d' % \
			( self.spec, self.mount_point, self.type,  ','.join( self.options ),
			  self.dump, self.passno )

class InvalidEntry( Exception ):
	pass

if __name__ == '__main__':
	mtab = File( 'mtab' )
	print mtab.get( '/dev/sda4' )
