# -*- coding: utf-8 -*-
#
# Univention Management Console
#  service module: revamps dialog result for the web interface
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

import string
import locale
from univention.config_registry_info import ConfigRegistryInfo, set_language

locale_language_code=locale.getlocale(locale.LC_MESSAGES)[0]
if locale_language_code and len(locale_language_code) >= 2:
	locale_language_code=locale_language_code[:2] # get ISO 3166-1 alpha-2 code
	set_language(locale_language_code)
else:
	set_language('en')
del locale_language_code

import univention.management.console as umc
import univention.management.console.tools as umct
import univention.management.console.dialog as umcd
import univention.management.console.protocol as umcp

import univention.debug as ud

_ = umc.Translation( 'univention.management.console.handlers.services' ).translate

class Web( object ):
	def _web_service_list( self, object, res ):
		lst = umcd.List()
		servs = res.dialog
		boxes = []
		lst.set_header( [ umcd.Fill( 2, _( 'Name' ) ), _( 'Status' ), _( 'Start type' ), _( 'Description' ), _('Select') ] )
		for name, srv in servs.items():
			if srv.running:
				icon = umcd.Image( 'actions/yes', umct.SIZE_SMALL )
			else:
				icon = umcd.Image( 'actions/no', umct.SIZE_SMALL )
			chk = umcd.Checkbox( static_options = { 'service' : name } )
			boxes.append( chk.id() )
			image = umcd.Image( 'services/default', umct.SIZE_MEDIUM )
			type = _( 'automatically' )
			if srv.autostart and srv.autostart == "yes":
				type = _( 'automatically' )
			elif srv.autostart and srv.autostart == "manually":
				type = _( 'manual' )
			elif srv.autostart and srv.autostart == "no":
				type = _( 'never' )
			lst.add_row( [ image, name, icon, type, srv[ 'description' ], chk ] )
		req = umcp.Command( args = [], opts= { 'service' : [] } )
		req_list = umcp.Command( args = [ 'service/list' ],
								 opts = {} )
		actions = ( umcd.Action( req, boxes, True ), umcd.Action( req_list ) )
		choices = [ ( 'service/start', _( 'Start services' ) ),
					( 'service/stop', _( 'Stop services' ) ),
					( 'service/start_auto', _( 'Start automatically' ) ),
					( 'service/start_manual', _( 'Start manually' ) ), 
					( 'service/start_never', _( 'Start never' ) ), ]
		select = umcd.SelectionButton( _( 'Select the operation' ), choices, actions )
		lst.add_row( [ umcd.Fill( 5 ), select ] )
		res.dialog = [ lst ]
		self.revamped( object.id(), res )
