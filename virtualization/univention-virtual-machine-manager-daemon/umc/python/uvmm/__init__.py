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
from univention.management.console.config import ucr
from univention.management.console.modules import Base, UMC_OptionTypeError, UMC_OptionMissing, UMC_CommandError
from univention.management.console.log import MODULE

from .uvmmd import UVMM_RequestBroker

from notifier import Callback

_ = Translation( 'univention-management-console-modules-uvmm' ).translate

_uvmm_locale = Translation( 'univention.virtual.machine.manager' ).translate

class Instance( Base ):
	DOMAIN_STATES = ( 'RUN', 'PAUSE', 'SHUTDOWN', 'RESTART' )
	def __init__( self ):
		Base.__init__( self )
		self.uvmm = UVMM_RequestBroker()


	def _thread_finish( self, thread, result, request ):
		"""This method is invoked when a threaded request function is
		finished. The result is send back to the client. If the result
		is an instance of BaseException an error is returned."""
		if not isinstance( result, BaseException ):
			success, data = result
			self.finished( request.id, data, success = success )
		else:
			msg = str( result ) + '\n' + '\n'.join( thread.trace )
			MODULE.process( 'An internal error occurred: %s' % msg )
			self.finished( request.id, None, msg, False )

	def group_query( self, request ):
		self.uvmm.send( 'GROUP_LIST', Callback( self._thread_finish, request ) )

	def node_query( self, request ):
		self.uvmm.send( 'NODE_LIST', Callback( self._thread_finish, request ), group = 'default', pattern = request.options.get( 'nodePattern', '*' ) )

	def domain_query( self, request ):
		self.uvmm.send( 'DOMAIN_LIST', Callback( self._thread_finish, request ), uri = request.options.get( 'nodePattern', '*' ), pattern = request.options.get( 'domainPattern', '*' ) )

	def node_get( self, request ):
		self.finished( request.id )

	def domain_get( self, request ):
		self.required_options( request, 'nodeURI', 'domainUUID' )
		self.uvmm.send( 'DOMAIN_INFO', Callback( self._thread_finish, request ), uri = request.options[ 'nodeURI' ], domain = request.options[ 'domainUUID' ] )

	def domain_add( self, request ):
		self.finished( request.id )

	def domain_put( self, request ):
		self.finished( request.id )

	def domain_state( self, request ):
		self.required_options( request, 'nodeURI', 'domainUUID', 'domainState' )
		if request.options[ 'domainState' ] not in Instance.DOMAIN_STATES:
			raise UMC_OptionTypeError( _( 'Invalid domain state' ) )
		self.uvmm.send( 'DOMAIN_STATE', Callback( self._thread_finish, request ), uri = request.options[ 'nodeURI' ], domain = request.options[ 'domainUUID' ], state = request.options[ 'domainState' ] )

	def domain_migrate( self, request ):
		self.finished( request.id )

	def nic_get( self, request ):
		self.finished( request.id )

	def nic_add( self, request ):
		self.finished( request.id )

	def nic_put( self, request ):
		self.finished( request.id )

	def snapshot_get( self, request ):
		self.finished( request.id )

	def snapshot_add( self, request ):
		self.finished( request.id )

	def snapshot_set( self, request ):
		self.finished( request.id )

	def device_get( self, request ):
		self.finished( request.id )

	def device_add( self, request ):
		self.finished( request.id )

	def device_put( self, request ):
		self.finished( request.id )

	def storage_query( self, request ):
		self.finished( request.id )

