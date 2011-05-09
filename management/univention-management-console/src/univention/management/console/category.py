# -*- coding: utf-8 -*-
#
# Univention Management Console
#  UMC syntax definitions
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

import os
import re
import sys
import locales
import xml.parsers.expat

from tools import ElementTree
import verify

_ = locales.Translation( 'univention.management.console' ).translate

class XML_Definition( ElementTree ):
	'''Definition of a category class'''
	def __init__( self, root = None, filename = None ):
		ElementTree.__init__( self, element = root, file = filename )

	@property
	def name( self ):
		return self.get_localized( 'name' )

	@property
	def id( self ):
		return self._root.get( 'id' )

	def json( self ):
		return { 'id' : self.id, 'name' : self.name }

class Manager( dict ):
	'''Manager of all available categories'''

	DIRECTORY = os.path.join( sys.prefix, 'share/univention-management-console/categories' )
	def __init__( self ):
		dict.__init__( self )
		self.load()

	def all( self ):
		return map( lambda x: x.json(), self.values() )

	def load( self ):
		self.clear()
		for filename in os.listdir( Manager.DIRECTORY ):
			if not filename.endswith( '.xml' ):
				continue
			try:
				definitions = ElementTree( file = os.path.join( Manager.DIRECTORY, filename ) )
				for category_elem in definitions.findall( 'categories/category' ):
					category = XML_Definition( root = category_elem )
					self[ category.id ] = category
			except xml.parsers.expat.ExpatError:
				continue
