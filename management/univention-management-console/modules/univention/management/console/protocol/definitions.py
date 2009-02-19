#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  UMCP definitions like commands, error codes etc.
#
# Copyright (C) 2006-2009 Univention GmbH
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

import univention.management.console.locales as locales

_ = locales.Translation( 'univention.management.console.protocol' ).translate

__all__ = ( 'command_names', 'command_is_known', 'command_has_arguments',
			'command_has_options', 'command_is_valid_option',
			'status_information' )

COMMANDS = {
	'AUTH' : ( False, ( 'username', 'password' ) ),
	'COMMAND' : ( True, () ),
	'VERSION' : ( False, None ),
	'GET' : ( True, () ),
	'SET' : ( True, () ),
	'CLOSE' : ( False, None ),
	'CANCEL' : ( False, ( 'ids', ) ),
	'STATUS' : ( False, ( 'ids', ) ),
	'EXIT' : ( True, () ),
}

STATUSINFORMATION = {
	200 : _( 'OK, operation successful' ),
	210 : _( 'OK, partial response' ),
	300 : _( 'Command currently not available/possible' ),
	400 : _( 'Invalid UMCP message' ),
	401 : _( 'Unknown command or not permitted to run' ),
	402 : _( 'Invalid command arguments' ),
	403 : _( 'Incomplete command' ),
	404 : _( 'Invalid body object' ),
	405 : _( 'Unparsable message header' ),
	410 : _( 'Unauthorized' ),
	411 : _( 'Authentication failed' ),
	412 : _( 'Account is expired' ),
	413 : _( 'Account is disabled' ),
	414 : _( 'Access to console daemon is prohibited' ),
	415 : _( 'Command execution prohibited' ),
	500 : _( 'Internal error' ),
	501 : _( 'Request could not be found' ),
	502 : _( 'Module process died unexpectedly' ),
	503 : _( 'Connection to module process failed' ),
	504 : _( 'SSL server certificate is not trustworthy' ),
	600 : _( 'Error occuried during command processing' ),
	601 : _( 'Specified locale is not available' ),
	}

def command_names():
	return COMMANDS.keys()

def command_is_known( name ):
	return ( name in COMMANDS.keys() )

def command_has_arguments( name ):
	return ( COMMANDS.has_key( name ) and COMMANDS[ name ][ 0 ] )

def command_has_options( name ):
	return ( COMMANDS.has_key( name ) and COMMANDS[ name ][ 1 ] )

def command_is_valid_option( name, option ):
	if COMMANDS.has_key( name ):
		valid = COMMANDS[ name ][ 1 ]
		if valid == None: return False
		if not len( valid ): return True
		return ( option in valid )
	return False

def status_information( status ):
	if STATUSINFORMATION.has_key( status ):
		return STATUSINFORMATION[ status ]
	return _( 'Unknown state' )
