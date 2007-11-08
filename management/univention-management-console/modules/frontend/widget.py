#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  web interface: main widget
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

import univention.management.console.protocol as umcp
import univention.management.console as umc
import univention.debug as ud

import client
import uniparts
import pages

_ = umc.Translation( 'univention.management.console.frontend' ).translate

class Notebook( object ):
	def __init__( self, save ):
		self.save = save
		self.pages = []
		self.selected = 0
		self.__refresh = {}
		self.notebook = None
		# create default pages: overview, about
		self.pages.extend( [ pages.Overview( self ), pages.About( self ) ] )

	def existsPage( self, name ):
		'''Checks whether a page already exists or not. This is used to
		determine if a module page is already opened.'''
		for page in self.pages:
			if page.id == name:
				return True
		return False

	def selectPage( self, name ):
		'''Changes the currently selected page of the notbook if found
		in the list of existing pages'''
		for i in range( len( self.pages ) ):
			if self.pages[ i ].id == name:
				self.selected = i
				break

	def appendPage( self, page, select = True, icon = None ):
		"""Append a new page to the notebook (before about page) and if
		the argument 'selected' is set to True the page will be the new
		current page"""
		# insert before 'about' page
		self.pages.insert( -1, page )
		if select:
			self.selectPage( page.id )

	def report( self ):
		ud.debug(ud.ADMIN, ud.INFO, 'SYNTAX: Notebook.report: report: %s' % self.pages[ self.selected ].report )
		if self.pages[ self.selected ].report:
			return self.pages[ self.selected ].report
		return ''

	def refresh( self ):
		return self.__refresh.has_key( self.selected ) and \
			   self.__refresh[ self.selected ]

	def layout( self ):
		'''Creates the unipart object for the notebook and the current
		page'''
		objects = []
		pages = []
		page_layout = self.pages[ self.selected ].layout()
		for i in range( 0, len( self.pages ) ):
			pages.append( self.pages[ i ].title( selected = ( i == self.selected ) ) )

		args = { 'buttons' : pages, 'selected' : self.selected }
		self.notebook = uniparts.notebook( '', {}, args )
		objects.append( self.notebook )

		# layout current page
		inner_opts = { 'obs': page_layout }
		inner_table = uniparts.table( '', { 'type' : 'inner_table' }, inner_opts )

		col1 = uniparts.tablecol( '', {}, { 'obs': [ inner_table ] } )
		row1 = uniparts.tablerow( '', {}, { 'obs' : [ col1 ] } )
		opts = { 'type' : 'content_main_menuless' }
		objects.append( uniparts.table( '', opts, { 'obs' : [ row1 ] } ) )

		# check for refresh
		self.__refresh[ self.selected ] = self.pages[ self.selected ].refresh()

		return objects

	def logout ( self ):
		self.save.put( 'logout' , '1')

	def apply( self ):
		'''If the selection has changed the user has selected another
		page/module. Otherwise the user has clicked anything on the
		current page that should be evaulated by the associated object'''
		self.closedModule = self.notebook.getclosed()
		ud.debug(ud.ADMIN, ud.INFO, 'SYNTAX: Notebook.apply: closedModule=%s' % self.closedModule )
		if self.closedModule > -1:

			# send EXIT to module
			ud.debug(ud.ADMIN, ud.INFO, 'SYNTAX: Notebook.apply: sending EXIT to module %s' % self.pages[ self.closedModule ].id )
			req = umcp.Request( 'EXIT', args = [ self.pages[ self.closedModule ].id ] )
			id = client.request_send( req )
			response = client.response_wait( id, timeout = 10 )
			if response:
				resp = response.body.get('status', None)
				ud.debug(ud.ADMIN, ud.INFO, 'SYNTAX: Notebook.apply: EXIT response: %s' % resp )

			del self.pages[ self.closedModule ]
			self.selected = self.notebook.getselected()
			if self.closedModule <= self.selected and self.selected > 0:
				self.selected -= 1
			self.pages[ self.selected ].focused()
		else:
			if self.selected != self.notebook.getselected():
				self.selected = self.notebook.getselected()
				self.pages[ self.selected ].focused()
			else:
				self.pages[ self.selected ].apply()
