#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  UMCP messages
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

import cPickle
import time
import re

from definitions import *

import univention.management.console.locales as locales

import univention.debug as ud

_ = locales.Translation( 'univention.management.console.protocol' ).translate

class Message( object ):
	"""This class represents a protocol message of UMCP"""
	RESPONSE, REQUEST = range( 0, 2 )

	_header = re.compile( '(?P<type>REQUEST|RESPONSE)/(?P<id>[\d-]+)/(?P<length>\d+): ?(?P<command>\w+) ?(?P<arguments>[^\n]+)?', re.UNICODE )

	def __init__( self, type = REQUEST, command = '', data = None,
				  arguments = [], options = {}, hosts = [], dialog = None,
				  module = None, incomplete = False, report = '' ):
		""" """
		self._id = None
		self._length = 0
		self._type = type
		self.command = command
		self.hosts = hosts
		self.arguments = arguments
		self.options = options
		self.dialog = dialog
		self.module = module
		self.incomplete = incomplete
		self.report = report
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
		if self.hosts:
			self.body[ '_hosts' ] = self.hosts
		if self.dialog:
			self.body[ '_dialog' ] = self.dialog
		if self.module:
			self.body[ '_module' ] = self.module
		if self.report:
			self.body[ '_report' ] = self.report

		if self.incomplete:
			self.body[ '_incomplete' ] = self.incomplete
		data = cPickle.dumps( self.body, 0 )
		args = ''
		if self.arguments:
			args = ' '.join( map( lambda x: str( x ), self.arguments ) )
		return '%s/%s/%d: %s %s\n%s' % ( type, self._id, len( data ),
										 self.command, args, data )

	def isType( self, type ):
		return ( self._type == type )

	def id( self, num = None ):
		if not num:
			return self._id
		else:
			self._id = num

	def status( self, code = None ):
		if not code:
			if self.body.has_key( '_status' ):
				return self.body[ '_status' ]
			else:
				return None
		else:
			self.body[ '_status' ] = int( code )

	def parse( self, msg ):
		import univention.debug as ud

		lines = msg.split( '\n', 1 )

		# is the format of the header line valid?
		match = Message._header.match( lines[ 0 ] )
		if not match:
			raise ParseError( 405, 'unparsable message header' )

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
			raise UnknownCommandError( 401, 'unknown UMCP command: %s' % \
									   self.command )

		if groups.has_key( 'arguments' ) and groups[ 'arguments' ]:
			if command_has_arguments( self.command ):
				self.arguments = groups[ 'arguments' ].split( ' ' )
			else:
				raise InvalidArgumentsError( 402, _( "The command '%s' do not have any arguments" % self.command ) )
		# invalid/missing message body?
		if len( lines ) < 2 or self._length > len( lines[ 1 ] ):
			if len(lines) >= 2:
				ud.debug( ud.ADMIN, ud.INFO, 'values: %d %d' % ( self._length, len( lines[ 1 ] ) ) )
			else:
				ud.debug( ud.ADMIN, ud.INFO, 'values: %d ---' % self._length )
			raise IncompleteMessageError( 'Part of the body is missing' )

		ud.debug( ud.ADMIN, ud.INFO, 'values: %d %d' % ( self._length, len( lines[ 1 ] ) ) )

		remains = ''
		if len( lines[ 1 ] ) > self._length:
			remains = lines[ 1 ][ self._length : ]
		try:
			if len( lines[ 1 ] ) > self._length:
				self.body = cPickle.loads( lines[ 1 ][ : self._length ] )
			else:
				self.body = cPickle.loads( lines[ 1 ] )
		except:
			ud.debug( ud.ADMIN, ud.ERROR, 'values: ERROR: UMCP PARSING ERROR' )
			raise ParseError( 404, 'error parsing UMCP message body' )

		if self.body.has_key( '_hosts' ):
			self.hosts = self.body[ '_hosts' ]
		if self.body.has_key( '_options' ):
			self.options = self.body[ '_options' ]
		if self.body.has_key( '_incomplete' ):
			self.incomplete = self.body[ '_incomplete' ]
		else:
			self.incomplete = False
		if self.body.has_key( '_dialog' ):
			self.dialog = self.body[ '_dialog' ]
		if self.body.has_key( '_module' ):
			self.module = self.body[ '_module' ]
		if self.body.has_key( '_report' ):
			self.report = self.body[ '_report' ]

		return remains

	def set_flag( self, key, value ):
		if key and not key[ 0 ] == '_':
			self.body[ key ] = value

	def get_flag( self, key ):
		return self.body[ key ]

	def has_flag( self, option ):
		return self.body.has_key( option )

class Request( Message ):
	"""This class describes a request from the console frontend to the
	console daemon"""

	__counter = 0
	def __init__( self, command, args = [], opts = {}, hosts = None, incomplete = False ):
		if not command_is_known( command ):
			raise UnknownCommandError( "'%s' is not a valid UMCP command" % command )
		Message.__init__( self, Message.REQUEST, command, arguments = args,
						  options = opts, hosts = hosts,
						  incomplete = incomplete )
		self.__create_id()

	def __create_id( self ):
		# cut off 'L' for long
		self._id = '%lu-%d' % ( long( time.time() * 100000 ),
								Request.__counter )
		Request.__counter += 1

	def recreate_id( self ):
		self.__create_id()

class Command( Request ):
	def __init__( self, args = [], opts = {}, hosts = None, incomplete = False ):
		Request.__init__( self, 'COMMAND', args, opts, hosts, incomplete )

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
			self.hosts = request.hosts
			self.module = request.module
			self.report = request.report
			self.dialog = request.dialog
			if request.body.has_key( '_status' ):
				self.status( request.status() )
		elif data:
			self.parse( data )

	def isFinal( self ):
		return ( self._id and self.status() != 210 )

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
