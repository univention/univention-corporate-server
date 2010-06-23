#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  mrtg module: revamp module command result for the specific user interface
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
import univention.management.console.dialog as umcd

import univention.debug as ud

_ = umc.Translation( 'univention.management.console.handlers.mrtg' ).translate

class Web( object ):

	day = _( "Period: previous day" )
	week = _( "Period: previous week" )
	month = _( "Period: previous month" )
	year = _( "Period: previous year" )

	def _web_mrtg_view( self, object, res ):
		text = { 'day' : self.day,
				 'week' : self.week,
				 'month' : self.month,
				 'year' : self.year }
		lst = []
		for key, img in res.dialog:
			lst.append( umcd.Frame( [ umcd.ImageURL( '/statistik/%s' % img ) ], text[ key ] ) )

		if not lst:
			lst.append( umcd.InfoBox( _( 'Could not find any statistics. Check if univention-maintance is installed correctly.' ) ) )
		lst.insert(0, umcd.HTML('<b>' + _( 'System load in percent' ) + '</b>'))

		res.dialog = lst
		self.revamped( object.id(), res )

	def _web_mrtg_view_session( self, object, res ):
		text = { 'day' : self.day,
				 'week' : self.week,
				 'month' : self.month,
				 'year' : self.year }
		lst = []
		for key, img in res.dialog:
			lst.append( umcd.Frame( [ umcd.ImageURL( '/statistik/%s' % img ) ], text[ key ] ) )

		if not lst:
			lst.append( umcd.InfoBox( _( 'Could not find any statistics. Check if univention-maintance is installed correctly.' ) ) )
		lst.insert(0, umcd.HTML('<b>' + _( 'Number of active terminal server sessions' ) + '</b>'))

		res.dialog = lst
		self.revamped( object.id(), res )

	def _web_mrtg_view_memory( self, object, res ):
		text = { 'day' : self.day,
				 'week' : self.week,
				 'month' : self.month,
				 'year' : self.year }
		lst = []
		for key, img in res.dialog:
			lst.append( umcd.Frame( [ umcd.ImageURL( '/statistik/%s' % img ) ], text[ key ] ) )

		if not lst:
			lst.append( umcd.InfoBox( _( 'Could not find any statistics. Check if univention-maintance is installed correctly.' ) ) )
		lst.insert(0, umcd.HTML('<b>' + _( 'Utilization of system memory in percent' ) + '</b>'))

		res.dialog = lst
		self.revamped( object.id(), res )

	def _web_mrtg_view_swap( self, object, res ):
		text = { 'day' : self.day,
				 'week' : self.week,
				 'month' : self.month,
				 'year' : self.year }
		lst = []
		for key, img in res.dialog:
			lst.append( umcd.Frame( [ umcd.ImageURL( '/statistik/%s' % img ) ], text[ key ] ) )

		if not lst:
			lst.append( umcd.InfoBox( _( 'Could not find any statistics. Check if univention-maintance is installed correctly.' ) ) )
		lst.insert(0, umcd.HTML('<b>' + _( 'Utilization of swap space in percent' ) + '</b>'))

		res.dialog = lst
		self.revamped( object.id(), res )
