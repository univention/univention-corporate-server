#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  class representing an image with a UMCP dialog
#
# Copyright (C) 2006-2009 Univention GmbH
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

	def get_image( self ):
		return umct.image_get( self.__tag, self.__size )

class ImageURL( base.Element ):
	def __init__( self, url = '', attributes = {} ):
		self.__url = url

	def get_image( self ):
		return self.__url

ImageTypes = ( type( Image() ), type( ImageURL() ) )
