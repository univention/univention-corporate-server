#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  mapping of UMCP dialog elements to uniparts
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

import univention.management.console.dialog as umcd
import univention.management.console.tools as umc_tools

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
	def __init__( self, module ):
		dict.__init__( self )
		self.__module = module

	def get_command( self, command ):
		for name, cmd in self.__module[ 'commands' ].items():
			if name == command:
				return cmd

	def get_module_name( self ):
		return self.__module.get( 'short_description', '' )

	def confirmation_required( self, command ):
		cmd = self.get_command( command.arguments[ 0 ] )
		if cmd and cmd[ 'confirm' ]:
			return cmd[ 'confirm' ]

		return None

	def to_uniparts( self, umcp_parts ):
		if type( umcp_parts ) in umcd.DynamicElementTypes:
			return self.__convert_dynamics( umcp_parts )
		elif type( umcp_parts ) in umcd.StructuralTypes + ( list, tuple ):
			return self.__convert_structural( umcp_parts )
		elif type( umcp_parts ) in umcd.ElementTypes:
			return self.__convert_elements( umcp_parts )

		return None
	def create_tag_attributes( self, elem, default_type = None ):
		if not default_type:
			args = { 'type' : 'umc_list_element' }
		else:
			args = { 'type' : default_type }
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
