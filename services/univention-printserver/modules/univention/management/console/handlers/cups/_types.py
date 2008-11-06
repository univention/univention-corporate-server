#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: manages a CUPS server
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

_ = umc.Translation( 'univention.management.console.handlers.cups' ).translate

class CUPS_SearchKeys( umc.StaticSelection ):
	def __init__( self, required = True ):
		umc.StaticSelection.__init__( self, unicode( _( 'Search Key' ) ), required = required )

	def choices( self ):
		return ( ( 'printer', _( 'Printer Name' ) ), ( 'description', _( 'Description' ) ),
				 ( 'location', _( 'Location' ) ) )

umcd.copy( umc.StaticSelection, CUPS_SearchKeys )

printername = umc.String( _( 'Printer' ) )
searchkey = CUPS_SearchKeys()
filter = umc.String( '&nbsp;' , required = False )
printers = umc.StringList( _( 'Printer List' ) )
jobs = umc.StringList( _( 'Job List' ) )
user = umc.String( _( 'User' ) )
pagesoftlimit = umc.Integer( _( 'Page Quota Soft-Limit' ) )
pagehardlimit = umc.Integer( _( 'Page Quota Hard-Limit' ) )
