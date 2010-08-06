#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  a button object for UMCP dialogs
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

import base
import image

import univention.management.console.locales as locales
import univention.management.console.tools as umct

_ = locales.Translation( 'univention.management.console.dialog' ).translate

class Action( object ):
	"""This class defines an action it is performed when a button is
	pressed. A button may have more than one of these action objects.

	The input fields stored in 'options' (identified by their unique ID)
	should be passed to the UMCP request 'command'. Therefore the
	'option' attribute of the input field defines the option's name and
	the value is taken from the input field.

	Additionally there is the possibility to get the UMCP request
	command from a selection input field instead of defining it in the
	UMCP request object statically. Therefore the attribute
	'command_selection' must be set to the ID of the selection input
	field. The key of the selected value is used for the request command
	name."""
	SUCCESS, FAILURE = range( 2 )
	def __init__( self, command = None, options = [], selection = False, status_range = None ):
		self.command = command
		self.options = options
		self.selection = selection
		if status_range == Action.SUCCESS:
			self.status_range = ( 200, 299 )
		elif status_range == Action.FAILURE:
			self.status_range = ( 300, 399 )
		else:
			self.status_range = status_range

class Button( base.Text, image.Image ):
	"""Represents a button of any kind. The argument actions contains a
	list of Action objects that defines the UMCP commands
	to execute when the button is presssed."""
	def __init__( self, label = '', tag = None, actions = [], attributes = {}, close_dialog = True, helptext = None, icon_right = False, default = False ):
		base.Text.__init__( self, label, attributes )
		image.Image.__init__( self, tag, attributes = attributes )
		if not 'class' in self and not default:
			self[ 'class' ] = 'cancel'
		elif default:
			self[ 'class' ] = 'submit'
			self[ 'defaultbutton' ] = '1'
		if not isinstance( actions, ( list, tuple ) ):
			self.actions = [ actions ]
		else:
			self.actions = actions
		self.close_dialog = close_dialog
		self.icon_right = icon_right
		if helptext:
			self.helptext = helptext

class SearchButton( Button ):
	def __init__( self, actions = [], attributes = {}, close_dialog = True, label = _( 'Search' ) ):
		Button.__init__( self, label, 'actions/ok', actions = actions,
						 attributes = attributes, close_dialog = close_dialog )

class SetButton( Button ):
	def __init__( self, actions = [], attributes = {}, close_dialog = True ):
		Button.__init__( self, _( 'Set' ), 'actions/ok', actions = actions, attributes = attributes, close_dialog = close_dialog )

class PrevButton( Button ):
	def __init__( self, actions = [], attributes = {}, close_dialog = True ):
		Button.__init__( self, _( 'Previous' ), 'actions/prev', actions = actions, attributes = attributes, close_dialog = close_dialog )

class NextButton( Button ):
	def __init__( self, actions = [], attributes = {}, close_dialog = True ):
		Button.__init__( self, _( 'Next' ), 'actions/next', actions = actions, attributes = attributes, close_dialog = close_dialog, icon_right = True )

class AddButton( Button ):
	def __init__( self, actions = [], attributes = {}, close_dialog = True, label = _('Add') ):
		Button.__init__( self, label, 'actions/add', actions = actions, attributes = attributes, close_dialog = close_dialog )

class SelectionButton( Button ):
	def __init__( self, label = '', choices = [], actions = [], attributes = {}, close_dialog = True ):
		Button.__init__( self, label, actions = actions, attributes = attributes, close_dialog = close_dialog )
		self.choices = choices

class SimpleSelectButton( Button ):
	def __init__( self, label = '', option = None, choices = [], actions = [], attributes = {}, default = None, close_dialog = True ):
		Button.__init__( self, label, actions = actions, attributes = attributes, close_dialog = close_dialog )
		self.choices = choices
		self.default = default
		self.option = option

class LinkButton( Button ):
	def __init__( self, label = '', tag = None, actions = [], attributes = {}, close_dialog = True, helptext = None, current = False ):
		if 'class' in attributes:
			attributes[ 'class' ] += ' linkbutton'
		else:
			attributes[ 'class' ] = 'linkbutton'
		if current:
			attributes[ 'class' ] += ' umc_tree_item_current'
		self.current = current

		Button.__init__( self, label, tag, actions = actions, attributes = attributes, close_dialog = close_dialog, helptext = helptext )
		self.set_size( umct.SIZE_TINY )

# choices = [ { 'description': ... ,
# 	        'actions': ( umcd.Action ( umcp.Command( args = [], opts= {} ), ... )
#  	      },
#             ...
#           ]
class ChoiceButton( Button ):
	"""
	choices = [ { 'description': ... ,
			   'actions': [ umcd.Action ( umcp.Command( args = [], opts= {} ) ), ... ]
			 },
			 { 'description': 'this description will be ignored' ,
			   'actions': '::invert',
			   'idlist': [ LIST OF UMC WIDGET IDs ],
			 },
				...
			  ]
	Valid string actions are: "::none", "::invert", "::select_all"
	otherwise actions should be a list of umcd.Actions
	"""
	def __init__( self, label = '', choices = [], attributes = {}, default = None, close_dialog = True ):
		Button.__init__( self, label, actions = [], attributes = attributes, close_dialog = close_dialog )
		self.choices = choices
		self.name2index = {}
		self.default = None
		for i in range(len(self.choices)):
			# add internal ids
			if type(self.choices[ i ]['actions']) == str and self.choices[ i ]['actions'] in [ '::none', '::invert', '::select_all' ]:
				self.choices[ i ]['name'] = self.choices[ i ]['actions']
				if self.choices[ i ]['name'] == '::none':
					self.choices[ i ]['description'] = '---'
				elif self.choices[ i ]['name'] == '::invert':
					self.choices[ i ]['description'] = _( 'Invert selection' )
				elif self.choices[ i ]['name'] == '::select_all':
					self.choices[ i ]['description'] = _( 'Select all' )
			elif len(self.choices[ i ]['actions']) == 0:
				self.choices[ i ]['name'] = '::none'
			else:
				self.choices[ i ]['name'] = 'choice-%d' % i
			# add mapping "internal name" to "list index"
			self.name2index[ self.choices[ i ]['name'] ] = i
			# convert default
			if i == default:
				self.default = self.choices[ i ]['name']

class FilteringSelectButton( Button ):
	"""This class provides a filtering select field."""
	def __init__( self, label = '', choices = [], actions = [], attributes = {}, default = None, close_dialog = True ):
		Button.__init__( self, label, actions = actions, attributes = attributes, close_dialog = close_dialog )
		self.choices = choices
		self.name2index = {}
		self.default = None
		for i in range(len(self.choices)):
			# add internal ids
			if len(self.choices[ i ]['actions']) == 0:
				self.choices[ i ]['name'] = '::none'
			else:
				self.choices[ i ]['name'] = 'choice-%d' % i
			# add mapping "internal name" to "list index"
			self.name2index[ self.choices[ i ]['name'] ] = i
			# convert default
			if i == default:
				self.default = self.choices[ i ]['name']

class ComboboxButton( Button ):
	"""This class provides a combobox field."""
	def __init__( self, label = '', choices = [], actions = [], attributes = {}, default = None, close_dialog = True ):
		Button.__init__( self, label, actions = actions, attributes = attributes, close_dialog = close_dialog )
		self.choices = choices
		self.name2index = {}
		self.default = None
		for i in range(len(self.choices)):
			# add internal ids
			if len(self.choices[ i ]['actions']) == 0:
				self.choices[ i ]['name'] = '::none'
			else:
				self.choices[ i ]['name'] = 'choice-%d' % i
			# add mapping "internal name" to "list index"
			self.name2index[ self.choices[ i ]['name'] ] = i
			# convert default
			if i == default:
				self.default = self.choices[ i ]['name']

class ISignalButton( Button ):
	"""This a special button that does not perform any UMCP action, but
	provides a possibility to create buttons that can be used to emit
	signals with in the frontend."""
	def __init__( self, label = '', tag = '', actions = [], attributes = {}, close_dialog = True ):
		Button.__init__( self, label = label, tag = tag, actions = actions, attributes = attributes, close_dialog = close_dialog )

class CancelButton( ISignalButton ):
	"""Can be used for cancel buttons"""
	def __init__( self, label = _( 'Cancel' ), attributes = {} ):
		ISignalButton.__init__( self, label , tag = 'actions/cancel',
								actions = [ '::cancel' ], attributes = attributes )

class CloseButton( ISignalButton ):
	"""Can be used for cancel buttons"""
	def __init__( self, attributes = {} ):
		ISignalButton.__init__( self, label = _( 'Close' ), tag = 'actions/ok',
								actions = [ '::cancel' ], attributes = attributes )

class ErrorButton( ISignalButton ):
	"""Can be used for error ok buttons"""
	def __init__( self, attributes = {} ):
		ISignalButton.__init__( self, label = _( 'Ok' ), tag = 'actions/ok',
								actions = [ '::error' ], attributes = attributes )

class ResetButton( ISignalButton ):
	"""Can be used for error ok buttons"""
	def __init__( self, fields = [], attributes = {}, close_dialog = True ):
		ISignalButton.__init__( self, label = _( 'Reset' ), tag = 'actions/cancel',
								actions = [ '::reset' ], attributes = attributes, close_dialog = close_dialog )
		self.fields = fields

class ReturnButton( ISignalButton ):
	"""return to the original command displayed on the current tab (used in
combination with confirmation dialogs)"""
	def __init__( self, label = _( 'Reset' ), fields = [], attributes = {} ):
		ISignalButton.__init__( self, label = label, tag = 'actions/cancel',
					actions = [ '::return' ], attributes = attributes )
		self.fields = fields

ButtonTypes = ( type( Button() ), type( SelectionButton() ), type( SimpleSelectButton() ), type( ChoiceButton() ),
				type( CancelButton() ), type( CloseButton() ), type( LinkButton() ), 
				type( ErrorButton() ), type( ResetButton() ), type( ReturnButton() ), type( SearchButton() ),
				type( SetButton() ), type( AddButton() ), type( NextButton() ), type( PrevButton() ),
				type( FilteringSelectButton() ), type( ComboboxButton() ) )
