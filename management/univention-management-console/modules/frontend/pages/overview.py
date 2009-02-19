#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
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


import univention.management.console.tools as umc_tools
import univention.management.console.protocol as umcp
import univention.management.console as umc

import univention.debug as ud

import base

import client

import uniparts

import module

_ = umc.Translation( 'univention.management.console.frontend' ).translate

class Overview( base.Page ):
	def __init__( self, notebook ):
		base.Page.__init__( self, 'overview', _( 'Overview' ) )
		self.__notebook = notebook
		self.modules = {}
		self.module_categories = {}
		self.module_buttons = {}
		self.__build_module_list()

	def __generate_module_icon( self, iconpath, description ):
		rows = []

		iconbutton = uniparts.button( '',{ 'icon' : umc_tools.image_get( iconpath, size = umc_tools.SIZE_LARGE ) },
									  { "helptext" : description } )
		rows.append( uniparts.tablerow( "", { 'type' : 'desktopicon' },
										{ 'obs' : [ uniparts.tablecol( '', { 'type' : 'desktopicon' },
																	   { 'obs' : [ iconbutton ] } ) ] } ) )

		descriptionbutton = uniparts.button( description, { 'link' : '1' }, { 'helptext' : description } )
		col1 = uniparts.tablecol( '', { 'type' : 'desktopicon' }, { 'obs' : [ descriptionbutton ] } )
		rows.append( uniparts.tablerow( '', { 'type' : 'desktopicon' }, { 'obs' : [ col1 ] } ) )

		return ( iconbutton, descriptionbutton,
				 uniparts.table( '', { 'type' : 'desktopicon' }, { 'obs' : rows } ) )

	def __build_module_list( self ):
		req = umcp.Request( 'GET', args = [ 'modules/list' ] )
		id = client.request_send( req )
		response = client.response_wait( id, timeout = 10 )
		if response:
			self.modules = response.body[ 'modules' ]
			self.module_categories = response.body[ 'categories' ]
			for cat in self.module_categories:
				self.categories.append( ( cat.name, cat.description ) )
		# TODO: not implemented yet
# 		self.categories.append( ( _( 'Favorites' ), _( 'Favorite Univention Management Console Modules' ) ) )

	def layout( self ):
		ud.debug( ud.ADMIN, ud.INFO, 'Overview.layout' )
		rows = base.Page.layout( self )

		buttonrows = []
		buttoncols = []
		iconcnt = 0
		# find current category
		# favorites is selected
		if self.selected == ( len( self.module_categories ) ):
			pass
		else:
			cat = self.module_categories[ self.selected ].id
			for name, module in self.modules.items():
				if not cat in module[ 'categories' ]:
					continue
				icon = module[ 'icon' ]
				but1, but2, btable = self.__generate_module_icon( icon, module[ 'short_description' ] )
				buttoncols.append( uniparts.tablecol( '', { }, { 'obs' : [ btable ] } ) )
				self.module_buttons[ name ] = ( but1, but2 )
				iconcnt += 1
				if iconcnt >= 10:
					buttonrows.append( uniparts.tablerow( '', { }, { 'obs' : buttoncols } ) )
					buttoncols = []
					iconcnt = 0

		if buttoncols:
			buttonrows.append( uniparts.tablerow( '', { }, { 'obs' : buttoncols } ) )
		desktop_content = uniparts.table( '', { }, { 'obs': buttonrows } )
		desktop_table = uniparts.table( '', { 'type' : 'desktop' }, { 'obs': [ uniparts.tablerow( '', { 'type' : 'desktop' }, { 'obs' : [ uniparts.tablecol( '', { 'type' : 'desktop' }, { 'obs' : [ desktop_content ] } ) ] } ) ] } )
		col1 = uniparts.tablecol( '', {}, { 'obs' : [ desktop_table ] } )
		rows.append( uniparts.tablerow( '', {}, { 'obs' : [ col1 ] } ) )

		rows.append(uniparts.tablerow("",{},{"obs":[
				uniparts.tablecol("",{"colspan":"2",'type':'about_layout'},{"obs":[]})
				]}))

		self.logoutbutton = uniparts.button( _( 'Logout from Univention Management Console' ), { 'icon' : '/style/cancel.gif' }, { 'helptext' : _( 'Logout from Univention Management Console' ) } )
		rows.append(uniparts.tablerow("",{},{"obs":[
				uniparts.tablecol("",{'type':'about_layout'},{"obs":[ self.logoutbutton ]}),
				]}))

		return rows

	def apply( self ):
		ud.debug( ud.ADMIN, ud.INFO, 'Overview.apply' )
		base.Page.apply( self )
		# see if the user has clicked anything on this page
		if self.logoutbutton.pressed():
			self.__notebook.logout()
		else:
			for name, ( but1, but2 ) in self.module_buttons.items():
				if but1.pressed() or but2.pressed():
					if self.__notebook.existsPage( name ):
						self.__notebook.selectPage( name )
					else:
						mod = module.Module( name, self.modules[ name ] )
						self.__notebook.appendPage( mod )
