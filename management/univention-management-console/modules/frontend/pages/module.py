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


import univention.management.console as umc
import univention.management.console.tools as umc_tools
import univention.management.console.protocol as umcp
import univention.management.console.dialog as umcd

import univention.debug as ud

import base
import client
import uniparts
import mapping

import copy

import startup

_ = umc.Translation( 'univention.management.console.frontend' ).translate

class ActiveProcess( object ):
	def __init( self ):
		self.__single = None
		self.__group = None

	def group( self, id ):
		self.__group = id
		self.__single = None

	def single( self, id ):
		self.__single = id
		self.__group = None

	def __nonzero__( self ):
		return bool( ( self.__single and len( self.__single ) ) or \
					 ( self.__group and len( self.__group ) ) )

	def reset( self ):
		self.__single = None
		self.__group = None

	def waitFor( self, timeout = 4 ):
		response = None
		if self.__single:
			response = client.response_wait( self.__single, timeout )
		elif self.__group:
			response = client.response_group_wait( self.__group, timeout )

		if not response:
			response = ()
		if not type( response ) in ( list, tuple ):
			response = ( response, )

		# if this is a _final_ response
		if response and response[ -1 ].status() == 200:
			self.reset()

		return response

class Module( base.Page ):
	def __init__( self, module_name, module ):
		base.Page.__init__( self, module_name, module[ 'short_description' ], closeable = True )
		self.__module = module
		self.__storage = mapping.Storage()
		self.__layout = None
		# TODO: partial response
		self.__layout_in_progress = None
		self.__in_progress = None
		self.__dialog = None
		self.__restore_referrer = False
		self.__operation_is_progress = False

		# check for icon
		if self.__module.has_key( 'icon' ) and self.__module[ 'icon' ]:
			self.icon = umc_tools.image_get( self.__module[ 'icon' ],
											 umc_tools.SIZE_SMALL )
		self.__startups = startup.List()
		self.active = ActiveProcess()
		for name, cmd in module[ 'commands' ].items():
			if cmd[ 'startup' ]:
				req = umcp.Command( args = [ name ], incomplete = True )
				self.__startups.add( req, cmd[ 'short_description' ], cmd[ 'long_description' ],
									 cmd[ 'priority' ], cmd[ 'caching' ] )

		# run command of first category
		cmd = self.__startups[ self.selected ]
		self.active.single( client.request_send( cmd.request ) )
		self.categories = self.__startups.categories()

	def focused( self ):
		cmd = self.__startups[ self.selected ]
		if not self.active and cmd.reload() and not self.__operation_is_progress:
			self.active.single( client.request_send( cmd.request ) )
		self.__operation_is_progress = False

	def layout( self ):
		rows = base.Page.layout( self )
		if not self.active:
			ud.debug(ud.ADMIN, ud.INFO, 'Module.layout: no action yet (might be okay)' )
			# TODO: partial response
# 			if self.__layout_in_progress:
# 				self.__storage.clear()
# 				self.__dialog = self.__storage.to_uniparts( self.__layout_in_progress )
# 				col = uniparts.tablecol( '', {}, { 'obs' : [ self.__dialog ]})
# 				row = uniparts.tablerow( '', {}, { 'obs' : [ col ]})
# 				rows.append( row )
# 				return rows
			# re-create error message
			if self.__startups[ self.selected ].error_active():
				ud.debug(ud.ADMIN, ud.INFO, 'Module.layout: error active' )
				self.__storage.clear()
				self.__layout = self.__startups[ self.selected ].error_message()
			# show old content
			if self.__layout:
				self.__restore_referrer = False
				ud.debug(ud.ADMIN, ud.INFO, 'Module.layout: show cached layout' )
				self.__storage.clear()
				self.__dialog = self.__storage.to_uniparts( self.__layout )
				col = uniparts.tablecol( '', {}, { 'obs' : [ self.__dialog ]})
				row = uniparts.tablerow( '', {}, { 'obs' : [ col ]})
				rows.append( row )
		else:
			ud.debug( ud.ADMIN, ud.INFO, 'Module.layout: active action!! %s' % self.active )
			responses = self.active.waitFor( timeout = 2 )

			# TODO: partial response
# 			if responses and responses[ -1 ].status() == 210:
# 				self._refresh = True
# 				lst = umcd.List()
# 				lst.add_row( [ umcd.Image( 'actions/info', umc_tools.SIZE_MEDIUM ),
# 							   responses[ -1 ].report ] )
# 				frame = umcd.Frame( [ lst ], _( 'Operation in progress ...' ) )
# 				ud.debug( ud.ADMIN, ud.INFO, 'Module.layout: PARTIAL RESPONSE' )
# 				self.__layout_in_progress = umcd.Dialog( [ frame ] )
# 				self.__storage.clear()
# 				self.__dialog = self.__storage.to_uniparts( self.__layout_in_progress )
# 				col = uniparts.tablecol( '', {}, { 'obs' : [ self.__dialog ]})
# 				row = uniparts.tablerow( '', {}, { 'obs' : [ col ]})
# 				rows.append( row )
# 				return rows
# 			else:
# 				self._refresh = False
# 				self.__layout_in_progress = None
			# check if any of the repsonses is an error:
			reports = []
			error_dialog = None
			exception = False
			for response in responses:
				if response.status() != 200:
					reports.append( response.report )
					if response.status() == 500:
						exception = True
						break
			if reports:
				ud.debug( ud.ADMIN, ud.INFO, 'Module.layout: setup error dialog: %s' % \
						  '\n'.join( reports ) )
				cur = self.__startups[ self.selected ]
				cur.cache = copy.deepcopy( self.__layout )
				error_dialog = cur.error_message( '\n'.join( reports ), exception = exception )
				self.active.reset()

			# received a _final_ response
			if not self.active:
				self._refresh = False
				self.__in_progress = None
				# convert dialog to uniparts stuff
				if error_dialog:
					ud.debug( ud.ADMIN, ud.INFO, 'Module.layout: error layout' )
					self.__layout = error_dialog
				else:
					ud.debug( ud.ADMIN, ud.INFO, 'Module.layout: normal layout' )
					cmd = self.__startups[ self.selected ]
					if self.__restore_referrer:
						self.__layout = cmd.cache
						self.__restore_referrer = False
					else:
						self.__layout = responses[ -1 ].dialog
						# should this page be cached?
						if cmd.caching:
							cmd.cache = self.__layout

				self.__storage.clear()
				self.__dialog = self.__storage.to_uniparts( self.__layout )
				col = uniparts.tablecol( '', {}, { 'obs' : [ self.__dialog ] } )
				row = uniparts.tablerow( '', {}, { 'obs' : [ col ] } )
				rows.append( row )
			else:
				self._refresh = True
				self.__operation_is_progress = True
				lst = umcd.List()
				lst.add_row( [ umcd.Image( 'actions/info', umc_tools.SIZE_MEDIUM ),
							   _( 'Operation still in progress. Please wait ...' ) ] )
				frame = umcd.Frame( [ lst ], _( 'Information' ) )
				self.__in_progress = umcd.Dialog( [ frame ] )
# 				self.__layout = self.__in_progress
				self.__storage.clear()
				self.__dialog = self.__storage.to_uniparts( self.__in_progress )
				col = uniparts.tablecol( '', {}, { 'obs' : [ self.__dialog ]})
				row = uniparts.tablerow( '', {}, { 'obs' : [ col ]})
				rows.append( row )
				ud.debug( ud.ADMIN, ud.INFO, 'Module.layout: no UMCP Response (yet)')

		return rows

	def __set_warning( self, invalid_umcp ):
		for params, umcp_item in self.dynamics:
			del umcp_item[ 'warning' ]
		for params, umcp_item in self.inputs:
			del umcp_item[ 'warning' ]

		invalid_umcp[ 'warning' ] = '1'
		self.report = invalid_umcp.syntax.error
		ud.debug( ud.ADMIN, ud.INFO, 'Module.apply: error message: %s' % unicode( self.report ) )

	def __cache_parts( self, parts ):
		for ( uni_part, umcp_part ) in parts:
			umcp_part.cached = uni_part.get_input()

	def __startup_request( self, req ):
		count = 0
		last_selected = self.selected
		index = self.__startups.find( req )
		if index >= 0:
			self.selected = index
			return True

		# new startup command?
		if req.has_flag( 'web:startup' ) and req.has_flag( 'web:startup_format' ):
			options = copy.deepcopy( req.options )
			for name, cmd in self.__module[ 'commands' ].items():
				if req.arguments[ 0 ] == name:
					options[ 'name' ] = cmd[ 'short_description' ]
					break
			title = req.get_flag( 'web:startup_format' ) % options
			title = title.replace( ' ', '&nbsp;' )
			cache = False
			if req.has_flag( 'web:startup_cache' ):
				cache = req.get_flag( 'web:startup_cache' )
			self.selected = self.__startups.add( req, title, title, caching = cache )
			self.categories = self.__startups.categories()
			if self.__startups[ self.selected ].dialog():
				self.__startups[ self.selected ].referrer = \
								 copy.deepcopy( self.__startups[ last_selected ].request )
				self.__startups[ self.selected ].referrer.recreate_id()
			return True
		return False

	def __change_to_selected( self ):
		cmd = self.__startups[ self.selected ]

		# safety check
		if cmd == None:
			# cmd to be selected is None ==> UMC would crash if we continue here, so let's choose another valid startup if available
			ud.debug( ud.ADMIN, ud.WARN, 'Module.__change_to_selected: selected item is None (self.selected=%s) (self.__startups=%s)' % (self.selected, str(self.__startups)))
			for x in self.__startups:
				if not x == None:
					cmd = x
					break
			else:
				ud.debug( ud.ADMIN, ud.ERROR, 'Module.__change_to_selected: all items in self.__startups are None')

		# error message to show?
		if cmd.error_active():
			self.__layout = cmd.error_message()
			return True
		# is this page cached?
		if cmd.caching and cmd.cache:
			ud.debug( ud.ADMIN, ud.INFO, 'Module.__change_to_selected: use cache' )
			self.__layout = cmd.cache
			return True
		self.active.reset()
		self.active.single( client.request_send( cmd.request ) )
		return False

	def apply( self ):
		if self.active: return
		base.Page.apply( self )

		ud.debug( ud.ADMIN, ud.INFO, 'Module.apply' )

		if self.closedPage > -1:
			if self.closedPage == self.selected:
				ud.debug( ud.ADMIN, ud.INFO, 'Module.apply: The closed page is active')

				# is current category a startup dialog that must be closed?
				if self.__startups[ self.selected ].dialog():
					#yes, so we switch to the referrer page
					referrer = self.__startups[ self.selected ].referrer
					self.__startups.remove( self.selected )
					self.categories = self.__startups.categories()
					self.active.single( client.request_send( referrer ) )
					self.selected = self.__startups.find( referrer )
					# referrer already closed?
					if self.selected == -1:
						self.selected = 0
					if self.__startups[ self.selected ].caching and self.__startups[ self.selected ].cache:
						self.__layout = self.__startups[ self.selected ].cache
						return
				else:
					#no, so we go one page back
					self.__startups.remove( self.closedPage )
					self.selected -= 1
					self.categories = self.__startups.categories()
					cmd = self.__startups[ self.selected ]
				self.__change_to_selected()
			else:
				self.__startups.remove( self.closedPage )

				if self.closedPage < self.selected:
					self.selected -= 1
				self.categories = self.__startups.categories()

			self.closedPage = -1

			return

		# if current page contains action items, see if any of these
		# items was pressed
		( self.buttons, self.inputs, self.dynamics ) = self.__storage.sort_by_type()

		# cache current content of input fields
		self.__cache_parts( self.inputs )

		# new category selected?
		if self.selection_changed:
			self.__change_to_selected()
			return
		elif self.reselected:
			cmd = self.__startups[ self.selected ]
			if cmd.caching and cmd.cache:
				self.__layout = cmd.cache
				return
			else:
				self.active.reset()
				self.active.single( client.request_send( cmd.request ) )


		# Handle dynamic elements
		for params, dyn in self.dynamics:
			try:
				if mapping.apply( type( dyn ), self.__storage, dyn, params ):
					return
			except umc.SyntaxError, error:
				self.__set_warning( error.args[ 0 ] )
				return

		for params, umcp_part in self.buttons:
			try:
				requests = mapping.apply( type( umcp_part ), self.__storage, umcp_part,
										  params, self.inputs, self.dynamics )
			except umc.SyntaxError, error:
				self.__set_warning( error.args[ 0 ] )
				return

			if requests:
				# selection button: dynamic action
				if requests[ -1 ] in ( '::dynamic', '::reset' ):
					break
				# selection button: nothing happened
				elif requests[ -1 ] == '::none':
					continue
				# was it a cancel button?
				elif requests[ -1 ] == '::cancel':
					requests = []
				# error message
				elif requests[ -1 ] == '::error':
					self.__startups[ self.selected ].error_reset()
					if self.__startups[ self.selected ].caching:
						self.__layout = self.__startups[ self.selected ].cache
						break
					else:
						requests = [ self.__startups[ self.selected ].request ]

				# is current category a startup dialog that must be closed?
				if self.__startups[ self.selected ].dialog() and umcp_part.close_dialog:
					referrer = self.__startups[ self.selected ].referrer
					use_referrer = self.__startups[ self.selected ].use_referrer()
					if not len( requests ):
						use_referrer = True
					self.__startups.remove( self.selected )
					self.categories = self.__startups.categories()
					idx = self.__startups.find( referrer )
					cmd = self.__startups[ idx ]
					if use_referrer:
						if cmd.caching and cmd.cache:
							self.__restore_referrer = True
							self.selected = idx
							self.__layout = cmd.cache
						else:
							requests.append( referrer )
					else:
						self.selected = 0

				if not self.__restore_referrer:
					if not len( requests ): # cancel button was pressed on a non-closable dialog?
						break
					else:
						req = requests[ -1 ]
						# is a startup request?
						self.__startup_request( req )

				self.active.reset()
				if len( requests ) > 1:
					self.active.group( client.request_group_send( requests ) )
				elif requests:
					self.active.single( client.request_send( requests[ 0 ] ) )
				# there can be just one button that was pressed -> break
				break
		else: # no button was pressed
			self.focused()
