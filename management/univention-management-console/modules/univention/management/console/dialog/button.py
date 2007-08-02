#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  a button object for UMCP dialogs
#
# Copyright (C) 2006 Univention GmbH
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

import base
import image

import univention.management.console.locales as locales
import univention.debug as ud

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
	def __init__( self, command = None, options = [], selection = False ):
		self.command = command
		self.options = options
		self.selection = selection

class Button( base.Text, image.Image ):
	"""Represents a button of any kind. The argument actions contains a
	list of Action objects that defines the UMCP commands
	to execute when the button is presssed."""
	def __init__( self, label = '', tag = None, actions = [], attributes = {}, close_dialog = True ):
		base.Text.__init__( self, label, attributes )
		image.Image.__init__( self, tag )
		if not isinstance( actions, ( list, tuple ) ):
			self.actions = [ actions ]
		else:
			self.actions = actions
		self.close_dialog = close_dialog

class SearchButton( Button ):
	def __init__( self, actions = [], attributes = {} ):
		Button.__init__( self, _( 'Search' ), 'actions/ok', actions = actions,
						 attributes = attributes )

class SetButton( Button ):
	def __init__( self, actions = [], attributes = {} ):
		Button.__init__( self, _( 'Set' ), 'actions/ok', actions = actions, attributes = attributes )

class AddButton( Button ):
	def __init__( self, actions = [], attributes = {} ):
		Button.__init__( self, _( 'Add' ), 'actions/add', actions = actions, attributes = attributes )

class SelectionButton( Button ):
	def __init__( self, label = '', choices = [], actions = [], attributes = {} ):
		Button.__init__( self, label, actions = actions, attributes = attributes )
		self.choices = choices

#		 choices = [ { 'description': ... ,
# 		               'actions': ( umcd.Action ( umcp.Command( args = [], opts= {} ), ... )
#  		             },
#                    ...
#                  ]
class ChoiceButton( Button ):
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
	def __init__( self, label = '', tag = '', actions = [], attributes = {} ):
		Button.__init__( self, label = label, tag = tag, actions = actions, attributes = attributes )

class CancelButton( ISignalButton ):
	"""Can be used for cancel buttons"""
	def __init__( self, attributes = {} ):
		ISignalButton.__init__( self, label = _( 'Cancel' ), tag = 'actions/cancel',
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
	def __init__( self, fields = [], attributes = {} ):
		ISignalButton.__init__( self, label = _( 'Reset' ), tag = 'actions/cancel',
								actions = [ '::reset' ], attributes = attributes )
		self.fields = fields

ButtonTypes = ( type( Button() ), type( SelectionButton() ), type( ChoiceButton() ),
				type( CancelButton() ), type( CloseButton() ),
				type( ErrorButton() ), type( ResetButton() ), type( SearchButton() ),
				type( SetButton() ), type( AddButton() ) )
