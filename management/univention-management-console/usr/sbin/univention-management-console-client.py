#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
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

from optparse import OptionParser
from getpass import getpass

import os, readline, socket, sys

import notifier
import notifier.threads as threads

import univention.management.console.protocol as umcp
import univention.debug as ud

_commands = umcp.command_names()
_commands.append( 'HELP' )

def _completer( text, state ):
	global _commands
	result = []
	text = text.upper()
	for cmd in umcp.command_names():
		if cmd.startswith( text ):
			result.append( cmd )

	if len( result ) > state:
		return result[ state ]
	else:
		return None

def _options( text, state ):
	print readline.input_buffer().split( ' ' )

def _readline():
	readline.set_completer( _completer )

	while True:
		command = raw_input( ' > ' )
		if umcp.command_is_known( command ):
			break
		elif command == 'HELP':
			return ( command, None, None, None )
		else:
			print 'error: unknown command:', command

	readline.set_completer( None )
	arguments = []
	if umcp.command_has_arguments( command ):
		while True:
			arg = raw_input( ' argument: ' )
			if arg:
				arguments.append( arg )
			else:
				break

	options = []
	if umcp.command_has_options( command ):
		while True:
			opt = raw_input( ' option: ' )
			if opt:
				if len( opt.split( '=' ) ) != 2:
					print 'error: invalid option format: <option>=<value>'
				else:
					options.append( opt )
			else:
				break

	hosts = []
	while True:
		host = raw_input( ' host: ' )
		if host:
			hosts.append( host )
		else:
			break

	return ( command, arguments, options, hosts )

class CLI_Client( umcp.Client ):
	def __init__( self, options = [], arguments = [] ):
		if options.unix_socket and os.path.exists( options.unix_socket ):
			umcp.Client.__init__( self, unix = options.unix_socket,
								  ssl = False, auth = options.authenticate )
		else:
			umcp.Client.__init__( self, servername = options.server,
								  port = options.port,
								  auth = options.authenticate )
		self.__wait = None
		self.__input = ''
		self.__timer = None
		self.__interactive = options.interactive

		if not self.connect():
			raise Exception( 'error: failed to connect to daemon on host %s' % \
							 options.server )
		else:
			print "connection to '%s' established" % options.server

		self.signal_connect( 'response', self._response )
		self.signal_connect( 'authenticated', self._authenticated )
		self.signal_connect( 'closed', self._closed )
		if arguments:
			self.__wait = self.create( arguments[ 0 ],
									   arguments[ 1 : ], options.options,
									   options.hosts, options.incomplete )
		if options.authenticate:
			self.authenticate( options.username, options.password )
		else:
			if self.__wait:
				self.request( self.__wait )
				self.__wait = None
			elif self.__interactive:
				readline.parse_and_bind( 'tab: complete' )
				rl = threads.Simple( 'readline', _readline, self._input )
				rl.run()

	def create( self, command, args = [], options = [], hosts = [],
				incomplete = False ):
		msg = umcp.Request( command.upper(), incomplete = incomplete )
		msg.arguments = args
		for opt in options:
			key, value = opt.split( '=' )
			msg.options[ key ] = value
		if hosts:
			msg.hosts = hosts
		return msg

	def _closed( self ):
		print 'error: server closed connection'
		if self.__timer:
			notifier.timer_remove( self.__timer )
		sys.exit( 0 )

	def _authenticated( self, success, status, text ):
		if success:
			print 'authentication successful'
			if self.__wait:
				self.request( self.__wait )
				self.__wait = None
				return
			if self.__interactive:
				readline.parse_and_bind( 'tab: complete' )
				rl = threads.Simple( 'readline', _readline, self._input )
				rl.run()
		else:
			raise Exception( 'error: authentication failed' )

	def _waiting_for_response( self ):
		sys.stdout.write( '.' )
		sys.stdout.flush()
		return True

	def _input( self, name, output ):
		req = self.create( *output )
		self.request( req )
		print "waiting for response to '%s' " % req.command,
		self.__timer = notifier.timer_add( 1000, self._waiting_for_response )

	def _response( self, msg ):
		notifier.timer_remove( self.__timer )
		self.__timer = None
		if self.__interactive:
			print ' found'
		print 'server replied:', msg.command
		print '  data length: %d' % len( str( msg ) )
		print '  message length: %d' % msg._length
		if msg.arguments:
			print '  arguments:', msg.arguments
		if msg.options:
			print '  options:', msg.options
		if msg.hosts:
			print '  hosts:', msg.hosts
		if msg.dialog:
			print '  dialog:', msg.dialog[ 0 ]
		print '  complete body:', msg.body
		if self.__interactive:
			readline.parse_and_bind( 'tab: complete' )
			rl = threads.Simple( 'readline', _readline, self._input )
			rl.run()
		else:
			sys.exit( 0 )

if __name__ == '__main__':
	notifier.init( notifier.GENERIC )

	parser = OptionParser( usage = "usage: %prog [options] command <arguments>" )
	parser.add_option( '-i', '--interactive', action = 'store_true',
					   dest = 'interactive',
					   help = 'provides a shell-like interactive interface' )
	parser.add_option( '-n', '--no-auth', action = 'store_false',
					   dest = 'authenticate', default = True,
					   help = 'if given the client do not try to authenticate first' )
	parser.add_option( '-s', '--server', type = 'string', action = 'store',
					   dest = 'server', default = 'localhost',
					   help = 'defines the host of the UMC daemon to connect to' )
	parser.add_option( '-p', '--port', type = 'int', action = 'store',
					   dest = 'port', default = '6670',
					   help = 'defines the port to connect to' )
	parser.add_option( '-u', '--unix-socket', type = 'string', action = 'store',
					   dest = 'unix_socket',
					   help = 'defines the filename of the UNIX socket' )
	parser.add_option( '-U', '--username', type = 'string',
					   action = 'store', dest = 'username',
					   help = 'set username for authentication' )
	parser.add_option( '-P', '--password', type = 'string',
					   action = 'store', dest = 'password',
					   help = 'set password for authentication' )
	parser.add_option( '-o', '--option', type = 'string', default = [],
					   action = 'append', dest = 'options',
					   help = 'append an option to the request' )
	parser.add_option( '-I', '--incomplete', action = 'store_true',
					   dest = 'incomplete',
					   help = 'if given it is known that the request has incomplete options for the command' )
	parser.add_option( '-H', '--host', type = 'string', default = [],
					   action = 'append', dest = 'hosts',
					   help = 'extend list of destination hosts' )
	parser.add_option( '-d', '--debug', action = 'store', type = 'int',
					   dest = 'debug', default = 0,
					   help = 'if given than debugging is activated and set to the specified level' )

	( options, arguments ) = parser.parse_args()

	if options.debug > 0:
		ud.init( '/var/log/univention/management-console-client.log', 1, 1 )
		ud.set_level( ud.ADMIN, options.debug )
	else:
		ud.init( '/dev/null', 0, 0 )

	if not options.interactive and not arguments:
		parser.error( 'command is missing' )
	if options.authenticate:
		if not options.username:
			options.username = raw_input( 'Username:' )
		if not options.password:
			options.password = getpass( 'Password:' )
	client = CLI_Client( options, arguments )

	notifier.loop()
