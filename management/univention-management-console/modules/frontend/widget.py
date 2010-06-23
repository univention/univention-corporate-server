#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  web interface: main widget
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
		# create default page: overview
		self.pages.extend( [ pages.Overview( self ) ] )

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
		self.pages.append( page )
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
		# this might happen if the module wants to exit (status code 250; see protocol spec)
		# in that case we return to the overview
		if not page_layout:
			del self.pages[ self.selected ]
			self.selected = 0
			page_layout = self.pages[ self.selected ].layout()
		for i in range( 0, len( self.pages ) ):
			pages.append( self.pages[ i ].title( selected = ( i == self.selected ) ) )

		objects.append( self.div_start('content-wrapper', divtype='id'))
		args = { 'buttons' : pages, 'selected' : self.selected }
		self.notebook = uniparts.notebook( '', {}, args )
		objects.append( self.notebook )
		objects.append( self.div_start('content', divtype='id'))

		# layout current page
		inner_opts = { 'obs': page_layout }
		inner_table = uniparts.table( 'testtesttest', { 'type' : 'inner_table' }, inner_opts )

		col1 = uniparts.tablecol( '', {}, { 'obs': [ inner_table ] } )
		row1 = uniparts.tablerow( '', {}, { 'obs' : [ col1 ] } )
		opts = { 'type' : 'content_main_menuless' }
		objects.append( uniparts.table( '', opts, { 'obs' : [ row1 ] } ) )

		# check for refresh
		self.__refresh[ self.selected ] = self.pages[ self.selected ].refresh()

		objects.append( self.div_stop('content') )
		objects.append( self.div_stop('content-wrapper') )

		return objects

	def div_start(self, div, divtype='id'):
		div_header = uniparts.htmltext ('', {}, \
			{'htmltext': ["""
				<div %(type)s="%(div)s">
				""" % {'div': div, 'type': divtype }]})
		return div_header

	def div_stop(self, div=None):
		div_header = uniparts.htmltext ('', {}, \
			{'htmltext': ["""
				</div>
				""" ]})
		return div_header

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
			if self.selected == None:
				self.selected = 0
			if self.closedModule <= self.selected and self.selected > 0:
				self.selected -= 1
			self.pages[ self.selected ].focused()
		else:
			if self.selected != self.notebook.getselected():
				self.selected = self.notebook.getselected()
				if self.selected == None:
					self.selected = 0
				self.pages[ self.selected ].focused()
			else:
				self.pages[ self.selected ].apply()
