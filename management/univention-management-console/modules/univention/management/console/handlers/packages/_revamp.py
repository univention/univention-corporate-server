#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  packages module: revamp module command result for the specific user interface
#
# Copyright 2007-2010 Univention GmbH
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
import univention.management.console.protocol as umcp
import univention.management.console.tools as umct

import univention.debug as ud

import tools, string

_ = umc.Translation( 'univention.management.console.handlers.packages' ).translate

class Web( object ):
	def _web_packages_search( self, object, res ):
		ud.debug( ud.ADMIN, ud.INFO, '_web_packages_search: %s' % object)
		main = []
		# add search form
		select = umcd.make( self[ 'packages/search' ][ 'section' ],
						default = object.options.get( 'section', 'all' ),
						attributes = { 'width' : '200' } )
		key = umcd.make( self[ 'packages/search' ][ 'key' ],
						default = object.options.get( 'key', 'name' ),
						attributes = { 'width' : '200' } )
		text = umcd.make( self[ 'packages/search' ][ 'pattern' ],
						default = object.options.get( 'pattern', '*' ),
						attributes = { 'width' : '250' } )
		installed = umcd.make( self[ 'packages/search' ][ 'installed' ],
						default = object.options.get( 'installed', False ) )

		form = umcd.SearchForm( 'packages/search', [ [ ( select, 'all' ), (installed, 'installed') ],
													   [ ( key, 'name' ), ( text, '*' ) ] ] )
		main.append( [ form ] )

		# append result list
		if not object.incomplete:
			result = umcd.List()

			if res.dialog:
				result.set_header( [ _( 'Package' ), _('Section'), _( 'Installed' ), _('Summary') ] )
				for package in res.dialog:
					if package.isInstalled:
						icon = umcd.Image( 'actions/yes', umct.SIZE_SMALL )
						req = umcp.Command( args = [ 'packages/show' ],
											opts = { 'package' : package.name, 'installed' : True, 'section': object.options.get( 'section', 'all' ), 'key': object.options.get( 'key', 'name' ) } )
						req.set_flag( 'web:startup', True )
						req.set_flag( 'web:startup_cache', False )
						req.set_flag( 'web:startup_dialog', True )
						req.set_flag( 'web:startup_referrer', True )
						req.set_flag( 'web:startup_format', _( 'Show package: %(package)s' ) )
						btn = umcd.Button( package.name, 'packages/module', umcd.Action( req ), close_dialog = False )
					else:
						icon = umcd.Image( 'actions/no', umct.SIZE_SMALL )
						req = umcp.Command( args = [ 'packages/show' ],
											opts = { 'package' : package.name, 'installed' : False, 'section': object.options.get( 'section', 'all' ), 'key': object.options.get( 'key', 'name' ) } )
						req.set_flag( 'web:startup', True )
						req.set_flag( 'web:startup_cache', False )
						req.set_flag( 'web:startup_dialog', True )
						req.set_flag( 'web:startup_referrer', True )
						req.set_flag( 'web:startup_format', _( 'Show package: %(package)s' ) )
						btn = umcd.Button( package.name, 'packages/module', umcd.Action( req ), close_dialog = False )

					result.add_row( [ btn, package.section, icon, package.summary ] )
			else:
				result.add_row( [ _( 'No packages were found.' ) ] )

			main.append( umcd.Frame( [ result ], _( 'Search results' ) ) )

		res.dialog = main

		self.revamped( object.id(), res )

	def _web_packages_show( self, object, res ):
		result = umcd.List()
		package = res.dialog
		if package.isInstalled:
			colspan = 2
			if package.isUpgradable:
				colspan += 1

			result.add_row( [ umcd.Text( '%s: ' % (self['packages/show'].values['package'].label ) ), umcd.Text( '%s' % (package.name), attributes = { 'colspan' : str( colspan ) }  ) ] )
			result.add_row( [ umcd.Text( '%s: ' % (self['packages/show'].values['summary'].label ) ), umcd.Text( '%s' % (package.summary), attributes = { 'colspan' : str( colspan ) } ) ] )
			result.add_row( [ umcd.Text( '%s: ' % (self['packages/show'].values['section'].label ) ), umcd.Text( '%s' % (package.section), attributes = { 'colspan' : str( colspan ) } ) ] )
			result.add_row( [ umcd.Text( '%s: ' % (self['packages/show'].values['installed'].label ) ), umcd.Image( 'actions/yes', umct.SIZE_SMALL )  ] )
			result.add_row( [ umcd.Text( '%s: ' % (self['packages/show'].values['installedVersion'].label ) ), umcd.Text( '%s' % (package.installedVersion), attributes = { 'colspan' : str( colspan ) } ) ] )
			if package.isUpgradable:
				result.add_row( [ umcd.Text( '%s: ' % (self['packages/show'].values['isUpgradable'].label ) ), umcd.Image( 'actions/yes', umct.SIZE_SMALL ) ] )
			else:
				result.add_row( [ umcd.Text( '%s: ' % (self['packages/show'].values['isUpgradable'].label ) ), umcd.Image( 'actions/no', umct.SIZE_SMALL ) ] )
			result.add_row( [ umcd.Text( '%s: ' % (self['packages/show'].values['packageSize'].label ) ), umcd.Text( '%s' % (package.packageSize), attributes = { 'colspan' : str( colspan ) } ) ] )
			result.add_row( [ umcd.Text( '%s: ' % (self['packages/show'].values['priority'].label ) ), umcd.Text( '%s' % (package.priority), attributes = { 'colspan' : str( colspan ) } ) ] )
			result.add_row( [ umcd.Text( '%s: ' % (self['packages/show'].values['description'].label ) ), umcd.Text( '%s' % (package.description), attributes = { 'colspan' : str( colspan ) } ) ] )
			req = umcp.Command( args = [ 'packages/uninstall' ], opts = { 'package' : package.name } )
			req.set_flag( 'web:startup', True )
			req.set_flag( 'web:startup_cache', True )
			req.set_flag( 'web:startup_dialog', True )
			req.set_flag( 'web:startup_referrer', True )
			req.set_flag( 'web:startup_format', _( 'Uninstall package: %(package)s' ) )
			req_upgrade = umcp.Command( args = [ 'packages/install' ], opts = { 'package' : package.name } )
			req_upgrade.set_flag( 'web:startup', True )
			req_upgrade.set_flag( 'web:startup_cache', True )
			req_upgrade.set_flag( 'web:startup_dialog', True )
			req_upgrade.set_flag( 'web:startup_referrer', True )
			req_upgrade.set_flag( 'web:startup_format', _( 'Upgrade package: %(package)s' ) )
			if package.isUpgradable:
				result.add_row( [ umcd.Button( label = _('Upgrade'), tag = 'actions/ok', actions = [  umcd.Action( req_upgrade )], close_dialog = False ), umcd.Button( label = _('Uninstall'), tag = 'actions/ok', actions = [  umcd.Action( req ) ]) , umcd.CancelButton() ] )
			else:
				result.add_row( [ umcd.Button( label = _('Uninstall'), tag = 'actions/ok', actions = [  umcd.Action( req ) ], close_dialog = False), umcd.CancelButton( ) ] )
		else:
			result.add_row( [ umcd.Text( '%s: ' % (self['packages/show'].values['package'].label ) ), umcd.Text( '%s' % (package.name) ) ] )
			result.add_row( [ umcd.Text( '%s: ' % (self['packages/show'].values['summary'].label ) ), umcd.Text( '%s' % (package.summary) ) ] )
			result.add_row( [ umcd.Text( '%s: ' % (self['packages/show'].values['section'].label ) ), umcd.Text( '%s' % (package.section) ) ] )
			result.add_row( [ umcd.Text( '%s: ' % (self['packages/show'].values['installed'].label ) ), umcd.Image( 'actions/no', umct.SIZE_SMALL ) ] )
			result.add_row( [ umcd.Text( '%s: ' % (self['packages/show'].values['packageSize'].label ) ), umcd.Text( '%s' % (package.packageSize) ) ] )
			result.add_row( [ umcd.Text( '%s: ' % (self['packages/show'].values['priority'].label ) ), umcd.Text( '%s' % (package.priority) ) ] )
			result.add_row( [ umcd.Text( '%s: ' % (self['packages/show'].values['description'].label ) ), umcd.Text( '%s' % (package.description) ) ] )
			req = umcp.Command( args = [ 'packages/install' ], opts = { 'package' : package.name} )
			req.set_flag( 'web:startup', True )
			req.set_flag( 'web:startup_cache', True )
			req.set_flag( 'web:startup_dialog', True )
			req.set_flag( 'web:startup_referrer', True )
			req.set_flag( 'web:startup_format', _( 'Install package: %(package)s' ) )
			result.add_row( [ umcd.Button( label = _('Install'), tag = 'actions/ok', actions = [  umcd.Action( req ) ], close_dialog = False ), umcd.CancelButton() ] )

		res.dialog = [ result ]
		
		self.revamped( object.id(), res )

	def __remove_status_messages( self, text ):
		result = []
		for line in text.split('\n'):
			if line.startswith('\r'):
				continue
			result.append(line)
		return string.join(result, '\n')
	
	def _web_packages_install( self, object, res ):
		result = umcd.List()
		returncode, log = res.dialog
		if returncode == 0:
			result.add_row( [ umcd.Image( 'actions/yes', umct.SIZE_LARGE ), umcd.HTML('<h2>' + _( '%s was successful installed!' ) % object.options['package'] + '</h2>') ] )
		else:
			result.add_row( [ umcd.Image( 'actions/no', umct.SIZE_LARGE ), umcd.HTML('<h2>' + _( 'Failed to install %s!' ) % object.options['package'] + '</h2>') ] )
		html = '<h2>' + _('Log Message') + '</h2>' + '<pre>' + self.__remove_status_messages(log) + '</pre>'
		result.add_row( [ umcd.HTML( html, attributes = { 'colspan' : str( 2 ) } ) ] )
		result.add_row( [ umcd.CloseButton( )] )
		res.dialog = [ result ]

		self.revamped( object.id(), res )

	def _web_packages_uninstall( self, object, res ):
		result = umcd.List()
		returncode, log = res.dialog
		if returncode == 0:
			result.add_row( [ umcd.Image( 'actions/yes', umct.SIZE_LARGE ), umcd.HTML('<h2>' + _( '%s was successful uninstalled!' ) % object.options['package'] + '</h2>') ] )
		else:
			result.add_row( [ umcd.Image( 'actions/no', umct.SIZE_LARGE ), umcd.HTML('<h2>' + _( 'Failed to uninstall %s!' ) % object.options['package'] + '</h2>') ] )
		html = '<h2>' + _('Log Message') + '</h2>' + '<pre>' + self.__remove_status_messages(log) + '</pre>'
		result.add_row( [ umcd.HTML( html, attributes = { 'colspan' : str( 2 ) } ) ] )
		result.add_row( [ umcd.CloseButton( )] )
		res.dialog = [ result ]

		self.revamped( object.id(), res )
	
	
