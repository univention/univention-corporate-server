# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: management of virtualization servers
#
# Copyright 2010-2012 Univention GmbH
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

from univention.lib.i18n import Translation

from univention.management.console.log import MODULE
from univention.management.console.modules import Base, UMC_OptionTypeError, UMC_OptionMissing, UMC_CommandError
from univention.management.console.protocol.definitions import MODULE_ERR_COMMAND_FAILED

from univention.uvmm.protocol import Disk
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
			if success:
				self.storage_pools[ request.options[ 'nodeURI' ] ] = dict( map( lambda p: ( p.name, object2dict( p ) ), data ) )
				self.finished( request.id, self.storage_pools[ request.options[ 'nodeURI' ] ].values() )
			else:
				self.finished( request.id, None, message = str( data ), status = MODULE_ERR_COMMAND_FAILED )

		self.uvmm.send( 'STORAGE_POOLS', Callback( _finished, request ), uri = request.options[ 'nodeURI' ] )

	def storage_volume_query( self, request ):
		"""Returns a list of volumes located in the given pool.

		options: { 'nodeURI': <node uri>, 'pool' : <pool name>[, 'type' : (disk|cdrom|floppy)] }

		return: [ { <volume description> }, ... ]
		"""
		self.required_options( request, 'nodeURI', 'pool' )

		def _finished( thread, result, request ):
			success, data = result
			if success:
				volume_list = []
				for vol in data:
					vol = object2dict( vol )
					vol[ 'volumeFilename' ] = os.path.basename( vol.get( 'source', '' ) )
					volume_list.append( vol )
				self.finished( request.id, volume_list )
			else:
				self.finished( request.id, None, message = str( data ), status = MODULE_ERR_COMMAND_FAILED )

		drive_type = request.options.get( 'type', None )
		if drive_type == 'floppy': # not yet supported
			drive_type = 'disk'
		self.uvmm.send( 'STORAGE_VOLUMES', Callback( _finished, request ), uri = request.options[ 'nodeURI' ], pool = request.options[ 'pool' ], type = drive_type )

	def storage_volume_remove( self, request ):
		"""Removes a list of volumes located in the given pool.

		options: { 'nodeURI': <node uri>, 'volumes' : [ { 'pool' : <pool name>, 'volumeFilename' : <filename> }, ... ] }

		return: 
		"""
		self.required_options( request, 'nodeURI', 'volumes' )
		volume_list = []
		node_uri = request.options[ 'nodeURI' ]
		for vol in request.options[ 'volumes' ]:
			path = self.get_pool_path( node_uri, vol[ 'pool' ] )
			if not path:
				MODULE.warn( 'Could not remove volume %(volumeFilename)s. The pool %(pool)s is not known' % vol )
				continue
			volume_list.append( os.path.join( path, vol[ 'volumeFilename' ] ) )
		self.uvmm.send( 'STORAGE_VOLUMES_DESTROY', Callback( self._thread_finish, request ), uri = request.options[ 'nodeURI' ], volumes = volume_list )

	def storage_volume_usedby( self, request ):
		"""Returns a list of domains that use the given volume.

		options: { 'nodeURI' : <node URI>, 'pool' : <pool name>, 'volumeFilename': <filename> }

		return: [ <domain URI>, ... ]
		"""
		self.required_options( request, 'nodeURI', 'pool', 'volumeFilename' )

		def _finished( thread, result, request ):
			if self._check_thread_error( thread, result, request ):
				return

			success, data = result
			if success:
				if isinstance( data, ( list, tuple ) ):
					data = map( lambda x: '#'.join( x ), data )
				self.finished( request.id, data )
			else:
				self.finished( request.id, None, message = str( data ), status = MODULE_ERR_COMMAND_FAILED )


		pool_path = self.get_pool_path( request.options[ 'nodeURI' ], request.options[ 'pool' ] )
		if pool_path is None:
			raise UMC_OptionTypeError( _( 'The given pool could not be found or is no file pool' ) )
		volume = os.path.join( pool_path, request.options[ 'volumeFilename' ] )
		self.uvmm.send( 'STORAGE_VOLUME_USEDBY', Callback( _finished, request ), volume = volume )

	def storage_volume_deletable( self, request ):
		"""Returns a list of domains that use the given volume.

		options: [ { 'domainURI' : <domain URI>, 'pool' : <pool name>, 'volumeFilename': <filename> }, ... ]

		return: [ { 'domainURI' : <domain URI>, 'pool' : <pool name>, 'volumeFilename': <filename>, 'deletable' : (True|False|None) }, ... ]
		"""
		_tmp_cache = {}
		return_value = []

		for volume in request.options:
			# check if volume is used by any other domain
			node_uri, domain_uuid = urlparse.urldefrag( volume[ 'domainURI' ] )
			pool_path = self.get_pool_path( node_uri, volume[ 'pool' ] )
			if pool_path is None:
				volume[ 'deletable' ] = None
				return_value.append( volume )
				continue
			volume_path = os.path.join( pool_path, volume[ 'volumeFilename' ] )

			success, result = self.uvmm.send( 'STORAGE_VOLUME_USEDBY', None, volume = volume_path )
			if not success:
				raise UMC_OptionTypeError( _( 'Failed to check if the drive is used by any other virtual instance' ) )

			if len( result ) > 1: # is used by at least one other domain
				volume[ 'deletable' ] = False
				return_value.append( volume )
				continue

			if not volume[ 'domainURI' ] in _tmp_cache:
				success, result = self.uvmm.send( 'DOMAIN_INFO', None, uri = node_uri, domain = domain_uuid )
				if not success:
					raise UMC_OptionTypeError(_('Could not retrieve details for domain %s') % domain_uuid)
				_tmp_cache[ volume[ 'domainURI' ] ] = result

			domain = _tmp_cache[ volume[ 'domainURI' ] ]
			drive = None
			for disk in domain.disks:
				if disk.source == volume_path:
					drive = disk
					break
			else:
				volume[ 'deletable' ] = None
				return_value.append( volume )
				continue

			volume[ 'deletable' ] = drive.type == Disk.TYPE_FILE and drive.device == Disk.DEVICE_DISK

			return_value.append( volume )

		self.finished( request.id, return_value )

	# helper functions
	def get_pool( self, node_uri, pool_name = None, pool_path = None ):
		"""Returns a pool object or None if the pool could not be found"""
		if pool_name is None and pool_path is None:
			return None
		if not node_uri in self.storage_pools:
			success, data = self.uvmm.send( 'STORAGE_POOLS', None, uri = node_uri )
			self.storage_pools[ node_uri ] = dict( map( lambda p: ( p.name, object2dict( p ) ), data ) )
			if not node_uri in self.storage_pools:
				return None

		if pool_name is not None and not pool_name in self.storage_pools[ node_uri ]:
			return None

		if pool_name is not None:
			return self.storage_pools[ node_uri ][ pool_name ]

		for uri, pool in self.storage_pools[ node_uri ].items():
			if pool_path.startswith( pool[ 'path' ] ):
				return pool

		return None

	def get_pool_path( self, node_uri, pool_name ):
		"""returns the absolute path for the given pool name on the node
		node_uri"""
		pool = self.get_pool( node_uri, pool_name )
		if pool is None:
			return None
		return pool[ 'path' ]

	def get_pool_name( self, node_uri, pool_path ):
		"""returns the pool name for the given pool path on the node
		node_uri"""
		pool = self.get_pool( node_uri, pool_path = pool_path )
		if pool is None:
			return None
		return pool[ 'name' ]

	def is_file_pool( self, node_uri, pool_name ):
		pool = self.get_pool( node_uri, pool_name )
		if pool is None:
			return None

		return pool[ 'type' ] in ( 'dir', 'netfs' )
