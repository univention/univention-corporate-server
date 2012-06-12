# -*- coding: utf-8 -*-
#
# Univention Management Console
#  UMC syntax definitions
#
# Copyright 2011-2012 Univention GmbH
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

import os
import re
import sys

from univention.lib.i18n import Translation

_ = Translation( 'univention.management.console' ).translate

class SyntaxVerificationError( Exception ):
	pass

#
# load all additional syntax files from */site-packages/univention/management/console/syntax.d/*.py
#
PREFIX_SYNTAX = 'univention/management/console'

def import_verification_functions():
	for dir in sys.path:
		if os.path.exists( os.path.join( dir, PREFIX_SYNTAX, 'syntax.py' ) ):
			if os.path.isdir( os.path.join( dir, PREFIX_SYNTAX, 'syntax.d/' ) ):
				for f in os.listdir( os.path.join( dir, PREFIX_SYNTAX, 'syntax.d/' ) ):
					if f.endswith('.py'):
						fn = os.path.join( dir, PREFIX_SYNTAX, 'syntax.d/', f )
						try:
							fd = open( fn, 'r' )
							exec fd in univention.management.console.verify.__dict__
						except:
							pass

def is_boolean( value, syntax, verify_function ):
	if not isinstance( value, bool ):
		raise SyntaxVerificationError( _( 'Value is not an boolean' ) )

	return True

def is_integer( value, syntax, verify_function ):
	if not isinstance( value, int ):
		raise SyntaxVerificationError( _( 'Value is not an integer' ) )

	return True

def is_float( value, syntax, verify_function ):
	if not isinstance( value, float ):
		raise SyntaxVerificationError( _( 'Value is not n floating point number' ) )

	return True

def _compile_regex( regular_expression ):
	try:
		regex = re.compile( regular_expression )
	except re.error, e:
		raise SyntaxVerificationError( _( 'Invalid regular expression (%(regex)s): %(message)s' ) % { 'regex' : syntax.regex, 'message' : str( e ) } )

	return regex

def is_string( value, syntax, verify_function ):
	if not isinstance( value, basestring ):
		raise SyntaxVerificationError( _( 'Value is not of type string' ) )

	if syntax.regex:
		regex = _compile_regex( syntax.regex )
		if not regex.match( value ):
			raise SyntaxVerificationError( _( 'Value contains invalid characters' ) )
	elif syntax.regex_invalid:
		regex = _compile_regex( syntax.regex_invalid )
		if regex.match( value ):
			raise SyntaxVerificationError( _( 'Value contains invalid characters' ) )

	return True

def is_list( value, syntax, verify_function ):
	if not isinstance( value, ( list, tuple ) ):
		raise SyntaxVerificationError( _( 'Value is not a list' ) )

	return True

def is_dict( value, syntax, verify_function ):
	if not isinstance( value, dict ):
		raise SyntaxVerificationError( _( 'Value is not a dictionary' ) )

	if syntax.item:
		key_syntax, value_syntax = syntax.item

		if not key_syntax and not value_syntax:
			return True

		for key, val in value.items():
			if key_syntax:
				verify_function( key_syntax, key )
			if value_syntax:
				verify_function( value_syntax, val )

	return True

def is_selection( value, syntax, verify_function ):
	if not isinstance( value, basestring ):
		raise SyntaxVerificationError( _( 'Value is not of type string' ) )

	if not syntax.choices:
		raise SyntaxVerificationError( _( 'No valid choices specified' ) )

	if not value in syntax.choices:
		raise SyntaxVerificationError( _( 'Value does not match any of the specified choices' ) )

	return True
