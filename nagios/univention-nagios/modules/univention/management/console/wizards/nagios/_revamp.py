#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  nagios wizard
#
# Copyright 2007-2011 Univention GmbH
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
import univention.management.console.protocol as umcp
import univention.management.console.tools as umct

_ = umc.Translation( 'univention.management.console.wizards.nagios' ).translate

class Web( object ):
	def _web_nagios_show( self, object, res ):
		options = res.dialog
		items = []
		wiz = umcd.Wizard( _( "Nagios configuration" ) )
		image = umcd.Image( 'wizards/nagios/wizard', umct.SIZE_LARGE )
		wiz.set_image( image )
		number = umcd.make( self[ 'wizard/nagios/set' ][ 'number' ], default = options[ 'number' ] )
		wiz.add_option( _( 'When an event is triggered by Nagios for this server the information will be sent to this phone number' ), number )
		items.append( number.id() )

		req = umcp.Command( args = [ 'wizard/nagios/set' ] )
		req_show = umcp.Command( args = [ 'wizard/nagios/show' ] )

		actions = ( umcd.Action( req, items ), umcd.Action( req_show ) )
		button = umcd.SetButton( actions )
		wiz.add_buttons( button, umcd.ResetButton( items ) )

		res.dialog = wiz

		self.revamped( object.id(), res )
