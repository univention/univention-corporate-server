#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module packages: handle debian packages
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
import univention.management.console.handlers as umch
import univention.management.console.dialog as umcd
import univention.management.console.tools as umct

import os, re

import notifier.popen

import _revamp

import univention.debug as ud

_ = umc.Translation( 'univention.management.console.handlers.packages' ).translate

name = 'packages'
icon = 'packages/module'
short_description = _( 'Package management' )
long_description = _( 'Install and uninstall software packages' )
categories = [ 'all', 'system' ]

sections = tools.get_sections()

class PackageSections( umc.StaticSelection ):
	def __init__( self ):
		umc.StaticSelection.__init__( self, _( 'Package categories' ) )

	def choices( self ):
		list = [ ( 'all', _( 'All' ) ) ]
		for section in sections:
			list.append( ( section, section ) )
		return list

class PackageSearchKey( umc.StaticSelection ):
	def __init__( self ):
		umc.StaticSelection.__init__( self, _( 'Search key' ) )
		self._choices = []

	def choices( self ):
		return ( ( 'name', _( 'Name' ) ),
				 ( 'description', _( 'Description' ) ) )

umcd.copy( umc.StaticSelection, PackageSections )
umcd.copy( umc.StaticSelection, PackageSearchKey )

section_type = PackageSections()
key_type = PackageSearchKey()

command_description = {
	'packages/search' : umch.command(
		short_description = _( 'Packages' ),
		method = 'packages_search',
		values = {	'section': section_type,
					'installed': umc.Boolean( _( 'Installed packages only' )),
					'key' : key_type,
					'pattern' : umc.String( _( 'Pattern' ) ) },
		startup = True,
		caching = True,
	),
	'packages/show' : umch.command(
		short_description = _( 'Show package' ),
		method = 'packages_show',
		values = {	'package' : umc.String( _( 'Package' ) ),
					'section': umc.String( _( 'Section' ) ),
					'installed' : umc.Boolean( _('Installed') ),
					'description': umc.String(_('Description')),
					'installedVersion': umc.String(_('Installed version')),
					'isUpgradable': umc.Boolean(_('Upgradeable')),
					'packageSize': umc.String(_('Package size')),
					'priority': umc.String(_('Priority')) ,
					'sourcePackageName': umc.String(_('Source package name')),
					'summary': umc.String(_('Summary'))
					},
	),
	'packages/install' : umch.command(
		short_description = _( 'Install package' ),
		method = 'packages_install',
		values = {	'package' : umc.String( _( 'Package' ) ) },
	),
	'packages/uninstall' : umch.command(
		short_description = _( 'Uninstall package' ),
		method = 'packages_uninstall',
		values = {	'package' : umc.String( _( 'Package' ) ) },
	),
	'packages/upgrade' : umch.command(
		short_description = _( 'Upgrade package' ),
		method = 'packages_upgrade',
		values = {	'package' : umc.String( _( 'Package' ) ) },
	),
}

class handler( umch.simpleHandler, _revamp.Web ):
	def __init__( self ):
		global command_description
		umch.simpleHandler.__init__( self, command_description )

	def packages_search( self, object ):
		if object.incomplete:
			self.finished( object.id(), None )
			pass
		else:
			ud.debug(ud.ADMIN, ud.INFO, 'packages_search: %s ' % object.options)
			infos = tools.search_packages(object.options[ 'section' ], object.options[ 'pattern' ], object.options[ 'installed' ], object.options[ 'key' ])
			self.finished( object.id(), infos )

	def packages_show( self, object ):
		infos = tools.get_package_info( object.options['package'] )
		if infos:
			self.finished( object.id(), infos )
		else:
			self.finished( object.id(), None )

	def packages_install( self, object ):
		result = tools.install_package ( object.options['package'] )
		self.finished( object.id(), result )

	def packages_upgrade( self, object ):
		result = tools.upgrade_package ( object.options['package'] )
		self.finished( object.id(), result )

	def packages_uninstall( self, object ):
		result = tools.uninstall_package ( object.options['package'] )
		self.finished( object.id(), result )
