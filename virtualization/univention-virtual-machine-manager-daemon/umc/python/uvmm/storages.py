#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: management of virtualization servers
#
# Copyright 2010-2011 Univention GmbH
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

from univention.lib.i18n import Translation

from univention.management.console.log import MODULE

# get the URI parser for nodes
import univention.uvmm.helpers
import urlparse

from notifier import Callback

from .tools import object2dict

_ = Translation( 'univention-management-console-modules-uvmm' ).translate

class Storages( object ):
	def __init__( self ):
		self.storage_pools = {}

	def storage_pool_query( self, request ):
		self.required_options( request, 'nodeURI' )
		if request.options[ 'nodeURI' ] in self.storage_pools:
			self.finished( request.id, self.storage_pools[ request.options[ 'nodeURI' ] ].values() )
			return

		def _finished( thread, result, request ):
			success, data = result
			self.storage_pools[ request.options[ 'nodeURI' ] ] = dict( map( lambda p: ( p.name, object2dict( p ) ), data ) )
			self.finished( request.id, self.storage_pools[ request.options[ 'nodeURI' ] ].values() )

		self.uvmm.send( 'STORAGE_POOLS', Callback( _finished, request ), uri = request.options[ 'nodeURI' ] )

	def storage_volume_query( self, request ):
		self.required_options( request, 'nodeURI', 'pool' )

		def _finished( thread, result, request ):
			success, data = result
			self.finished( request.id, map( lambda d: object2dict( d ), data ) )

		self.uvmm.send( 'STORAGE_VOLUMES', Callback( _finished, request ), uri = request.options[ 'nodeURI' ], pool = request.options[ 'pool' ], type = request.options.get( 'type', None ) )

	def storage_volume_remove( self, request ):
		self.required_options( request, 'nodeURI', 'volumes' )
		self.uvmm.send( 'STORAGE_VOLUMES_DESTROY', Callback( self._thread_finish, request ), uri = request.options[ 'nodeURI' ], pool = request.options[ 'volumes' ] )


	# helper functions
	def get_pool( self, node_uri, pool_name ):
		"""Returns a pool object or None if the pool could not be found"""
		if not node_uri in self.storage_pools:
			return None
		if not pool_name in self.storage_pools[ node_uri ]:
			return None

		return self.storage_pools[ node_uri ][ pool_name ]

	def get_pool_path( self, node_uri, pool_name ):
		"""returns the absolute path for the given pool name on the node
		node_uri"""
		pool = self.get_pool( node_uri, pool_name )
		if pool is None:
			return None
		return pool.path

	def is_file_pool( self, node_uri, pool_name ):
		pool = self.get_pool( node_uri, pool_name )
		if pool is None:
			return None

		return pool.type in ( 'dir', 'netfs' )
