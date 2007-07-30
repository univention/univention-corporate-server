#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  classes for different types of input fieldes within a UMCP dialog
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

import base

class Input( base.Text ):
	"""This class is the base class for all kinds of input fields. It
	provides a label for the field, a 'value' attribute to store the
	input given by the user and an eextra attribute for a default
	value. The 'option' attribute is used to identify the UMCP command
	option name that is associated with the input field. The attribute
	'static_options' provides a possibility associate other options with
	specific static values additional to the option provided by the
	input field itself."""
	def __init__( self, option = ( None, None ), default = None, static_options = {},
				  attributes = {} ):
		self.value = None
		self.syntax = None
		self.option = None
		self.option, self.syntax = option
		if self.syntax:
			base.Text.__init__( self, self.syntax.label, attributes )
		else:
			base.Text.__init__( self, '', attributes )
		self.static_options = static_options
		# store default value in a separate attribute to have the
		# possiblity for reverting changes
		self.default = default
		# store cached value; this is required for pages using dynamic
		# elements
		self.cached = None

	def label( self ):
		if self.syntax:
			return self.syntax.name
		return None

	def item( self, value ):
		return ( value, value )

class ReadOnlyInput( Input ):
	"""This input class represents a simple text field as base.Text
	does. The only difference is that this field may provide input for
	action items."""
	def __init__( self, option = ( None, None ), default = '', static_options = {}, attributes = {} ):
		Input.__init__( self, option, default, static_options, attributes )

class TextInput( Input ):
	"""This class represent a simple string input field."""
	def __init__( self, option = ( None, None ), default = '', static_options = {}, attributes = {} ):
		Input.__init__( self, option, default, static_options, attributes )

class SecretInput( Input ):
	"""This class represent a password input field."""
	def __init__( self, option = ( None, None ), default = '', static_options = {}, attributes = {} ):
		Input.__init__( self, option, default, static_options, attributes )

class MultiLineInput( Input ):
	"""This class represent a simple string input field."""
	def __init__( self, option = ( None, None ), default = '', static_options = {}, attributes = {} ):
		Input.__init__( self, option, default, static_options, attributes )

class Checkbox( Input ):
	"""This class might also be used to provide an boolean option for a
	UMCP command, but may also be used to control if the static_options
	provide with this control are passed to the UMCP command. To use an
	object of this class as a simple boolean option just provide a valid
	name for the attribute 'option'. To use it for controlling whether
	the given static_options should be passed to a command depending of
	the value of the check box set the attribute 'option' to None."""
	def __init__( self, option = ( None, None ), default = False, static_options = {},
				  attributes = {} ):
		Input.__init__( self, option, default, static_options, attributes )

class Selection( Input ):
	"""This class represents a selection list. 'choices' contains a list
	of pairs. The first element of a pair is an identifer (unique within
	the list) and the second one is the Text shown in the frontend. The
	'default' attribute should contain the identifer of the pre-selected
	item."""
	def __init__( self, option = ( None, None ), default = '', static_options = {}, attributes = {} ):
		Input.__init__( self, option, default, static_options, attributes )

	def choices( self ):
		if self.syntax:
			return self.syntax.choices()
		return ()

	def item( self, value ):
		values = self.choices()
		for key, descr in values:
			if key == value:
				return ( key, descr )
		return ( value, value )

InputTypes = ( type( ReadOnlyInput() ), type( TextInput() ), type( SecretInput() ),
			   type( Checkbox() ), type( Selection() ), type( MultiLineInput() ) )
