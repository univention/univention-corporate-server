#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  softmon module: revamp module command result for the specific user interface
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
import univention.management.console.values as umcv
import univention.management.console.protocol as umcp
import univention.management.console.tools as umct

import univention.debug as ud

import _syntax

_ = umc.Translation( 'univention.management.console.handlers.softmon' ).translate

class Web( object ):
	def _web_softmon_system_search( self, object, res ):
		ud.debug( ud.ADMIN, ud.INFO, "SOFTMON: revamp: object.options=%s" % object.options )
		ud.debug( ud.ADMIN, ud.INFO, "SOFTMON: revamp: res.dialog=%s" % res.dialog )
		self._create_search_output( object, res, 'softmon/system/search' )


	def _web_softmon_package_search( self, object, res ):
		ud.debug( ud.ADMIN, ud.INFO, "SOFTMON: revamp: object.options=%s" % object.options )
		ud.debug( ud.ADMIN, ud.INFO, "SOFTMON: revamp: res.dialog=%s" % res.dialog )
		self._create_search_output( object, res, 'softmon/package/search' )


	def _create_search_output( self, object, res, umc_command ):
		ud.debug( ud.ADMIN, ud.INFO, "SOFTMON: revamp: umc_command=%s" % umc_command )
		saved_searches = res.dialog.get('saved_searches', [])
		current_search = res.dialog.get('current_search', None)
		filter_items = res.dialog.get('filter_items', None)
		search_results = res.dialog.get('search_results', None)
		max_results_default = res.dialog.get('max_results_default', '20')
		system_versions = res.dialog.get('system_versions', [])
		system_versions_default = res.dialog.get('system_versions_default', '')

		idlist_search = []
		idlist_save = []

		###################################################
		# max results per page
		###################################################

		max_results = umcd.make( ( 'max_results', umcv.Integer( _( 'Results per Page' ) ) ),
								 default = max_results_default, attributes = { 'width' : '100' } )
		idlist_search.append(max_results.id())
		idlist_save.append(max_results.id())

		###################################################
		# search filters
		###################################################

		if umc_command == 'softmon/system/search':
			select = umcd.Selection( ( 'key', _syntax.SoftMonSystemSearchKey() ), default = 'name', attributes = { 'width': '150'} )
			op = umcd.Selection( ( 'operator', _syntax.SoftMonSearchOperator() ), default = 'eq', attributes = { 'width': '150'} )
			values = {
				'name' : umcd.TextInput( ( 'pattern', umc.String( '' ) ), default = '*' ),
				'ucs_version' : umcd.Selection( ( 'pattern', _syntax.SoftMonSystemVersions( system_versions ) ),	default = system_versions_default ),
				'role' : umcd.Selection( ( 'pattern', umc.SystemRoleSelection( '' ) ), default = 'domaincontroler_master' ),
				}
		elif umc_command == 'softmon/package/search':
			select = umcd.Selection( ( 'key', _syntax.SoftMonPackageSearchKey() ), default = 'pkg_name', attributes = { 'width': '150'} )
			op = umcd.Selection( ( 'operator', _syntax.SoftMonSearchOperator() ), default = 'eq', attributes = { 'width': '150'} )
			values = {
				'pkg_name' : umcd.TextInput( ( 'pattern', umc.String( '' ) ), default = '*' ),
				'pkg_version' : umcd.TextInput( ( 'pattern', umc.String( '' ) ), default = '*' ),
				'selected_state' : umcd.Selection( ( 'pattern', _syntax.SoftMonStateSelected( system_versions ) ),	default = None ),
				'installed_state' : umcd.Selection( ( 'pattern', _syntax.SoftMonStateInstalled( system_versions ) ),	default = None ),
				'current_state' : umcd.Selection( ( 'pattern', _syntax.SoftMonStateCurrent( system_versions ) ),	default = None ),
				'ucs_version' : umcd.Selection( ( 'pattern', _syntax.SoftMonSystemVersions( system_versions ) ),	default = system_versions_default ),
				}
		else:
			select = umcd.Text('UNKNOWN UMC COMMAND')

		descr = umcd.DynamicList( self[ umc_command ][ 'filter' ],
								  [ _( 'Searchkey' ), _( 'Operator' ), _( 'Pattern' )  ], [ op, ],
								  modifier = select, modified = values, default = filter_items )
		descr[ 'colspan' ] = '3'
		idlist_search.append(descr.id())
		idlist_save.append(descr.id())

		###################################################
		# select and save search filters
		###################################################

		# text input search name
		new_search_name = umcd.TextInput( ( 'newsearchname', umc.String( _('Save Search Filter As') ) ), default = '', attributes = { 'width': '250'} )
		idlist_save.append(new_search_name.id())

		# search select drop down
		choices = [ { 'description': _('--- Please Select ---'), 'actions': [] } ]
		choicedefault = 0
		current_search_name = None
		for searchitem in saved_searches:
			choices.append( { 'description': searchitem,
							  'actions': [ umcd.Action( umcp.Command( args = [ umc_command ], opts = { 'searchname': searchitem } ), [ max_results.id() ] ) ] } )
			if searchitem == current_search:
				choicedefault = len( choices ) - 1
		saved_search_select = umcd.ChoiceButton( _( 'Select Saved Search Filters') , choices = choices, default = choicedefault, attributes = { 'width': '250'} )
		idlist_search.append(saved_search_select.id())
		idlist_save.append(saved_search_select.id())

		# save button
		req = umcp.Command( args = [ umc_command ], opts= { 'filter': [], 'save': True } )
		save_search_btn = umcd.Button( label = _('Save Search Filter'), tag = 'addfilter', actions = umcd.Action( req, idlist_save ), attributes = { 'width': '250'} )

		# save button
		req = umcp.Command( args = [ umc_command ], opts= { 'searchname': current_search, 'delete': True } )
		delete_search_btn = umcd.Button( label = _('Delete Search Filter'), tag = 'removefilter', actions = umcd.Action( req, [ saved_search_select.id() ] ), attributes = { 'width': '250'} )

		###################################################
		# search button
		###################################################

		req = umcp.Command( args = [ umc_command ], opts= { 'filter': [], 'search': True } )
		search_btn = umcd.SearchButton( umcd.Action( req, idlist_search ) )

		###################################################
		# build layout
		###################################################

		lst1 = umcd.List()
		lst1.add_row( [ saved_search_select, delete_search_btn ] )
		lst1.add_row( [ new_search_name, save_search_btn ] )

		lst2 = umcd.List()
		lst2.add_row( [ descr ] )

		lst3 = umcd.List()
		lst3.add_row( [ max_results, search_btn ] )

		if umc_command == 'softmon/system/search':
			res.dialog = [ umcd.Frame( [ lst1, lst2, lst3 ], _('Search Systems') ) ]
		elif umc_command == 'softmon/package/search':
			res.dialog = [ umcd.Frame( [ lst1, lst2, lst3 ], _('Search Packages') ) ]
		else:
			res.dialog = [ umcd.Frame( [ lst1, lst2, lst3 ], 'UNKNOWN UMC COMMAND' ) ]

		if umc_command == 'softmon/system/search':
			if not search_results == None:
				resultlst = umcd.List()
				resultlst.set_header( [ _( 'system name' ), _( 'UCS role' ), _('current version'), _('collect date') ] )
				for item in search_results:
					resultlst.add_row( [ item['name'], item['role'], item['version'], item['date'] ] )
				res.dialog.append( umcd.Frame( [ resultlst ], _( '%d Search Result(s)' ) % len(search_results) ) )
		elif umc_command == 'softmon/package/search':
			if not search_results == None:
				resultlst = umcd.List()
				resultlst.set_header( [ _( 'system' ), _( 'package' ), _('version'), _('collect date'), _('select state'), _('installation state'), _('current state') ] )
				for item in search_results:
					resultlst.add_row( [ item['sysname'], item['pkgname'], item['version'], item['date'], item['selected_state'], item['installation_state'], item['current_state'] ] )
				res.dialog.append( umcd.Frame( [ resultlst ], _( '%d Search Result(s)' ) % len(search_results) ) )

		self.revamped( object.id(), res )

