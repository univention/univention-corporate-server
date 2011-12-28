#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  UMCP definitions like commands, error codes etc.
#
# Copyright 2006-2011 Univention GmbH
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

import sys

from univention.lib.i18n import NullTranslation

_ = NullTranslation( 'univention.management.console' ).translate

# buffer size for reading commands from socket
RECV_BUFFER_SIZE = 65536

class CommandDefinition( object ):
	def __init__( self, name, has_arguments, *options ):
		self._name = name
		self._has_arguments = has_arguments
		self._options = options

	@property
	def name( self ):
		return self._name

	@property
	def has_arguments( self ):
		return self._has_arguments

	@property
	def options( self ):
		return self._options

COMMANDS = (
	CommandDefinition( 'AUTH', False, 'username', 'password' ),
	CommandDefinition( 'COMMAND', True ),
	CommandDefinition( 'VERSION', False ),
	CommandDefinition( 'GET', True ),
	CommandDefinition( 'SET', True ),
	CommandDefinition( 'CLOSE', False ),
	CommandDefinition( 'STATISTICS', False ),
	CommandDefinition( 'CANCEL', False, 'ids' ),
	CommandDefinition( 'STATUS', False, 'ids' ),
	CommandDefinition( 'EXIT', True ),
	CommandDefinition( 'UPLOAD', True ),
)

class Status( object ):
	def __init__( self, name, code, description ):
		self._name = name
		self._code = code
		self._description = description

	@property
	def name( self ):
		return self._name

	@property
	def code( self ):
		return self._code

	@property
	def description( self ):
		if self._description:
			return self._description
		return _( 'Unknown status code' )

STATUS = (
	# UMCP request success messages
	Status( 'SUCCESS'							, 200, _( 'OK, operation successful' ) ),
	Status( 'SUCCESS_MESSAGE'					, 204, _( 'OK, containing report message' ) ),
	Status( 'SUCCESS_PARTIAL'					, 206, _( 'OK, partial response' ) ), # not yet used
	Status( 'SUCCESS_SHUTDOWN'					, 250, _( 'OK, operation successful ask for shutdown of connection' ) ),

	Status( 'CLIENT_ERR_NONFATAL'				, 301, _( 'A non-fatal error has occured processing may continue' ) ),

	# the UMCP request was parsable but within the context it is not valid
	Status( 'BAD_REQUEST'						, 400, _( 'Bad request' ) ),
	Status( 'BAD_REQUEST_UNAUTH'				, 401, _( 'Unauthorized' ) ),
	Status( 'BAD_REQUEST_FORBIDDEN'				, 403, _( 'Forbidden' ) ),
	Status( 'BAD_REQUEST_NOT_FOUND'				, 404, _( 'Not found' ) ),
	Status( 'BAD_REQUEST_INVALID_ARGS'			, 406, _( 'Invalid command arguments' ) ),
	Status( 'BAD_REQUEST_INVALID_OPTS'			, 407, _( 'Invalid or missing command options' ) ),
	Status( 'BAD_REQUEST_AUTH_FAILED'  			, 411, _( 'The authentication has failed' ) ),
	Status( 'BAD_REQUEST_ACCOUNT_EXPIRED'		, 412, _( 'The account is expired and can not be used anymore' ) ),
	Status( 'BAD_REQUEST_ACCOUNT_DISABLED'		, 413, _( 'The account as been disabled' ) ),
	Status( 'BAD_REQUEST_UNAVAILABLE_LOCALE'	, 414, _( 'Specified locale is not available' ) ),

	# UMCP server core errors
	Status( 'SERVER_ERR'						, 500, _( 'Internal error' ) ),
	Status( 'SERVER_ERR_MODULE_DIED'			, 510, _( 'Module process died unexpectedly' ) ),
	Status( 'SERVER_ERR_MODULE_FAILED'			, 511, _( 'Connection to module process failed' ) ),
	Status( 'SERVER_ERR_CERT_NOT_TRUSTWORTHY'	, 512, _( 'SSL server certificate is not trustworthy' ) ),

	# generic UMCP parser errors
	Status( 'UMCP_ERR_UNPARSABLE_HEADER'		, 551, _( 'Unparsable message header' ) ),
	Status( 'UMCP_ERR_UNKNOWN_COMMAND'			, 552, _( 'Unknown command' ) ),
	Status( 'UMCP_ERR_ARGS_MISSMATCH'			, 553, _( 'Invalid number of arguments' ) ),
	Status( 'UMCP_ERR_UNPARSABLE_BODY'			, 554, _( 'Unparsable message body' ) ),

	# errors occuring during command process in module process
	Status( 'MODULE_ERR'						, 590, _( 'Error occuried during command processing' ) ),
	Status( 'MODULE_ERR_COMMAND_FAILED'			, 591, _( 'The execution of a command caused an fatal error' ) )
)

# create symbols for status codes
for status in STATUS:
	setattr( sys.modules[ 'univention.management.console.protocol.definitions' ], status.name, status.code )

def command_get( name ):
	for cmd in COMMANDS:
		if cmd.name == name:
			return cmd
	return None

def command_is_known( name ):
	return command_get( name ) is not None

def command_has_arguments( name ):
	cmd = command_get( name )
	return cmd is not None and cmd.has_arguments == True

def status_description( code ):
	for status in STATUS:
		if status.code == code:
			return status.description

	return _( 'Unknown status code' )

def status_get( code ):
	for status in STATUS:
		if status.code == code:
			return status
	return None
