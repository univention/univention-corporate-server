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

import univention.management.console.tools as umc_tools
import univention.management.console.dialog as umcd
import univention.management.console as umc

from uniparts import *

import mapper
import utils
import copy

import univention.debug as ud

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
					if isinstance( umcp, umcd.ReadOnlyInput ) or umcp.syntax.may_change == False:
						value = umcp.default
					else:
						value = new_value
						if req.verify_options and not utils.check_syntax( umcp, value ):
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

		if action.status_range:
			req.options[ '_range' ] = action.status_range

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

	def confirm_attributes( self, storage, umcp_part, attributes ):
		for action in umcp_part.actions:
			if isinstance( action, basestring ): continue
			confirm = storage.confirmation_required( action.command )
			if confirm:
				attributes.update( { 'webui-confirm-title' : '%s - %s' % ( storage.get_module_name(), str( confirm.title ) ), 'webui-confirm-question' : str( confirm.question ), 'webui-confirm-yes' : str( confirm.yes ), 'webui-confirm-no' : str( confirm.no ) } )

	def layout( self, storage, umcp_part, attributes = {} ):
		attributes = copy.copy( attributes )
		attributes.update( utils.attributes( umcp_part ) )
		if umcp_part.get_tag():
			icon = umcp_part.get_image()
			attributes.update( { 'icon' : icon } )

			if umcp_part.icon_right:
				attributes.update( { 'icon_side' : 'right' } )
			else:
				attributes.update( { 'icon_side' : 'left' } )

		self.confirm_attributes( storage, umcp_part, attributes )

		but = button( unicode( umcp_part ), attributes, { 'helptext' : unicode( umcp_part ) } )
		storage[ umcp_part.id() ] = ( but, umcp_part )

		return but

	def apply( self, storage, umcp_part, parameters, *args ):
		if not parameters.pressed():
			return []

		return IButtonMap.apply( self, storage, umcp_part, parameters, *args )

mapper.add( umcd.Button, ButtonMap() )
mapper.add( umcd.SetButton, ButtonMap() )
mapper.add( umcd.PrevButton, ButtonMap() )
mapper.add( umcd.NextButton, ButtonMap() )
mapper.add( umcd.AddButton, ButtonMap() )
mapper.add( umcd.SearchButton, ButtonMap() )

class LinkButtonMap( ButtonMap ):
	def __init__( self ):
		ButtonMap.__init__( self )

	def layout( self, storage, umcp_part ):
		return ButtonMap.layout( self, storage, umcp_part, { 'link' : 'yes', 'type' : 'umc_link_button' } )

mapper.add( umcd.LinkButton, LinkButtonMap() )

class SelectionButtonMap( IButtonMap, mapper.IMapper ):
	def __init__( self ):
		IButtonMap.__init__( self )
		mapper.IMapper.__init__( self )

	def layout( self, storage, umcp_part ):
		commit_button = button( _( 'Execute' ), {},
								{ 'helptext' : _( 'Perform action on selected objects.' ) } )
		choices = [ { 'name' : '::none', 'description' : '---' },
					{ 'name' : '::invert', 'description' : _( 'Invert selection' ) },
					{ 'name' : '::select_all', 'description' : _( 'Select all' ) } ]
		for key, descr in umcp_part.choices:
			choices.append( { 'name' : key, 'description' : descr } )

		attributes = utils.attributes( umcp_part )
		if not 'width' in attributes:
			attributes.update( { 'width' : '200' } )
		selection = question_select( _( 'Selected objects ...' ),
									 attributes,
									 { 'helptext' : _( 'Selected objects ...' ),
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

class SimpleSelectButtonMap( IButtonMap, mapper.IMapper ):
	def __init__( self ):
		IButtonMap.__init__( self )
		mapper.IMapper.__init__( self )

	def layout( self, storage, umcp_part ):
		commit_button = button( _( 'Execute' ), {},	{ 'helptext' : '' } )
		choices = []
		default = utils.default( umcp_part )
		for key, descr in umcp_part.choices:
			if key == default:
				choices.append( { 'name' : key, 'description' : descr, 'selected' : '1' } )
			else:
				choices.append( { 'name' : key, 'description' : descr } )

		attributes = utils.attributes( umcp_part )
		if not 'width' in attributes:
			attributes.update( { 'width' : '300' } )
		selection = question_select( umcp_part.get_text(), attributes, { 'choicelist' : choices, 'button' : commit_button, 'helptext' : umcp_part.get_text() } )
		storage[ umcp_part.id() ] = ( ( selection, commit_button ), umcp_part )

		return selection

	def _create_request( self, action, value, option ):
		req = copy.deepcopy( action.command )

		if action.status_range:
			req.options[ '_range' ] = action.status_range

		if option:
			req.options[ option ] = value

		return req

	def apply( self, storage, umcp_part, parameters, *args ):
		self.storage = storage
		select, btn = parameters

		if not btn.pressed():
			return []

		value = select.getselected()
		requests = []
		for action in umcp_part.actions:
			req = self._create_request( action, value, umcp_part.option )
			if req:
				requests.append( req )
			else:
				break

		return requests

mapper.add( umcd.SimpleSelectButton, SimpleSelectButtonMap() )

class ChoiceButtonMap( IButtonMap, mapper.IMapper ):
	def __init__( self ):
		IButtonMap.__init__( self )
		mapper.IMapper.__init__( self )

	def layout( self, storage, umcp_part ):
		commit_button = button( _( 'Select' ), {},
								{ 'helptext' : _( 'Select entry' ) } )

# have a look at univention/management/console/dialog/button.py for structure of umcp_part.choices
		default = utils.default( umcp_part )

		choices = []
		defaultset = False
		for data in umcp_part.choices:
			if default and not default.startswith( '::' ) and data['name'] == default and not defaultset:
				defaultset = True
				choices.append( { 'name' : data['name'], 'description' : data['description'], 'selected' : '1' } )
			else:
				choices.append( { 'name': data['name'], 'description': data['description'] } )

		attributes = utils.attributes( umcp_part )
		if not 'width' in attributes:
			attributes.update( { 'width' : '120' } )
		selection = question_select( umcp_part.get_text(),
									 attributes,
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
		# invert selection
		if selected == '::invert':
			idlist = umcp_part.choices[ idx ].get('idlist', [])
			for ( uni, umcp ) in self.inputs:
				if not umcp or umcp.option:
					continue
				if umcp.id() in idlist:
					if uni.get_input() == 'checked':
						umcp.cached = False
					else:
						umcp.cached = True
			return [ '::dynamic' ]

		# select all
		if selected == '::select_all':
			idlist = umcp_part.choices[ idx ].get('idlist', [])
			for ( uni, umcp ) in self.inputs:
				if not umcp or umcp.option:
					continue
				if umcp.id() in idlist:
					umcp.cached = True
			return [ '::dynamic' ]

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

class FilteringSelectButtonMap( IButtonMap, mapper.IMapper ):
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

		attributes = utils.attributes( umcp_part )
		if not 'width' in attributes:
			attributes.update( { 'width' : '120' } )
		selection = question_dojo_select( umcp_part.get_text(),
									 attributes,
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

		requests = []
		for action in umcp_part.choices[ idx ]['actions']:
			req = self._create_request( parameters, action )
			if req:
				requests.append( req )
			else:
				break

		return requests

mapper.add( umcd.FilteringSelectButton, FilteringSelectButtonMap() )

class ComboboxButtonMap( IButtonMap, mapper.IMapper ):
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

		attributes = utils.attributes( umcp_part )
		if not 'width' in attributes:
			attributes.update( { 'width' : '120' } )
		selection = question_dojo_comboselect( umcp_part.get_text(),
									 attributes,
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

mapper.add( umcd.ComboboxButton, ComboboxButtonMap() )

class SignalButtonMap( ButtonMap, mapper.IMapper ):
	def __init__( self ):
		ButtonMap.__init__( self )
		mapper.IMapper.__init__( self )

	def layout( self, storage, umcp_part, attributes = {} ):
		attributes[ 'class' ] = 'cancel'
		ret = ButtonMap.layout( self, storage, umcp_part, attributes )
		return ret

	def apply( self, storage, umcp_part, parameters, *args ):
		if parameters.pressed():
			return umcp_part.actions
		else:
			return []

mapper.add( umcd.CancelButton, SignalButtonMap() )
mapper.add( umcd.CloseButton, SignalButtonMap() )
mapper.add( umcd.ErrorButton, SignalButtonMap() )
mapper.add( umcd.ReturnButton, SignalButtonMap() )

class ResetButtonMap( ButtonMap, mapper.IMapper ):
	def __init__( self ):
		ButtonMap.__init__( self )
		mapper.IMapper.__init__( self )

	def layout( self, storage, umcp_part, attributes = {} ):
		attributes[ 'class' ] = 'cancel'
		ret = ButtonMap.layout( self, storage, umcp_part, attributes )
		return ret

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

def __rewrite_tree( storage, data, level = 0, parent = None, collapsible = None, name = 'default', items = [] ):
	rows = []
	prev = None
	for item in data:
		if not type( item ) in ( list, tuple ):
			args = utils.layout_attrs( storage, item )
			unipart = storage.to_uniparts( item )
			args[ 'type' ] = 'umc_tree_view_item_level%d' % level
			col_unipart = tablecol( '', {}, { 'obs' : [ unipart, ] } )
			if level <= collapsible:
				if parent:
					item_id = name + '.' + parent + '.' + item.get_text()
				else:
					item_id = name + '.' + item.get_text()
				if not item.current:
					items.append( '"%s"' % item_id )
				link_button = '<a href="javascript:umc_hide_show(\'%(id)s\', \'%(minus)s\', \'%(plus)s\')"><img style="border: 0px" id="%(id)s.button" src="%(current)s"/></a>' % { 'id' : item_id, 'minus' : utils.img_minus, 'plus' : utils.img_plus, 'current' : utils.img_minus }
				col_toggle = tablecol( '', {}, { 'obs' : [ htmltext( '', {}, { 'htmltext' : [ link_button, ] } ), ] } )
				row = tablerow( '', {}, { 'obs' : [ col_toggle, col_unipart ] } )
			else:
				row = tablerow( '', {}, { 'obs' : [ col_unipart ] } )

			col = tablecol( '', args, { 'obs' : [ table( '', {}, { 'obs' : [ row, ] } ), ] } )
			if parent:
				row = tablerow( '', {}, { 'obs' : [ col, ] } )
			else:
				row = tablerow( '', {}, { 'obs' : [ col, ] } )
			rows.append( row )
		else:
			if prev:
				if parent:
					new_parent = parent + '.' + prev.get_text()
				else:
					new_parent = prev.get_text()
			else:
				new_parent = None
			rows.extend( __rewrite_tree( storage, item, level + 1, parent = new_parent, collapsible = collapsible, name = name, items = items ) )
		prev = item
	if not rows:
		return []
	else:
		if parent:
			return [ tablerow( '', {}, { 'obs' : [ tablecol( '', {}, { 'obs' :  [ table( '', { 'webui-id' : name + '.' + parent }, { 'obs' : rows } ), ] } ), ] } ), ]
		else:
			return [ tablerow( '', {}, { 'obs' : [ tablecol( '', {}, { 'obs' :  [ table( '', { 'webui-id' : name + '.' }, { 'obs' : rows } ), ] } ), ] } ), ]

def simple_treeview_map( storage, umcp_part ):
	items = []
	tablerows = __rewrite_tree( storage, umcp_part._tree_data, collapsible = umcp_part.collapsible, name = umcp_part.name, items = items )
	args = { 'type' : 'umc_tree_view', 'webui-id' : umcp_part.name }
	args.update( utils.layout_attrs( storage, umcp_part ) )
	on_load = htmltext( '', {}, { 'htmltext' : [ '''
<script type="text/javascript">
dojo.addOnLoad(function(){
	var items = new Array( %s );
	umc_restore( items, "%s", "%s" );
});
</script>''' % ( ', '.join( items ), utils.img_minus, utils.img_plus ) ] } )
	tablerows.append( on_load )
	return table( '', args, { 'obs' : tablerows } )

mapper.add( umcd.SimpleTreeView, simple_treeview_map )
