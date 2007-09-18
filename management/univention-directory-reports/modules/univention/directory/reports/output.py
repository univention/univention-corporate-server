# -*- coding: utf-8 -*-
#
# Univention Directory Reports
#  write an interpreted token structure to a file
#
# Copyright (C) 2007 Univention GmbH
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

import codecs
import os

from tokens import *

class Output( object ):
	def __init__( self, tokens, filename = None, fd = None ):
		self._tokens = tokens
		self._filename = filename
		self._fd = fd

	def _create_dir( self ):
		if not os.path.isdir( os.path.dirname( self._filename ) ):
			os.makedir( self.path, mode = 0700 )

	def open( self ):
		if self._fd:
			return
		self._create_dir()
		self._fd = codecs.open( self._filename, 'wb', encoding = 'utf8' )

	def close( self ):
		if self._fd:
			self._fd.close()
		self._fd = None

	def write( self, tokens = [] ):
		if not self._fd:
			return
		if not tokens:
			tokens = self._tokens
		for token in tokens:
			if isinstance( token, TextToken ):
				self._fd.write( unicode( token.data, 'utf8' ) )
			elif isinstance( token, ( ResolveToken, QueryToken ) ):
				if len( token ):
					self.write( token )
			elif isinstance( token, ( AttributeToken, PolicyToken ) ):
				self._fd.write( token.value )
