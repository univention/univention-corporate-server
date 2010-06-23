#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  base classes for UMCP dialogs
#
# Copyright 2006-2010 Univention GmbH
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
		btn = button.CancelButton( attributes = {'class': 'cancel'} ) 
		self.add_row( [ '', btn , button.Button( okay, 'actions/ok', attributes = {'class': 'submit'}, actions = actions ) ] )

class YesNoQuestion( base.Frame ):
	def __init__( self, title = _( 'Confirmation' ), text = _( 'Are you sure?' ), actions = [], yes = _( 'Yes' ), no = _( 'No' ), icon = 'actions/info' ):
		lst = base.List()
		self._image = image.Image( icon, umct.SIZE_SMALL )
		self._text = base.Text( text, attributes = { 'colspan' : '2' } )
		lst.add_row( [ self._image, self._text ] )
		btn = button.ReturnButton( no )
		lst.add_row( [ '', button.Button( yes, 'actions/ok', actions = actions ), btn ] )
		base.Frame.__init__( self, [ lst ], title )

class SearchForm( base.List ):
	def __init__( self, command = None, fields = [], opts = {}, search_button_label = _("Search"), paged_results = False ):
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
		btn = button.SearchButton( button.Action( req, ids ), {'class': 'submit', 'defaultbutton': '1'}, label = search_button_label )
		btn.close_dialog = False
		reset = button.ResetButton( fields = defaults, attributes = { 'class': 'cancel' } )
		reset.close_dialog = False
		if paged_results:
			num_result = widget.make_readonly( ( None, umcv.Integer( _( 'Results per page' ) ) ),
										   attributes = { 'width' : '100' } )
		else:
			num_result = base.Fill(1)
		btnlst = base.List()
		btnlst.add_row( [ reset, btn ], attributes = { 'padding-top': '10px'} )
		self.add_row( [ num_result, btnlst ] )
		self.add_row( [ base.Fill( 2 ) ] )

HelperTypes = ( type( InfoBox() ), type( Question() ), type( YesNoQuestion() ), type( SearchForm() ) )
