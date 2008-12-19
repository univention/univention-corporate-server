#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  base classes for UMCP dialogs
#
# Copyright (C) 2006, 2007 Univention GmbH
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

import univention.management.console.tools as umct
import univention.management.console.values as umcv
import univention.management.console.protocol as umcp
import univention.management.console.locales as locales

import base
import image
import button
import input
import widget

_ = locales.Translation( 'univention.management.console.dialog' ).translate

class InfoBox( base.Text, image.Image ):
	def __init__( self, text = '', columns = 1, icon = 'actions/info', size = umct.SIZE_SMALL ):
		image.Image.__init__( self, icon, size )
		base.Text.__init__( self, text, attributes = { 'colspan' : str( columns ) } )

class Question( base.List ):
	def __init__( self, text = '', actions = [], okay = _( 'Ok' ) ):
		base.List.__init__( self )
		self._image = image.Image( 'actions/info', umct.SIZE_SMALL )
		self._text = base.Text( text, attributes = { 'colspan' : '2' } )
		self.add_row( [ self._image, self._text ] )
		btn = button.CancelButton()
		self.add_row( [ '', button.Button( okay, 'actions/ok', actions = actions ), btn ] )

class SearchForm( base.List ):
	def __init__( self, command = None, fields = [], opts = {} ):
		base.List.__init__( self )
		ids = []
		defaults = {}
		for row in fields:
			line = []
			for pair in row:
				if isinstance( pair, ( list, tuple ) ):
					cell, default = pair
					line.append( cell )
					if isinstance( cell, input.Input ):
						ids.append( cell.id() )
						defaults[ cell.id() ] = default
				else:
					line.append( pair )
			self.add_row( line )
		req = umcp.Command( args = [ command ], opts = opts )
		btn = button.SearchButton( button.Action( req, ids ) )
		btn.close_dialog = False
		reset = button.ResetButton( fields = defaults )
		reset.close_dialog = False
		num_result = widget.make_readonly( ( None, umcv.Integer( _( 'Results per Page' ) ) ),
										   attributes = { 'width' : '100' } )
		btnlst = base.List()
		btnlst.add_row( [ btn, reset ] )
		self.add_row( [ num_result, btnlst ] )
		self.add_row( [ base.Fill( 2 ) ] )

HelperTypes = ( type( InfoBox() ), type( Question() ), type( SearchForm() ) )
