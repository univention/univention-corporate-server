#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  icon loader: tries to load icon file identified by a tag and size
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

__all__ = [ 'image_get', 'image_path_append',
			'SIZE_MICROSCOPIC', 'SIZE_TINY', 'SIZE_SMALL', 'SIZE_MEDIUM',
			'SIZE_NORMAL', 'SIZE_LARGE', 'SIZE_HUGE' ]

_image_theme = 'default'
_image_prefix = '/usr/share/univention-management-console/www'
_image_pathes = [ 'themes/images', ]

SIZE_MICROSCOPIC = 8
SIZE_TINY = 12
SIZE_SMALL = 16
SIZE_MEDIUM = 24
SIZE_NORMAL = 32
SIZE_LARGE = 64
SIZE_HUGE = 92

class ImageLoader( object ):
	def __init__( self ):
		self.__cache = {}

	def load( self, tag, size = SIZE_NORMAL ):
		if not self.__cache.has_key( tag ):
			filename = self.find( tag, size )
			if filename:
				fd = open( filename, 'r' )
				data = fd.read()
				self.__cache[ tag ] = data
			else:
				return None
		return self.__cache[ tag ]

	def find( self, tag, size = SIZE_NORMAL ):
		global _image_pathes, _image_prefix, _image_theme
		for theme in [ _image_theme ]:
			for path in _image_pathes:
				f = os.path.join( _image_prefix, path, _image_theme,
								  "%dx%d" % ( size, size ), tag )
				for ext in ( 'png', 'gif', 'jpg' ):
					filename = '%s.%s' % ( f, ext )
					if os.path.isfile( filename ):
						return filename[ len( _image_prefix ) + 1 : ]

		return None

_image_loader = ImageLoader()

def image_get( tag, size = SIZE_NORMAL ):
	global _image_loader
	return _image_loader.find( tag, size )

def image_path_append( path ):
	global _image_pathes
	if not path or path[ 0 ] != '/' or not os.path.isdir( path ):
		raise Exception( 'error: image path must be an absolute path' )
	_image_pathes.append( path )
