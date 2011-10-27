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

from notifier import Callback

from .tools import object2dict

_ = Translation( 'univention-management-console-modules-uvmm' ).translate

class Domains( object ):
	def domain_query( self, request ):
		"""Returns a list of domains matching domainPattern on the nodes matching nodePattern.

		options: { 'nodepattern': <node name pattern>, 'domainPattern' : <domain pattern> }

		return: { <node uri> : [ ( <uuid>, <name> ), ... ], ... }
		"""
		self.uvmm.send( 'DOMAIN_LIST', Callback( self._thread_finish, request ), uri = request.options.get( 'nodePattern', '*' ), pattern = request.options.get( 'domainPattern', '*' ) )

	def domain_get( self, request ):
		"""Returns details about a domain domainUUID.

		options: { 'nodeURI': <node uri>, 'domainUUID' : <domain UUID> }

		return: { 'success' : (True|False), 'message' : <details> }
		"""
		def _finished( thread, result, request ):
			if self._check_thread_error( thread, result, request ):
				return

			success, data = result

			json = object2dict( data, convert_attrs = ( 'graphics', 'interfaces', 'disks' )  )
			MODULE.info( 'Got domain description: success: %s, data: %s' % ( success, json ) )
			self.finished( request.id, { 'success' : success, 'data' : json } )

		self.required_options( request, 'nodeURI', 'domainUUID' )
		self.uvmm.send( 'DOMAIN_INFO', Callback( _finished, request ), uri = request.options[ 'nodeURI' ], domain = request.options[ 'domainUUID' ] )

	def domain_add( self, request ):
		"""Creates a new domain on nodeURI.

		options: { 'nodeURI': <node uri>, 'domain' : {} }

		return: { 'success' : (True|False), 'message' : <details> }
		"""
		self.finished( request.id )

	def domain_put( self, request ):
		"""Modifies a domain domainUUID on node nodeURI.

		options: { 'nodeURI': <node uri>, 'domainUUID' : <domain UUID>, 'domain' : {} }

		return: { 'success' : (True|False), 'message' : <details> }
		"""
		self.finished( request.id )

	def domain_state( self, request ):
		"""Set the state a domain domainUUID on node nodeURI.

		options: { 'nodeURI': <node uri>, 'domainUUID' : <domain UUID>, 'domainState': (RUN|SHUTDOWN|PAUSE|RESTART) }

		return: { 'success' : (True|False), 'message' : <details> }
		"""
		self.required_options( request, 'nodeURI', 'domainUUID', 'domainState' )
		if request.options[ 'domainState' ] not in Instance.DOMAIN_STATES:
			raise UMC_OptionTypeError( _( 'Invalid domain state' ) )
		self.uvmm.send( 'DOMAIN_STATE', Callback( self._thread_finish, request ), uri = request.options[ 'nodeURI' ], domain = request.options[ 'domainUUID' ], state = request.options[ 'domainState' ] )

	def domain_migrate( self, request ):
		"""Migrates a domain from sourceURI to targetURI.

		options: { 'sourceURI': <source node uri>, 'domainUUID' : <domain UUID>, 'targetURI': <target node uri> }

		return: { 'success' : (True|False), 'message' : <details> }
		"""
		self.required_options( request, 'sourceURI', 'domainUUID', 'targetURI' )
		self.uvmm.send( 'DOMAIN_MIGRATE', Callback( self._thread_finish, request ), uri = request.options[ 'sourceURI' ], domain = request.options[ 'domainUUID' ], target_uri = request.options[ 'targetURI' ] )

	def domain_remove( self, request ):
		"""Removes a domain. Optional a list of volumes can bes specified that should be removed

		options: { 'nodeURI': <node uri>, 'domainUUID' : <domain UUID> }

		return: { 'success' : (True|False), 'message' : <details> }
		"""
		self.required_options( request, 'nodeURI', 'domainUUID' )
		self.uvmm.send( 'DOMAIN_UNDEFINE', Callback( self._thread_finish, request ), uri = request.options[ 'nodeURI' ], domain = request.options[ 'domainUUID' ], volumes = request.options[ 'volumes' ] )

