#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: manages Univention Baseconfig variables
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

import univention.management.console as umc
import univention.management.console.dialog as umcd

from univention.config_registry_info import ConfigRegistryInfo, Variable

_ = umc.Translation( 'univention.management.console.handlers.baseconfig' ).translate

class BaseconfigCategory( umc.StaticSelection ):
	def __init__( self, required = True ):
		umc.StaticSelection.__init__( self, _( 'Category' ), required = required )

	def choices( self ):
		info = ConfigRegistryInfo()
		lst = []

		# build list of categories
		for cat_name in info.get_categories():
			cat = info.get_category( cat_name )
			lst.append( ( cat_name, cat[ 'name' ] ) )

		return lst

umcd.copy( umc.StaticSelection, BaseconfigCategory )

class BaseconfigCategorySearch( BaseconfigCategory ):
	def __init__( self, required = True ):
		BaseconfigCategory.__init__( self, required )

	def choices( self ):
		lst = BaseconfigCategory.choices( self )
		lst.insert( 0, ( 'all', _( 'All (incl. not registered)' ) ) )
		lst.insert( 0, ( 'all-registered', _( 'All' ) ) )
		return lst

umcd.copy( umc.StaticSelection, BaseconfigCategorySearch )

class BaseconfigCategoryList( BaseconfigCategory ):
	def __init__( self, required = True ):
		BaseconfigCategory.__init__( self, required = required )
		self.label = _( 'List of Categories' )
		self.multivalue = True

umcd.copy( umc.StaticSelection, BaseconfigCategoryList )

class BaseconfigTypes( umc.StaticSelection ):
	def __init__( self, required = True ):
		umc.StaticSelection.__init__( self, _( 'Types' ), required = required )

	def choices( self ):
		return ( ( 'str', _( 'String' ) ), )

umcd.copy( umc.StaticSelection, BaseconfigTypes )

class BaseconfigSearchKeys( umc.StaticSelection ):
	def __init__( self, required = True ):
		umc.StaticSelection.__init__( self, _( 'Search Key' ), required = required )

	def choices( self ):
		return ( ( 'variable', _( 'Variable' ) ), ( 'value', _( 'Value' ) ),
				 ( 'description', _( 'Description' ) ) )

umcd.copy( umc.StaticSelection, BaseconfigSearchKeys )

# attribute types
key = umc.String( _( 'Key' ), regex = '^[a-z0-9A-Z/_]*$' )
filter = umc.String( '&nbsp;', required = False )
value = umc.String( _( 'Value' ), required = False )
bctype = BaseconfigTypes()
category = BaseconfigCategory()
categorysearch = BaseconfigCategorySearch()
categories = BaseconfigCategoryList( required = False )
searchkey = BaseconfigSearchKeys()
descr_text = umc.String( _( 'Description' ), required = False )
descr_lang = umc.LanguageSelection( _( 'Language' ) )
descr = umc.MultiDictValue( _( 'Multilinugal Description' ),
								 syntax = { 'text' : descr_text, 'lang' : descr_lang } )
