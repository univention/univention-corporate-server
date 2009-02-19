#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  maps UMC syntax objects to dialog widgets
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

from copy import deepcopy

import univention.management.console.values as values

import dynamic
import input

__all__ = [ 'register', 'make', 'make_readonly', 'copy' ]

_widget_generator = {}

def register( syntax, function ):
	global _widget_generator
	if not _widget_generator.has_key( syntax ):
		_widget_generator[ syntax ] = function

def copy( base, new ):
	global _widget_generator
	if _widget_generator.has_key( base ):
		_widget_generator[ new ] = _widget_generator[ base ]

def make( option, **kwargs ):
	global _widget_generator
	name, syntax = option

	if _widget_generator.has_key( type( syntax ) ):
		return _widget_generator[ type( syntax ) ]( option, **kwargs )

	return None

def make_readonly( option, **kwargs ):
	global _widget_generator
	name, syntax = deepcopy( option )

	if _widget_generator.has_key( type( syntax ) ):
		syntax.may_change = False
		return _widget_generator[ type( syntax ) ]( ( name, syntax ), **kwargs )

	return None

# String & Integer
def _text_input( option, **kwargs ):
	name, syntax = option
	if syntax.may_change:
		return input.TextInput( option, **kwargs )
	else:
		return input.ReadOnlyInput( option, **kwargs )

register( values.String, _text_input )
register( values.Integer, _text_input )
register( values.EMailAddress, _text_input )
register( values.IP_Address, _text_input )

# Password
def _password_input( option, **kwargs ):
	name, syntax = option
	return input.SecretInput( option, **kwargs )

register( values.Password, _password_input )

# longer text fields

def _long_text_input( option, **kwargs ):
	return input.MultiLineInput( option, **kwargs )

register( values.Text, _long_text_input )

# Boolean
def _bool_input( option, **kwargs ):
	return input.Checkbox( option, **kwargs )

register( values.Boolean, _bool_input )

# Selection
def _select_input( option, **kwargs ):
	name, syntax = option
	if syntax.multivalue:
		return dynamic.MultiValue( option, **kwargs )
	return input.Selection( option, **kwargs )

register( values.StaticSelection, _select_input )
register( values.LanguageSelection, _select_input )
register( values.SystemRoleSelection, _select_input )

# ObjectSelect
def _dnlist_input( option, **kwargs ):
	name, syntax = option
	return dynamic.ObjectSelect( option, **kwargs )

register( values.ObjectDNList, _dnlist_input )

# FileUpload
def _fileupload_input( option, **kwargs ):
	name, syntax = option
	return dynamic.FileUpload( option, **kwargs )

register( values.FileUploader, _fileupload_input )
