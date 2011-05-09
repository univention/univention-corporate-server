#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  UMCP 2.0 messages
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

import time
import re

try:
	import simplejson as json
except:
	import json

from definitions import *

import univention.management.console.locales as locales

_ = locales.Translation( 'univention.management.console' ).translate

class Message( object ):
	"""This class represents a protocol message of UMCP"""
	RESPONSE, REQUEST = range( 0, 2 )

	_header = re.compile( '(?P<type>REQUEST|RESPONSE)/(?P<id>[\d-]+)/(?P<length>\d+): ?(?P<command>\w+) ?(?P<arguments>[^\n]+)?', re.UNICODE )
	__counter = 0

	def __init__( self, type = REQUEST, command = '', data = None, arguments = [], options = {} ):
		"""Parser for UMCP 2.0 messages """
		self._id = None
		self._length = 0
		self._type = type
		self.command = command
		self.arguments = arguments
		self.options = options
		self.body = {}
		if data:
			self.parse( data )

	def __str__( self ):
		"""returns the formatted message"""
		type = 'RESPONSE'
		if self._type == Message.REQUEST:
			type = 'REQUEST'
		if self.options:
			self.body[ '_options' ] = self.options

		data = json.dumps( self.body )
		args = ''
		if self.arguments:
			args = ' '.join( map( lambda x: str( x ), self.arguments ) )
		return '%s/%s/%d: %s %s\n%s' % ( type, self._id, len( data ),
										 self.command, args, data )

	def _create_id( self ):
		# cut off 'L' for long
		self._id = '%lu-%d' % ( long( time.time() * 100000 ),
								Message.__counter )
		Message.__counter += 1

	def recreate_id( self ):
		self._create_id()

	def isType( self, type ):
		return ( self._type == type )

	def id( self, num = None ):
		if not num:
			return self._id
		else:
			self._id = num

	# property: message
	def _set_message( self, msg ):
		self.body[ '_message' ] = msg

	def _get_message( self ):
		return self.body.get( '_message' )

	message = property( _get_message, _set_message )

	# property: result
	def _set_result( self, data ):
		self.body[ '_result' ] = data

	def _get_result( self ):
		return self.body.get( '_result' )

	result = property( _get_result, _set_result )

	# property: status
	def _set_status( self, code ):
		self.body[ '_status' ] = int( code )

	def _get_status( self ):
		return self.body.get( '_status' )

	status = property( _get_status, _set_status )

	def parse( self, msg ):
		import univention.debug as ud

		lines = msg.split( '\n', 1 )

		# is the format of the header line valid?
		match = Message._header.match( lines[ 0 ] )
		if not match:
			raise ParseError( 551, 'unparsable message header' )

		groups = match.groupdict()
		if groups[ 'type' ] == 'REQUEST':
			self._type = Message.REQUEST
		else:
			self._type = Message.RESPONSE
		self._id = groups[ 'id' ]
		self._length = int( groups[ 'length' ] )
		self.command = groups[ 'command' ]

		# known command?
		if not command_is_known( self.command ):
			raise UnknownCommandError( 552, 'unknown UMCP command: %s' % \
									   self.command )

		if groups.get( 'arguments' ):
			if command_has_arguments( self.command ):
				self.arguments = groups[ 'arguments' ].split( ' ' )
			else:
				raise InvalidArgumentsError( 553, _( "The command '%s' do not have any arguments" ) % self.command )
		# invalid/missing message body?
		if len( lines ) < 2 or self._length > len( lines[ 1 ] ):
			raise IncompleteMessageError( 'Part of the body is missing' )

		remains = ''
		if len( lines[ 1 ] ) > self._length:
			remains = lines[ 1 ][ self._length : ]
		try:
			if len( lines[ 1 ] ) > self._length:
				self.body = json.loads( lines[ 1 ][ : self._length ] )
			else:
				self.body = json.loads( lines[ 1 ] )
		except:
			ud.debug( ud.ADMIN, ud.ERROR, 'values: ERROR: UMCP PARSING ERROR' )
			raise ParseError( 554, 'error parsing UMCP message body' )

		for key in ( '_options', ):
			if key in self.body:
				setattr( self, key[ 1 : ], self.body[ key ] )

		return remains

	def set_flag( self, key, value ):
		if key and not key[ 0 ] == '_':
			self.body[ key ] = value

	def get_flag( self, key ):
		return self.body[ key ]

	def has_flag( self, option ):
		return option in self.body

class Request( Message ):
	"""This class describes a request from the console frontend to the
	console daemon"""

	def __init__( self, command, args = [], opts = {} ):
		if not command_is_known( command ):
			raise UnknownCommandError( "'%s' is not a valid UMCP command" % command )
		Message.__init__( self, Message.REQUEST, command, arguments = args, options = opts )
		self._create_id()

class Command( Request ):
	def __init__( self, args = [], opts = {} ):
		Request.__init__( self, 'COMMAND', args, opts )

class SimpleCommand( Request ):
	def __init__( self, command, options = {}, **flags ):
		Request.__init__( self, 'COMMAND',  [ command ], options )
		for k, v in flags.items():
			self.set_flag( 'web:%s' % k, v )

class Response( Message ):
	"""This class describes a response to a request from the console
	frontend to the console daemon"""
	def __init__( self, request = None, data = None ):
		Message.__init__( self, Message.RESPONSE )
		if request:
			self._id = request._id
			self.command = request.command
			self.arguments = request.arguments
			self.options = request.options
			if '_status' in request.body:
				self.status = request.status
		elif data:
			self.parse( data )

	def isFinal( self ):
		return ( self._id and self.status != 210 )

	recreate_id = None

class ParseError( Exception ):
	pass

class IncompleteMessageError( Exception ):
	pass

class UnknownCommandError( Exception ):
	pass

class InvalidArgumentsError( Exception ):
	pass

if __name__ == '__main__':
	# encode
	auth = Request( 'AUTH' )
	auth.body[ 'username' ] = 'fasel'
	auth.body[ 'password' ] = 'secret'
	req = Request( 'COMMAND', 'cups/list', args = [ 'slave.domain.tld' ] )
	res = Response( req )

	for msg in ( req, res, auth ):
		if msg.isType( Message.REQUEST ): print ">>> a request:",
		if msg.isType( Message.RESPONSE ): print "<<< a response:",
		print msg

	print Message( data = str( auth ) )
	# decode
	data = str( req )
	msg = Message( data = data )
	print msg
