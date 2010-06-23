# -*- coding: utf-8 -*-
#
# Univention Management Console
#  baseconfig module: revamps dialog result for the web interface
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

import operator
import string
import locale

import univention.management.console as umc
import univention.management.console.dialog as umcd
import univention.management.console.protocol as umcp

import univention.debug as ud

from univention.config_registry_info import ConfigRegistryInfo, set_language

import _types

locale_language_code=locale.getlocale(locale.LC_MESSAGES)[0]
if locale_language_code and len(locale_language_code) >= 2:
	locale_language_code=locale_language_code[:2] # get ISO 3166-1 alpha-2 code
	set_language(locale_language_code)
else:
	set_language('en')
del locale_language_code

_ = umc.Translation( 'univention.management.console.handlers.baseconfig' ).translate

class Web( object ):
	def _web_baseconfig_search( self, object, res ):
		ud.debug( ud.ADMIN, ud.INFO, 'Baseconfig.search: options: %s' % str( object.options ) )
		main = []
		info = ConfigRegistryInfo()

		# dictionary of baseconfig variables
		( key, filter, category ), variables = res.dialog

		# add search form
		select = umcd.make( self[ 'baseconfig/search' ][ 'category' ], default = category,
							attributes = { 'width' : '200' } )
		key = umcd.make( self[ 'baseconfig/search' ][ 'key' ], default = key,
						 attributes = { 'width' : '200' } )
		text = umcd.make( self[ 'baseconfig/search' ][ 'filter' ], default = filter,
						  attributes = { 'width' : '250' } )

		form = umcd.SearchForm( 'baseconfig/search', [ [ ( select, 'all' ), '' ],
													   [ ( key, 'variable' ), ( text, '*' ) ] ] )
		main.append( [ form ] )

		# append result list
		if not object.incomplete:
			result = umcd.List()

			if variables:
				result.set_header( [ _( 'Variable' ), _( 'Value' ), _( 'Description' ),
									 _( 'Categories' ) ] )
				lines = []
				for key, var in variables.items():
					if var.get( 'categories', None ):
						cat_names = []
						for cat_name in var[ 'categories' ].split( ',' ):
							cat = info.get_category( cat_name )
							if cat:
								cat_names.append( cat[ 'name' ] )
						cat_text = ', '.join( cat_names )
					else:
						cat_text = ''

					try:
						descr_text = var[ 'description' ]
					except KeyError:
						descr_text = ''
					if len( descr_text ) > 40:
						try:
							descr_text = '%s&nbsp;...' % str( unicode( descr_text )[ : 40 ] )
						except:
							# buggy encoding may cause trouble -> ignore it
							descr_text = ''

					value = var.value
					if not isinstance( value, basestring ):
						value = ''
					if len( value ) > 40:
						value = '%s&nbsp;...' % str( unicode( value )[ : 40 ] )

					value.replace( ' ', '&nbsp;' )
					lines.append( [ key, value, descr_text, cat_text ] )

				# sort by variable
				lines = sorted( lines, key = operator.itemgetter( 0 ) )

				for key, value, descr_text, cat_text in lines:
					req_set = umcp.Command( args = [ 'baseconfig/show' ], opts = { 'key' : key } )
					req_set.set_flag( 'web:startup', True )
					req_set.set_flag( 'web:startup_reload', True )
					req_set.set_flag( 'web:startup_cache', True )
					req_set.set_flag( 'web:startup_dialog', True )
					req_set.set_flag( 'web:startup_format', _( 'Variable: %(key)s' ) )
					btn = umcd.Button( key, 'baseconfig/variable', umcd.Action( req_set ) )
					result.add_row( [ btn, value, descr_text, cat_text ] )
			else:
				result.add_row( [ _( 'No configuration registry variables were found.' ) ] )

			main.append( umcd.Frame( [ result ], _( 'Search results' ) ) )

		res.dialog = main
		self.revamped( object.id(), res )

	def _web_baseconfig_show( self, object, res ):
		main = []
		form = umcd.List()

		ud.debug( ud.ADMIN, ud.INFO, 'Baseconfig.show: options: %s' % str( res.dialog ) )
		variable = res.dialog
		# name
		if variable != None:
			varname = umcd.make_readonly( self[ 'baseconfig/set' ][ 'key' ],
										  default = object.options.get( 'key', '' ) )
		else:
			varname = umcd.make( self[ 'baseconfig/set' ][ 'key' ] )

		# value
		if variable != None:
			value = umcd.make( self[ 'baseconfig/set' ][ 'value' ], default = variable.value )
		else:
			value = umcd.make( self[ 'baseconfig/set' ][ 'value' ] )
		form.add_row( [ varname, value ] )

		# type
		if variable != None:
			vartype = umcd.make( self[ 'baseconfig/set' ][ 'type' ], default = variable.get( 'type', 'str' ) )
		else:
			vartype = umcd.make( self[ 'baseconfig/set' ][ 'type' ] )

		# category
		fields = [ umcd.make( ( None, _types.category ) ) ]
		if variable != None:
			default = []
			cats = variable.get( 'categories', None )
			if cats:
				info = ConfigRegistryInfo( install_mode = True )
				info.load_categories()
				for cat in cats.split( ',' ):
					cat_info = info.get_category( cat )
					if cat_info:
						default.append( ( string.lower( cat ), cat_info[ 'name' ] ) )
					else:
						default.append( ( string.lower( cat ), '' ) )
			category = umcd.make( self[ 'baseconfig/set' ][ 'categories' ], fields = fields,
								  default = default )
		else:
			category = umcd.make( self[ 'baseconfig/set' ][ 'categories' ], fields = fields )

		form.add_row( [ vartype, category ] )

		# description
		default = []
		if variable:
			descr = variable.get_dict( 'description' )
			for lang, text in descr.items():
				default.append( { 'lang' : lang, 'text' : text } )
		lang = umcd.Selection( ( 'lang', _types.descr_lang ), default = 'de' )
		text = umcd.TextInput( ( 'text', _types.descr_text ) )
		descr = umcd.DynamicList( self[ 'baseconfig/set' ][ 'descriptions' ],
								  [ _( 'Language' ), _( 'Description' ) ], [ lang, text ],
								  default = default )
		descr[ 'colspan' ] = '2'
		form.add_row( [ descr ] )

		req = umcp.Command( args = [ 'baseconfig/set' ] )
		ids = [ varname.id(), vartype.id(), value.id(), descr.id(),	category.id() ]
		cancel = umcd.CancelButton(attributes = {'class': 'cancel'})
		if variable != None:
			form.add_row( [ cancel, umcd.SetButton( umcd.Action( req, ids ), attributes = {'class': 'submit'} ) ] )
		else:
			form.add_row( [ cancel, umcd.AddButton( umcd.Action( req, ids ), attributes = {'class': 'submit'} ) ] )

		# title
		if variable != None:
			main.append( umcd.Frame( [ form ], _( 'Modify Configuration Registry variable' ) ) )
		else:
			main.append( umcd.Frame( [ form ], _( 'Add Configuration Registry variable(s)' ) ) )

		res.dialog = main
		self.revamped( object.id(), res )

	# add uses the same function for web revamping as show
	_web_baseconfig_set = _web_baseconfig_show
