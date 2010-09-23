#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  maps dynamic elements
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

import mapper
import utils

import univention.management.console.tools as umc_tools
import univention.management.console as umc
import univention.management.console.dialog as umcd

from uniparts import *

_ = umc.Translation( 'univention.management.console.frontend' ).translate

def rows_map( storage, umcp_part ):
	row = []
	default_type = getattr( umcp_part, 'default_type', None )
	for elem in umcp_part:
		part = []
		args = {}
		if isinstance( elem, ( list, tuple ) ):
			for item in elem:
				part.append( storage.to_uniparts( item ) )
				args.update( utils.layout_attrs( storage, item, default_type = default_type ) )
		elif isinstance( elem, umcd.Cell ):
			if isinstance( elem.item, ( list, tuple ) ):
				for item in elem.item:
					part.append( storage.to_uniparts( item ) )
					args.update( utils.layout_attrs( storage, elem, default_type = default_type ) )
			else:
				part.append( storage.to_uniparts( elem.item ) )
				args.update( utils.layout_attrs( storage, elem, default_type = default_type ) )
		else:
			part.append( storage.to_uniparts( elem ) )
			args = utils.layout_attrs( storage, elem, default_type = default_type )
		row.append( tablecol( '', args, { 'obs' : part } ) )

	row_args = { 'type' : 'umc_list_row' }
	if isinstance( umcp_part, umcd.Row ):
		row_args.update( utils.layout_attrs( storage, umcp_part, default_type = default_type ) )

	return tablerow( '', row_args, { 'obs' : row } )

mapper.add( list, rows_map )
mapper.add( tuple, rows_map )
mapper.add( umcd.Row, rows_map )

def frame_map( storage, umcp_part ):
	rows = []

	title = umcp_part.get_title()
	if title:
		elem = storage.to_uniparts( title )
		col = tablecol( '', { 'type' : 'h4' }, { 'obs' : [ elem ] } )
		rows.append( tablerow( '', {},
							   { 'obs' : [ col ] } ) )

	for row in umcp_part:
		up = storage.to_uniparts( row )
		col = tablecol( '', { 'type' : 'umc_frame_col' }, { 'obs' : [ up ] } )
		rows.append( tablerow( '', { 'type' : 'umc_frame_row' },
							   { 'obs' : [ col ] } ) )

	attrs = utils.layout_attrs( storage, umcp_part )
	attrs[ 'type' ] = 'umc_frame'
	return table( '', attrs, { 'obs' : rows } )

mapper.add( umcd.Frame, frame_map )
mapper.add( umcd.Dialog, frame_map )

def section_map( storage, umcp_part ):
	rows = []

	if umcp_part.hideable:
		items = { 'id' : umcp_part.name, 'title' : umcp_part.title, 'minus' : utils.img_minus, 'plus' : utils.img_plus }
		if umcp_part.hidden:
			items[ 'current' ] = items[ 'plus' ]
			items[ 'class' ] = 'umc_hidden'
		else:
			items[ 'current' ] = items[ 'minus' ]
			items[ 'class' ] = 'umc_visible'
			
		title = '<p class="umc_title">%(title)s&nbsp;<a href="javascript:umc_hide_show(\'%(id)s\',\'%(minus)s\',\'%(plus)s\')"><img style="border: 0px" id="%(id)s.button" src="%(current)s"/></a></p>' % items
		script = '''
<script type="text/javascript">
dojo.addOnLoad(function(){
	var items = new Array( "%(id)s" );
	umc_restore( items, "%(minus)s", "%(plus)s", "%(class)s" );
});
</script>''' % items
		on_load = htmltext( '', {}, { 'htmltext' : [ script ] } )
		
	else:
		on_load = None
		title = '<p class="umc_title">%s</p>' % umcp_part.title
	
	elem = htmltext( '', {}, { 'htmltext' : [ title ] } )
	if on_load:
		col = tablecol( '', { 'type' : 'umc_section_title' }, { 'obs' : [ elem, on_load ] } )
	else:
		col = tablecol( '', { 'type' : 'umc_section_title' }, { 'obs' : [ elem ] } )
	rows.append( tablerow( '', {}, { 'obs' : [ col ] } ) )

	body = storage.to_uniparts( umcp_part.body )
	col = tablecol( '', {}, { 'obs' : [ body ] } )
	if umcp_part.hidden:
		css_class = 'umc_hidden'
	else:
		css_class = 'umc_visible'
	rows.append( tablerow( '', { 'type' : css_class, 'webui-id' : umcp_part.name }, { 'obs' : [ col ] } ) )

	attrs = utils.layout_attrs( storage, umcp_part )
	attrs[ 'type' ] = 'umc_section'

	return table( '', attrs, { 'obs' : rows } )

mapper.add( umcd.Section, section_map )

def list_map( storage, umcp_part ):
	headers = []
	default_type = getattr( umcp_part, 'default_type', None )
	for col in umcp_part.get_header():
		if isinstance( col, umcd.ToggleCheckboxes ):
			head = htmltext( '', {}, { 'htmltext' : [ '<span class="h7">%s</span>' % str( col ) ] } )
		else:
			head = header( unicode( col ), { 'type' : '6' }, {} )
		args = utils.layout_attrs( storage, col, default_type = default_type )
		if not umcp_part.get_second_header():
			args.update( { 'type' : 'umc_list_head' } )
		else:
			args.update( { 'type' : 'umc_list_head_first' } )
		headers.append( tablecol( '', args, { 'obs' : [ head ] } ) )
	if headers:
		rows = [ tablerow( '', { 'type' : 'umc_list_head' }, { 'obs' : headers } ) ]
	else:
		rows = []

	headers = []
	if umcp_part.get_second_header():
		for col in umcp_part.get_second_header():
			head = header( unicode( col ), { 'type' : '7' }, {} )
			args = utils.layout_attrs( storage, col, default_type = default_type )
			args.update( { 'type' : 'umc_list_head_second' } )
			headers.append( tablecol( '', args, { 'obs' : [ head ] } ) )
		rows.append( tablerow( '', { 'type' : 'umc_list_head' }, { 'obs' : headers } ) )

	for row in umcp_part.get_content():
		up = storage.to_uniparts( row )
		rows.append( up )

	args = { 'type' : 'umc_list' }
	args.update( utils.layout_attrs( storage, umcp_part, default_type = default_type ) )
	return table( '', args, { 'obs' : rows } )

mapper.add( umcd.List, list_map )
mapper.add( umcd.SearchForm, list_map )
mapper.add( umcd.SimpleTreeTable, list_map )

def wizard_map( storage, umcp_part ):
	return storage.to_uniparts( umcp_part.setup() )

mapper.add( umcd.Wizard, wizard_map )

