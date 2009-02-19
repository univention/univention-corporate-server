#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  base class for UMC module pages
#
# Copyright (C) 2006-2009 Univention GmbH
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

import uniparts
import univention.management.console as umc
import univention.management.console.tools as umc_tools
import univention.debug as ud

_ = umc.Translation( 'univention.management.console.frontend' ).translate

class Page( object ):
	def __init__( self, id, title, closeable = False ):
		self.__title = title
		self.id = id
		self.selected = 0
		self.selection_changed = True
		self.reselected = False
		self.page_closeable = closeable
		self.closed = False
		self.categories = []
		self.categorylist = None
		self.report = ''
		self.icon = None
		self._refresh = False

	def title( self, selected = False ):
		if self._refresh:
			if selected:
				status = umc_tools.image_get( 'actions/progress-active', umc_tools.SIZE_SMALL )
			else:
				status = umc_tools.image_get( 'actions/progress', umc_tools.SIZE_SMALL )
			return ( self.__title, self.__title, self.icon, status, self.page_closeable )
		return ( self.__title, self.__title, self.icon, None, self.page_closeable )

	def layout( self ):
		rows = []
		category_elements = []

		for category in self.categories:
			closeable = '0'
			# (name, description, is_startup )
			if len(category) > 2 and category[2] == False:
				closeable = '1'
			# an example with a icon in the category line
			# category_elements.append( { 'description' : category, 'icon' : '/style/down.gif', 'closeable' : closeable } )
			category_elements.append( { 'description' : category, 'closeable' : closeable } )

		args = { 'categories' : category_elements , 'selected' : self.selected }
		self.categorylist = uniparts.categorylist( '', {}, args )
		args = { 'colspan' : '2', 'type' : 'login_layout' }
		col1 = uniparts.tablecol( '', args, { 'obs' : [  self.categorylist ] } )
		rows.append( uniparts.tablerow( '', {}, { 'obs' : [ col1 ] } ) )

		return rows

	def refresh( self ):
		'''This method should return True if this page needs to be
		reloaded, e.g. to update a status message.'''
		return self._refresh

	def focused( self ):
		'''this method is called when a page is selected via the
		notebook tabs'''

	def apply( self ):
		selected = self.categorylist.getselected()
		# check if the current category is re-selected
		if getattr( self.categorylist, 'bpressed', 0 ) and self.selected == selected:
			self.reselected = True
		else:
			self.reselected = False

		self.selection_changed = ( self.selected != selected )
		self.selected = selected

		self.closedPage = self.categorylist.getclosed()
