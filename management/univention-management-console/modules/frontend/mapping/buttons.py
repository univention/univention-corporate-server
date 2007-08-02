#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  maps dynamic elements
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

import univention.management.console.tools as umc_tools
import univention.management.console.dialog as umcd
import univention.management.console as umc

from uniparts import *

import mapper
import utils
import copy

_ = umc.Translation( 'univention.management.console.frontend' ).translate

class IButtonMap( object ):
	'''base class for button map classes'''
	def __init__( self ):
		self.storage = None
		self.inputs = None
		self.dynamics = None

	def _parse_dynamics( self, req, opt ):
		for params, dyn in self.dynamics:
			if dyn.id() == opt:
				req.options[ dyn.option ] = mapper.parse( type( dyn ), self.storage, dyn, params )

	def _parse_inputs( self, req, opt ):
		for ( uni, umcp ) in self.inputs:
			if umcp and umcp.id() == opt:
				new_value = uni.get_input()
				# check if the value has changed. if no 'option' is
				# defined this is a special input field and this
				# check must be skipped
				if umcp.option and new_value == umcp.default:
					req.options[ umcp.option ] = new_value
					continue
				# check if the value should be appended or
				# replaced. If option is not set, skip it
				if umcp.option:
					if isinstance( umcp, umcd.ReadOnlyInput ):
						value = umcp.default
					else:
						value = new_value
						if not utils.check_syntax( umcp, value ):
							raise umc.SyntaxError( umcp )
					if req.options.has_key( umcp.option ) and \
						   isinstance( req.options[ umcp.option ], list ):
						req.options[ umcp.option ].append( utils.convert( umcp, value ) )
					else:
						req.options[ umcp.option ] = utils.convert( umcp, value )
				# check for static options and apply them. If option
				# is not set check whether the input field is to
				# 'True', otherwise skip the static options too
				if not umcp.option and not new_value:
					continue

				for k, v in umcp.static_options.items():
					if req.options.has_key( k ) and isinstance( req.options[ k ], list ):
						req.options[ k ].append( v )
					else:
						req.options[ k ] = v

	def _create_request( self, parameters, action ):
		req = copy.deepcopy( action.command )

		for opt in action.options:
			self._parse_dynamics( req, opt )
			self._parse_inputs( req, opt )

		return req

	def apply( self, storage, umcp_part, parameters, *args ):
		self.storage = storage
		self.inputs, self.dynamics = args

		requests = []
		for action in umcp_part.actions:
			req = self._create_request( parameters, action )
			if req:
				requests.append( req )
			else:
				break

		return requests

class ButtonMap( IButtonMap, mapper.IMapper ):
	def __init__( self ):
		IButtonMap.__init__( self )
		mapper.IMapper.__init__( self )

	def layout( self, storage, umcp_part ):
		attributes = utils.attributes( umcp_part )
		if umcp_part.get_tag():
			icon = umcp_part.get_image()
			attributes.update( { 'icon' : icon } )
		but = button( unicode( umcp_part ), attributes, { 'helptext' : unicode( umcp_part ) } )
		storage[ umcp_part.id() ] = ( but, umcp_part )

		return but

	def apply( self, storage, umcp_part, parameters, *args ):
		if not parameters.pressed():
			return []

		return IButtonMap.apply( self, storage, umcp_part, parameters, *args )

mapper.add( umcd.Button, ButtonMap() )
mapper.add( umcd.SetButton, ButtonMap() )
mapper.add( umcd.AddButton, ButtonMap() )
mapper.add( umcd.SearchButton, ButtonMap() )

class SelectionButtonMap( IButtonMap, mapper.IMapper ):
	def __init__( self ):
		IButtonMap.__init__( self )
		mapper.IMapper.__init__( self )

	def layout( self, storage, umcp_part ):
		commit_button = button( _( 'Do' ), {},
								{ 'helptext' : _( 'Do action with selected objects.' ) } )
		choices = [ { 'name' : '::none', 'description' : '---' },
					{ 'name' : '::invert', 'description' : _( 'Invert Selection' ) },
					{ 'name' : '::select_all', 'description' : _( 'Select All' ) } ]
		for key, descr in umcp_part.choices:
			choices.append( { 'name' : key, 'description' : descr } )
		selection = question_select( _( 'Do with selected objects ...' ),
									 { 'width' : '200' },
									 { 'helptext' : _( 'Do with selected objects ...' ),
									   'choicelist' : choices, 'button' : commit_button } )
		storage[ umcp_part.id() ] = ( ( selection, commit_button ), umcp_part )

		return selection

	def _create_request( self, parameters, action ):
		select, btn = parameters
		req = copy.deepcopy( action.command )

		# if the command name is not pre-defined, but stored in a selection
		if action.selection:
			value = select.getselected()
			req.arguments.insert( 0, value )

		for opt in action.options:
			self._parse_dynamics( req, opt )
			self._parse_inputs( req, opt )

		return req

	def apply( self, storage, umcp_part, parameters, *args ):
		select, btn = parameters
		inputs, dynamics = args

		selected = select.getselected()
		if not btn.pressed() or selected == '::none':
			return [ '::none' ]

		# invert selection
		if selected == '::invert':
			action = umcp_part.actions[ 0 ]
			for ( uni, umcp ) in inputs:
				if not umcp or umcp.option:
					continue
				if umcp.id() in action.options:
					if uni.get_input() == 'checked':
						umcp.cached = False
					else:
						umcp.cached = True
			return [ '::dynamic' ]

		# select all
		if selected == '::select_all':
			action = umcp_part.actions[ 0 ]
			for ( uni, umcp ) in inputs:
				if not umcp or umcp.option:
					continue
				if umcp.id() in action.options:
					umcp.cached = True
			return [ '::dynamic' ]

		return IButtonMap.apply( self, storage, umcp_part, parameters, *args )

mapper.add( umcd.SelectionButton, SelectionButtonMap() )

class ChoiceButtonMap( IButtonMap, mapper.IMapper ):
	def __init__( self ):
		IButtonMap.__init__( self )
		mapper.IMapper.__init__( self )

	def layout( self, storage, umcp_part ):
		commit_button = button( _( 'Select' ), {},
								{ 'helptext' : _( 'Select entry' ) } )

# umcp_part.choices = [ { 'description': ... ,
#  		                  'actions': ( umcd.Action ( umcp.Command( args = [], opts= {} ), ... )
#  		                },
#                       ...
#                     ]
		default = utils.default( umcp_part )

		choices = []
		defaultset = False
		for data in umcp_part.choices:
			if default and data['name'] == default and not defaultset:
				defaultset = True
				choices.append( { 'name' : data['name'], 'description' : data['description'], 'selected' : '1' } )
			else:
				choices.append( { 'name': data['name'], 'description': data['description'] } )

		selection = question_select( umcp_part.get_text(),
									 { 'width' : '200' },
									 { 'helptext' : umcp_part.get_text(),
										 'choicelist' : choices, 'button' : commit_button } )
		storage[ umcp_part.id() ] = ( ( selection, commit_button ), umcp_part )

		return selection

	def _create_request( self, parameters, action ):
		select, btn = parameters
		req = copy.deepcopy( action.command )

		for opt in action.options:
			self._parse_dynamics( req, opt )
			self._parse_inputs( req, opt )

		return req

	def apply( self, storage, umcp_part, parameters, *args ):
		select, btn = parameters
		self.inputs, self.dynamics = args

		selected = select.getselected()
		if not btn.pressed() or selected == '::none':
			return [ '::none' ]

		umcp_part.cached = selected

		idx = umcp_part.name2index[selected]
		requests = []
		for action in umcp_part.choices[ idx ]['actions']:
			req = self._create_request( parameters, action )
			if req:
				requests.append( req )
			else:
				break

		return requests


mapper.add( umcd.ChoiceButton, ChoiceButtonMap() )

class SignalButtonMap( ButtonMap, mapper.IMapper ):
	def __init__( self ):
		ButtonMap.__init__( self )
		mapper.IMapper.__init__( self )

	def apply( self, storage, umcp_part, parameters, *args ):
		if parameters.pressed():
			return umcp_part.actions
		else:
			return []

mapper.add( umcd.CancelButton, SignalButtonMap() )
mapper.add( umcd.CloseButton, SignalButtonMap() )
mapper.add( umcd.ErrorButton, SignalButtonMap() )

class ResetButtonMap( ButtonMap, mapper.IMapper ):
	def __init__( self ):
		ButtonMap.__init__( self )
		mapper.IMapper.__init__( self )

	def apply( self, storage, umcp_part, parameters, *args ):
		if parameters.pressed():
			if isinstance( umcp_part.fields, dict ):
				for id, default in umcp_part.fields.items():
					uni_part, umcp_item = storage.find_by_umcp_id( id )
					umcp_item.cached = default
			elif isinstance( umcp_part.fields, ( list, tuple ) ):
				for id in umcp_part.fields:
					uni_part, umcp_item = storage.find_by_umcp_id( id )
					umcp_item.cached = umcp_item.default
			return umcp_part.actions
		else:
			return []

mapper.add( umcd.ResetButton, ResetButtonMap() )
