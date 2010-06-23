# -*- coding: utf-8 -*-
#
# Univention Management Console
#  UMC syntax definitions
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

import re

import locales

import univention.debug as ud

_ = locales.Translation( 'univention.management.console' ).translate

class Value( object ):
	""" This class describes an UMC command arguments. Mandatory are the
	attributes 'name', providing a translated name, and 'syntax' that is
	a basic Python type or a Univention Admin Syntax class. If
	'multivalue' is True attributes of this type should always be a list
	or tuple. Only if 'required' is set to True the attribute has to
	exist."""
	def __init__( self, label, syntax, multivalue = False, required = True,
				  may_change = True, regex = None ):
		self.label = label
		self.syntax = syntax
		self.multivalue = multivalue
		self.required = required
		self.may_change = may_change
		if regex:
			self.regex = re.compile( regex )
		else:
			self.regex = None

		# contains the last error description
		self.error = ''

	def _item_valid( self, value, syntax = None ):
		if not syntax:
			syntax = self.syntax
		if not syntax:
			return True
		if not self.required and not value:
			return True
		if ( isinstance( syntax, Value ) and syntax.is_valid( value ) ) or \
			   isinstance( value, syntax ):
			if self.regex:
				if self.regex.match( value ):
					return True
				else:
					self.error = _( 'value contains invalid characters' )
			else:
				return True

		return False

	def is_valid( self, value ):
		self.error = ''
		if self.multivalue:
			if not isinstance( value, ( list, tuple ) ):
				return False
			for v in value:
				if not self._item_valid( v, self.syntax ):
					return False
			return True
		else:
			return self._item_valid( value, self.syntax )

	def convert( self, value ):
		return value

class SyntaxError( Exception ):
	def __init__( self, *args ):
		Exception.__init__( self, *args )

class MultiValue( Value ):
	def __init__( self, label, syntax, required = False, may_change = True ):
		Value.__init__( self, label, syntax, multivalue = True,
						required = required, may_change = may_change )

# some basic value types
class Boolean( Value ):
	def __init__( self, label, required = True, may_change = True ):
		Value.__init__( self, label, bool, required = required, may_change = may_change )

	def is_valid( self, value ):
		if value in ( '0', None, '1', 'checked' ):
			return True
		return False

	def convert( self, value ):
		if value in ( '0', None ):
			return False
		return True

class String( Value ):
	def __init__( self, label, required = True, regex = None, may_change = True ):
		Value.__init__( self, label, basestring, required = required, regex = regex,
						may_change = may_change )

class Password( Value ):
	def __init__( self, label, required = True, regex = None, may_change = True ):
		Value.__init__( self, label, basestring, required = required, regex = regex,
						may_change = may_change )

class Text( Value ):
	def __init__( self, label, required = True, regex = None, may_change = True ):
		Value.__init__( self, label, basestring, required = required, regex = regex,
						may_change = may_change )

class EMailAddress( String ):
	def __init__( self, label = _( 'E-Mail address' ), required = True, may_change = True ):
		String.__init__( self, label = label, regex = '[a-zA-Z.-]+@[a-zA-Z.]+',
						 required = required, may_change = may_change )

class IP_Address( String ):
	def __init__( self, label = _( 'IP address' ), required = True, may_change = True ):
		String.__init__( self, label = label,
						 regex = '(?P<a>[0-9]{1,3})\.(?P<b>[0-9]{1,3})\.(?P<a>[0-9]{1,3})\.(?P<b>[0-9]{1,3})',
						 required = required, may_change = may_change )

	def is_valid( self, value ):
		ret = String.is_valid( value )
		if ret:
			m = self.regex( value ).groupdict()
			for net, val in m.items():
				if not 0 <= int( val ) <= 255:
					self.error = _( 'Invalid number (%s). Must be between 0 and 255' ) % val
					return False
		return ret

class Integer( Value ):
	def __init__( self, label, required = True, may_change = True ):
		Value.__init__( self, label, int, required = required, may_change = may_change )

	def is_valid( self, value ):
		if isinstance( value, basestring ):
			try:
				value = int( value )
			except:
				self.error = _( 'Value is not a valid integer number.' )
				return False
		return Value.is_valid( self, value )

# single value selections
class StaticSelection( Value ):
	"""This class represents a selection box with a static set of values
	defined by the member variable 'choices'."""
	def __init__( self, label, required = True, may_change = True ):
		Value.__init__( self, label, basestring, required = required, may_change = may_change )

	def is_valid( self, value ):
		choices = map( lambda x: x[ 0 ], self.choices() )
		if not self.multivalue:
			if not value in choices:
				self.error = _( 'invalid value.' )
				return False
			return True
		else:
			if not value and self.required:
				self.error = _( 'At least one entry is required.' )
				return False
			for item in value:
				if not item in choices:
					return False

		return True

	def choices( self ):
		return ()

class LanguageSelection( StaticSelection ):
	def __init__( self, label, required = True, may_change = True ):
		StaticSelection.__init__( self, label, required = required, may_change = may_change )

	def choices( self ):
		return ( ( 'de', _( 'German' ) ), ( 'en', _( 'English' ) ) )

class SystemRoleSelection( StaticSelection ):
	def __init__( self, label, required = True, may_change = True ):
		StaticSelection.__init__( self, label, required = required, may_change = may_change )

	def choices( self ):
		return ( ( 'domaincontroller_master', _( 'Domain controller Master' ) ),
				 ( 'domaincontroller_backup', _( 'Domain controller Backup' ) ),
				 ( 'domaincontroller_slave', _( 'Domain controller Slave' ) ),
				 ( 'memberserver', _( 'Member Server' ) ),
				 ( 'managed_client', _( 'Managed Client' ) ),
				 ( 'mobile_client', _( 'Mobile Client' ) ) )

# multi values
class IMultiSequenceValue( MultiValue ):
	def __init__( self, label, syntax, required = True, may_change = True ):
		MultiValue.__init__( self, label, syntax = syntax, required = required,
							 may_change = may_change )

	def is_valid( self, value ):
		if not isinstance( value, ( list, tuple ) ):
			return False
		for item in value:
			if isinstance( item, ( list, tuple ) ):
				for v in item:
					if not self._item_valid( v ):
						return False
			if isinstance( item, dict ):
				for k, v in item.items():
					if not self.syntax.has_key ( k ):
						return False
					if not self.syntax[ k ].required and not v:
						continue
					if not v:
						self.error = _( 'A value is required.' )
						return False
					if not self._item_valid( v, self.syntax[ k ] ):
						return False

		return True

class MultiListValue( IMultiSequenceValue ):
	def __init__( self, label, syntax, required = True, may_change = True ):
		if not isinstance( syntax, ( list, tuple ) ):
			raise AttributeError( 'syntax must be of type list or tuple' )
		IMultiSequenceValue.__init__( self, label, syntax = syntax, required = required,
									  may_change = may_change )

class MultiDictValue( IMultiSequenceValue ):
	def __init__( self, label, syntax, required = True, may_change = True ):
		if not isinstance( syntax, dict ):
			raise AttributeError( 'syntax must be of type dict' )
		IMultiSequenceValue.__init__( self, label, syntax = syntax, required = required,
									  may_change = may_change )

class StringList( MultiValue ):
	def __init__( self, label, required = True, may_change = True ):
		MultiValue.__init__( self, label, basestring, required = required, may_change = may_change )

class IntegerList( MultiValue ):
	def __init__( self, label, required = True, may_change = True ):
		MultiValue.__init__( self, label, int, required = required, may_change = may_change )

class ObjectDNList( StringList ):
	def __init__( self, label, required = True, may_change = True ):
		StringList.__init__( self, label, required = required, may_change = may_change )

class FileUploader( StringList ):
	def __init__( self, label, required = True, may_change = True ):
		StringList.__init__( self, label, required = required, may_change = may_change )
