#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  nagios wizard
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

_ = umc.Translation( 'univention.management.console.wizards.mail' ).translate

class Web( object ):
	def _web_nagios_show( self, object, res ):
		options = res.dialog
		items = []
		wiz = umcd.Wizard( _( "Nagios Configuration" ) )
		image = umcd.Image( 'wizards/nagios/wizard', umct.SIZE_LARGE )
		wiz.set_image( image )
		number = umcd.make( self[ 'wizard/nagios/set' ][ 'number' ], default = options[ 'number' ] )
		wiz.add_option( _( 'If an event is triggered by nagios on this server the information are send to this phone number' ), number )
		items.append( number.id() )

		req = umcp.Command( args = [ 'wizard/nagios/set' ] )
		req_show = umcp.Command( args = [ 'wizard/nagios/show' ] )

		actions = ( umcd.Action( req, items ), umcd.Action( req_show ) )
		button = umcd.SetButton( actions )
		wiz.add_buttons( button, umcd.ResetButton( items ) )

		res.dialog = wiz

		self.revamped( object.id(), res )
