#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  UVMM navigation commands
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

import univention.uvmm.helpers # need the extensions to urlparse
import urlparse

from notifier import Callback

_ = Translation( 'univention-management-console-modules-uvmm' ).translate

class Navigation( object ):
	"""Handler for all commands for the navigation tree view"""

	def _nav_thread_finished( self, thread, result, request, parent ):
		"""This method is invoked when a threaded request for the
		navigation is finished. The result is send back to the
		client. If the result is an instance of BaseException an error
		is returned."""
		if self._check_thread_error( thread, result, request ):
			return

		MODULE.info( 'Result from UVMMd: %s' % str( result ) )
		success, data = result
		elements = []
		if parent[ 'type' ] == 'group':
			MODULE.info( 'Parent type is group so we prepare a list of nodes ...' )
			for node_pd in data:
				uri = urlparse.urlsplit( node_pd.uri )
				if not uri or not uri.netloc:
					continue
				elements.append( { 'id' : node_pd.uri, 'label' : uri.netloc, 'icon' : 'uvmm-node-%s' % uri.scheme } )
			MODULE.info( 'The following nodes have been found: %s' % str( elements ) )
		self.finished( request.id, elements, success = success )

	def nav_query( self, request ):
		"""Returns a list of children of the given parent. A parent is a dict with id and type.

		options: { 'parent' : { 'id' : 'default', 'type' : 'group' } }

		return: [ { 'id' : <node URI>, 'type' : 'node', 'label' : <server name> }, ... ] or
				[ { 'id' : <group ID>, 'type' : 'group', 'label' : <group name> }, ... ]
		"""
		self.required_options( request, 'parent' )

		parent = request.options[ 'parent' ]
		if not isinstance( parent, dict ) and parent is not None:
			raise UMC_OptionTypeError( _( 'The parent must be None or a dictionary' ) )

		if not parent:
			self.finished( request.id, [ { 'id' : 'default', 'label' : _( 'Physical servers' ), 'type' : 'group', 'icon' : 'uvmm-group' }, ] )
			return
		self.uvmm.send( 'NODE_LIST', Callback( self._nav_thread_finished, request, parent ), group = parent[ 'id' ], pattern = '*' )
