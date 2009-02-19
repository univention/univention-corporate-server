#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  mrtg module: revamp module command result for the specific user interface
#
# Copyright (C) 2007-2009 Univention GmbH
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
import univention.management.console.dialog as umcd

import univention.debug as ud

_ = umc.Translation( 'univention.management.console.handlers.mrtg' ).translate

class Web( object ):
	def _web_mrtg_view( self, object, res ):
		text = { 'day' : _( 'Day' ),
				 'week' : _( 'Week' ),
				 'month' : _( 'Month' ),
				 'year' : _( 'Year' ) }
		lst = []
		for key, img in res.dialog:
			lst.append( umcd.Frame( [ umcd.ImageURL( '/statistik/%s' % img ) ], text[ key ] ) )

		if not lst:
			lst.append( umcd.InfoBox( _( 'Could not find any statistics. Check if univention-maintance is installed correctly.' ) ) )
		res.dialog = lst
		self.revamped( object.id(), res )
