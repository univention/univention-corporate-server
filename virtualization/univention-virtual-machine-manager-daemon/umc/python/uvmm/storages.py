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

_ = Translation( 'univention-management-console-modules-uvmm' ).translate

class Storages( object ):
	def storage_pool_query( self, request ):
		self.required_options( request, 'nodeURI' )
		self.uvmm.send( 'STORAGE_POOLS', Callback( self._thread_finish, request ), uri = request.options[ 'nodeURI' ] )

	def storage_volume_query( self, request ):
		self.required_options( request, 'nodeURI', 'pool' )
		self.uvmm.send( 'STORAGE_VOLUMES', Callback( self._thread_finish, request ), uri = request.options[ 'nodeURI' ], pool = request.options[ 'pool' ], type = request.options.get( 'type', None ) )

	def storage_volume_remove( self, request ):
		self.required_options( request, 'nodeURI', 'volumes' )
		self.uvmm.send( 'STORAGE_VOLUMES_DESTROY', Callback( self._thread_finish, request ), uri = request.options[ 'nodeURI' ], pool = request.options[ 'volumes' ] )

