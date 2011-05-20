#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: manages a CUPS server
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

_ = umc.Translation( 'univention.management.console.handlers.cups' ).translate

class CUPS_SearchKeys( umc.StaticSelection ):
	def __init__( self, required = True ):
		umc.StaticSelection.__init__( self, unicode( _( 'Search key' ) ), required = required )

	def choices( self ):
		return ( ( 'printer', _( 'Printer name' ) ), ( 'description', _( 'Description' ) ),
				 ( 'location', _( 'Location' ) ) )

umcd.copy( umc.StaticSelection, CUPS_SearchKeys )

printername = umc.String( _( 'Printer' ) )
searchkey = CUPS_SearchKeys()
filter = umc.String( '&nbsp;' , required = False )
printers = umc.StringList( _( 'Printer list' ) )
jobs = umc.StringList( _( 'Job list' ) )
user = umc.String( _( 'User' ) )
pagesoftlimit = umc.Integer( _( 'Page quota soft limit' ) )
pagehardlimit = umc.Integer( _( 'Page quota hard limit' ) )
