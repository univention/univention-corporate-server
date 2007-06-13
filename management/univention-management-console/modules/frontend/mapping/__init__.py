#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  mapping of UMCP dialog elements to uniparts
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

import univention.management.console.dialog as umcd
import univention.management.console.tools as umc_tools

import univention.debug as ud

from uniparts import *
from syntax import *

# element types
import structural
import simple
import buttons
import dynamics
import helper

from mapper import *

# Convert UMCP dialog elements to frontend uniparts
class Storage( dict ):
	def __init__( self ):
		dict.__init__( self )

	def to_uniparts( self, umcp_parts ):
		if type( umcp_parts ) in umcd.DynamicElementTypes:
			return self.__convert_dynamics( umcp_parts )
		elif type( umcp_parts ) in umcd.StructuralTypes + ( list, tuple ):
			return self.__convert_structural( umcp_parts )
		elif type( umcp_parts ) in umcd.ElementTypes:
			return self.__convert_elements( umcp_parts )

		return None
	def create_tag_attributes( self, elem ):
		args = { 'type' : 'umc_list_element' }
		if isinstance( elem, umcd.Date ):
			args[ 'type' ] = 'umc_list_element_date'
		elif isinstance( elem, umcd.Number ):
			args[ 'type' ] = 'umc_list_element_number'

		return args

	def __convert_dynamics( self, umcp_part ):
		ret = layout( type( umcp_part ), self, umcp_part )
		return ret

	def __convert_structural( self, umcp_part ):
		ret = layout( type( umcp_part ), self, umcp_part )
		return ret

	def __convert_elements( self, umcp_part ):
		ret = layout( type( umcp_part ), self, umcp_part )
		return ret

	def sort_by_type( self ):
		buttons = []
		inputs = []
		dynamics = []
		for id, ( uni, umcp ) in self.items():
			if type( umcp ) in umcd.InputTypes:
				inputs.append( ( uni, umcp ) )
			elif type( umcp ) in umcd.ButtonTypes:
 				buttons.append( ( uni, umcp ) )
			elif type( umcp ) in umcd.DynamicElementTypes:
				dynamics.append( ( uni, umcp ) )

		return ( buttons, inputs, dynamics )

	def find_umcp( self, item ):
		for id, ( unipart, umcppart ) in self.items():
			if item == unipart:
				return umcppart

		return None

	def find_by_umcp_id( self, id ):
		if self.has_key( id ):
			return self.__getitem__( id )
		return None
