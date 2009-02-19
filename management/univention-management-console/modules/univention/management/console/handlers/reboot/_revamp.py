#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  reboot module: revamp module command result for the specific user interface
#
# Copyright (C) 2008-2009 Univention GmbH
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

import os

import univention.management.console as umc
import univention.management.console.dialog as umcd
import univention.management.console.protocol as umcp
import univention.management.console.tools as umct

import univention.debug as ud

_ = umc.Translation( 'univention.management.console.handlers.reboot' ).translate

class Web( object ):
	def _web_reboot_do(self,object,res):
		result = umcd.List()
		if object.incomplete:
			select = umcd.make( self[ 'reboot/do' ][ 'action' ], default = 'reboot')
			text = umcd.make( self[ 'reboot/do' ][ 'message' ])

			req = umcp.Command( args = [ 'reboot/do' ])
			ids = [select.id(), text.id()]

			result.add_row( [select] )
			result.add_row( [text] )
			result.add_row( [ umcd.Button( label = _( 'Execute' ), tag = 'actions/ok', actions = [  umcd.Action( req,ids ) ], close_dialog = True ) ] )

		else:
			result.add_row( [ umcd.InfoBox(  res.dialog  ) ] )

		res.dialog = [result]
		self.revamped( object.id(), res )
