#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: display mrtg images
#
# Copyright 2007-2010 Univention GmbH
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

import univention.management.console as umc
import univention.management.console.handlers as umch
import univention.management.console.dialog as umcd
import univention.management.console.tools as umct

import os

import notifier.popen

import _revamp

_ = umc.Translation( 'univention.management.console.handlers.mrtg' ).translate

name = 'mrtg'
icon = 'mrtg/module'
short_description = _( 'System statistics' )
long_description = _( 'System statistics' )
categories = [ 'all', 'system' ]

command_description = {
	'mrtg/view' : umch.command(
		short_description = _( 'System load' ),
		method = 'mrtg_view',
		values = {},
		startup = True,
		priority = 40,
	),
	'mrtg/session' : umch.command(
		short_description = _( 'Terminal server sessions' ),
		method = 'mrtg_view_session',
		values = {},
		startup = True,
		priority = 30,
	),
	'mrtg/memory' : umch.command(
		short_description = _( 'Memory' ),
		method = 'mrtg_view_memory',
		values = {},
		startup = True,
		priority = 20,
	),
	'mrtg/swap' : umch.command(
		short_description = _( 'Swap space' ),
		method = 'mrtg_view_swap',
		values = {},
		startup = True,
		priority = 10,
	),


}

class handler( umch.simpleHandler, _revamp.Web ):
	def __init__( self ):
		global command_description
		umch.simpleHandler.__init__( self, command_description )
		self.path = '/var/www/statistik'

	def mrtg_view( self, object ):
		path = self.path
		images = ( ( 'day', 'ucs_0load-day.png' ),
				   ( 'week', 'ucs_0load-week.png' ),
				   ( 'month', 'ucs_0load-month.png' ),
				   ( 'year', 'ucs_0load-year.png' ) )

		result = []
		for key, img in images:
			filename = os.path.join( path, img )
			if os.path.exists( filename ):
				result.append( ( key, img ) )

		self.finished( object.id(), result )

	def mrtg_view_session( self, object ):
		path = self.path
		images = ( ( 'day', 'ucs_1sessions-day.png' ),
				   ( 'week', 'ucs_1sessions-week.png' ),
				   ( 'month', 'ucs_1sessions-month.png' ),
				   ( 'year', 'ucs_1sessions-year.png' ) )

		result = []
		for key, img in images:
			filename = os.path.join( path, img )
			if os.path.exists( filename ):
				result.append( ( key, img ) )

		self.finished( object.id(), result )

	def mrtg_view_memory( self, object ):
		path = self.path
		images = ( ( 'day', 'ucs_2mem-day.png' ),
				   ( 'week', 'ucs_2mem-week.png' ),
				   ( 'month', 'ucs_2mem-month.png' ),
				   ( 'year', 'ucs_2mem-year.png' ) )

		result = []
		for key, img in images:
			filename = os.path.join( path, img )
			if os.path.exists( filename ):
				result.append( ( key, img ) )

		self.finished( object.id(), result )

	def mrtg_view_swap( self, object ):
		path = self.path
		images = ( ( 'day', 'ucs_3swap-day.png' ),
				   ( 'week', 'ucs_3swap-week.png' ),
				   ( 'month', 'ucs_3swap-month.png' ),
				   ( 'year', 'ucs_3swap-year.png' ) )

		result = []
		for key, img in images:
			filename = os.path.join( path, img )
			if os.path.exists( filename ):
				result.append( ( key, img ) )

		self.finished( object.id(), result )



