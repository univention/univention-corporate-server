#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  maps dynamic elements
#
# Copyright (C) 2007-2009 Univention GmbH
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

import mapper
import utils

import univention.management.console.tools as umc_tools
import univention.management.console as umc
import univention.management.console.dialog as umcd

from uniparts import *

_ = umc.Translation( 'univention.management.console.frontend' ).translate

def rows_map( storage, umcp_part ):
	row = []
	for elem in umcp_part:
		part = []
		args = {}
		if isinstance( elem, ( list, tuple ) ):
			for item in elem:
				part.append( storage.to_uniparts( item ) )
				args.update( utils.layout_attrs( storage, item ) )
		else:
			part.append( storage.to_uniparts( elem ) )
			args = utils.layout_attrs( storage, elem )
		row.append( tablecol( '', args, { 'obs' : part } ) )

	row_args = { 'type' : 'umc_list_row' }
	if isinstance( umcp_part, umcd.Row ):
		row_args.update( utils.layout_attrs( storage, umcp_part ) )

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

	return table( '', { 'type' : 'umc_frame' }, { 'obs' : rows } )

mapper.add( umcd.Frame, frame_map )
mapper.add( umcd.Dialog, frame_map )

def list_map( storage, umcp_part ):
	headers = []
	for col in umcp_part.get_header():
		head = header( unicode( col ), { 'type' : '4' }, {} )
		args = utils.layout_attrs( storage, col )
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
			head = header( unicode( col ), { 'type' : '5' }, {} )
			args = utils.layout_attrs( storage, col )
			args.update( { 'type' : 'umc_list_head_second' } )
			headers.append( tablecol( '', args, { 'obs' : [ head ] } ) )
		rows.append( tablerow( '', { 'type' : 'umc_list_head' }, { 'obs' : headers } ) )

	for row in umcp_part.get_content():
		up = storage.to_uniparts( row )
		rows.append( up )

	args = { 'type' : 'umc_list' }
	args.update( utils.layout_attrs( storage, umcp_part ) )
	return table( '', args, { 'obs' : rows } )

mapper.add( umcd.List, list_map )
mapper.add( umcd.SearchForm, list_map )

def wizard_map( storage, umcp_part ):
	return storage.to_uniparts( umcp_part.setup() )

mapper.add( umcd.Wizard, wizard_map )
