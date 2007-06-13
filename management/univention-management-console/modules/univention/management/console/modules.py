#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  manages the UMC modules
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

import os, sys, copy

'''
This implements the console module manager
'''

import univention.debug as ud

_manager = None

class Manager( object ):
	def __init__( self ):
		self._modules = { }
		self.__load( )
		self.__instances = { }
		self.__commands = {}
		self.__processes = []

	def __check_module( self, module ):
		return ( hasattr( module, 'icon' ) and \
				 hasattr( module, 'short_description' ) and \
				 hasattr( module, 'long_description' ) and \
				 hasattr( module, 'categories' ) )

	def get( self, name ):
		if self._modules.has_key( name ):
			return self._module[ name ].handler()

		return None

	def modules( self ):
		return self._modules.keys()

	def __load( self ):
		def _walk( root, dir, files ):
			for file in copy.copy( files ):
				p = os.path.join( dir, file )
				if not os.path.isdir( p ):
					continue
				files.remove( file )
				if not os.path.exists( os.path.join( p, '__init__.pyo' ) ) and \
					   not os.path.exists( os.path.join( p, '__init__.py' ) ):
					continue
				p = p.replace( root, '' )[ 1 : ]

				try:
					m = __import__( p )
				except Exception, e:
					import traceback
					ud.debug( ud.ADMIN, ud.ERROR,
							  "Exception occured: loading module '%s' failed: %s\n%s" % \
							  ( p, str( e ), traceback.format_exc() ) )
					continue
				if self.__check_module( m ):
					self._modules[ os.path.basename( p ) ] = m

		for p in sys.path:
			for type in ( 'handlers', 'wizards' ):
				dir = os.path.join( p, 'univention/management/console/%s' % type )
				if not os.path.isdir( dir ):
					continue
				os.path.walk( dir, _walk, p )

	def get_command_descriptions( self, hostname, acls ):

		for module in self._modules.keys():
			for command in self._modules[ module ].command_description.keys():
				if acls.is_command_allowed( command, hostname ):
					if not self.__commands.has_key( module ):
						self.__commands[ module ] = {}
						self.__commands[ module ][ 'commands' ] = {}
					self.__commands[ module ][ 'commands' ][ command ] = {}
					self.__commands[ module ][ 'commands' ][ command ][ 'short_description' ] = \
									 self._modules[ module ].command_description[ command ].short_description
					self.__commands[ module ][ 'commands' ][ command ][ 'long_description' ] = \
									 self._modules[ module ].command_description[ command ].long_description
					self.__commands[ module ][ 'commands' ][ command ][ 'startup' ] = \
									 self._modules[ module ].command_description[ command ].startup
					self.__commands[ module ][ 'commands' ][ command ][ 'caching' ] = \
									 self._modules[ module ].command_description[ command ].caching
					self.__commands[ module ][ 'commands' ][ command ][ 'priority' ] = \
									 self._modules[ module ].command_description[ command ].priority
			if self.__commands.has_key( module ):
				self.__commands[ module ][ 'icon' ] = self._modules[ module ].icon
				self.__commands[ module ][ 'short_description' ] = self._modules[ module ].short_description
				self.__commands[ module ][ 'long_description' ] = self._modules[ module ].long_description
				self.__commands[ module ][ 'categories' ] = self._modules[ module ].categories

		return self.__commands


	def search_command( self, command ):
		for module in self.__commands.keys( ):
			if self.__commands[ module ].has_key( 'commands' ):
				if self.__commands[ module ][ 'commands' ].has_key( command ):
					return module

		return None

if __name__ == '__main__':
	mgr = Manager()
