#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  class representing an image with a UMCP dialog
#
# Copyright 2006-2010 Univention GmbH
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

import base

import univention.management.console.tools as umct

class Image( base.Element ):
	def __init__( self, tag = None, size = umct.SIZE_MEDIUM, attributes = {} ):
		base.Element.__init__( self, attributes )
		self.__tag = tag
		self.__size = size

	def __str__( self ):
		return "%s: %s" % ( base.Element.__str__( self ), self.__tag )

	def get_tag( self ):
		return self.__tag

	def get_size( self ):
		return self.__size

	def set_size( self, size ):
		self.__size = size

	def get_image( self ):
		return umct.image_get( self.__tag, self.__size )

class ImageURL( base.Element ):
	def __init__( self, url = '', attributes = {} ):
		self.__url = url

	def get_image( self ):
		return self.__url

ImageTypes = ( type( Image() ), type( ImageURL() ) )
