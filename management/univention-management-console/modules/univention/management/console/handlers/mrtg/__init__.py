#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: display mrtg images
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
short_description = _( 'Load Statistic' )
long_description = _( 'System Load Statistic' )
categories = [ 'all', 'system' ]

command_description = {
	'mrtg/view' : umch.command(
		short_description = _( 'Load Statistic' ),
		method = 'mrtg_view',
		values = {},
		startup = True,
	),
}

class handler( umch.simpleHandler, _revamp.Web ):
	def __init__( self ):
		global command_description
		umch.simpleHandler.__init__( self, command_description )

	def mrtg_view( self, object ):
		path = '/var/www/statistik'
		images = ( ( 'day', 'uds_0load-day.png' ),
				   ( 'week', 'uds_0load-week.png' ),
				   ( 'month', 'uds_0load-month.png' ),
				   ( 'year', 'uds_0load-year.png' ) )

		result = []
		for key, img in images:
			filename = os.path.join( path, img )
			if os.path.exists( filename ):
				result.append( ( key, img ) )

		self.finished( object.id(), result )
