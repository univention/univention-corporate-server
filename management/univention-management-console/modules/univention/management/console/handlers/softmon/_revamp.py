#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  softmon module: revamp module command result for the specific user interface
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
import univention.management.console.dialog as umcd
import univention.management.console.protocol as umcp
import univention.management.console.tools as umct

import univention.debug as ud

import _syntax

_ = umc.Translation( 'univention.management.console.handlers.softmon' ).translate

class Web( object ):
	def _web_softmon_system_search( self, object, res ):
		main = []
		form = umcd.List()

		# INFO: erste Aufgabe ist das Widget für die Suchfilter fertigzustellen
		# INFO: das basiert auf DynamicList und hat die auf diesen Fall zugeschnitte Erweiterung
		# INFO: dass das erste Element ein Select-Button ist, der das Widget in der letzten
		# INFO: Spalte verändern kann
		# INFO: Hier wird momentan nur dieses Widget angezeigt.
		select = umcd.Selection( ( 'key', _syntax.SoftMonSystemSearchKey() ), default = 'name' )
		op = umcd.Selection( ( 'operator', _syntax.SoftMonSearchOperator() ), default = 'eq' )
		values = {
			'name' : umcd.TextInput( ( 'pattern', umc.String( '' ) ),
									 default = 'domaincontroller_master' ),
			'ucs_version' : umcd.Selection( ( 'pattern', _syntax.SoftMonSystemVersions() ),
											default = '1.3-2-0' ),
			'role' : umcd.Selection( ( 'pattern', umc.SystemRoleSelection( '' ) ),
									 default = 'domaincontroler_master' ),
			}
		descr = umcd.DynamicList( self[ 'softmon/system/search' ][ 'filter' ],
								  [ _( 'Key' ), _( 'Operator' ), _( 'Pattern' )  ], [ op, ],
								  modifier = select, modified = values ) #,
								  # default = default )
		descr[ 'colspan' ] = '2'
		form.add_row( [ descr ] )

		res.dialog = form

		self.revamped( object.id(), res )

		return
