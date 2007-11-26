#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  session handling
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

import locale, sys, os, string, ldap

import notifier
import notifier.signals as signals
import notifier.popen as popen

from OpenSSL import *

import univention.uldap

from message import *
from client import *
from version import *
from definitions import *

from univention.management.console.modules import Manager
from univention.management.console.auth import AuthHandler
from univention.management.console.acl import ConsoleACLs
import univention.management.console.categories as categories
import univention.management.console as umc

class State( signals.Provider ):
	def __init__( self, client, socket ):
		signals.Provider.__init__( self )
		self.__auth = AuthHandler()
		self.__auth.signal_connect( 'authenticated', self._authenticated )
		self.client = client
		self.socket = socket
		self.processor = None
		self.authenticated = False
		self.buffer = ''
		self.requests = {}
		self.authResponse = None
		self.signal_new( 'authenticated' )
		self.resend_queue = []

	def __del__( self ):
		ud.debug( ud.ADMIN, ud.PROCESS, 'State: dying' )
		del self.processor

	def _authenticated( self, success ):
		self.signal_emit( 'authenticated', success, self )

	def authenticate( self, username, password ):
		self.__auth.authenticate( username, password )

	def credentials( self ):
		return self.__auth.credentials()


class ModuleProcess( Client ):
	COMMAND = '/usr/sbin/univention-management-console-module'

	def __init__( self, module, interface, debug = '0', locale = None ):
		socket = '/var/run/univention-management-console/%u-%lu.socket' % \
				 ( os.getpid(), long( time.time() * 1000 ) )
		# determine locale settings
		args = [ ModuleProcess.COMMAND, '-m', module, '-s', socket,
				 '-i', interface, '-d', debug ]
		if locale:
			args.extend( ( '-l', '%s' % locale ) )
			self.__locale = locale
		else:
			self.__locale = None
		Client.__init__( self, unix = socket, ssl = False, auth = False )
		self.signal_connect( 'response', self._response )
		ud.debug( ud.ADMIN, ud.PROCESS, 'running: %s' % args )
		self.__process = popen.RunIt( args, stdout = False )
		self.__process.signal_connect( 'finished', self._died )
		self.__pid = self.__process.start()
		self._connect_retries = 1
		self.signal_new( 'result' )
		self.signal_new( 'finished' )
		self.name = module

	def __del__( self ):
		ud.debug( ud.ADMIN, ud.PROCESS, 'ModuleProcess: dying' )
		self.disconnect()
		self.__process.stop()
		ud.debug( ud.ADMIN, ud.PROCESS, 'ModuleProcess: child stopped' )

	def _died( self, pid, status ):
		ud.debug( ud.ADMIN, ud.PROCESS, 'ModuleProcess: child died' )
		self.signal_emit( 'finished', pid, status, self.name )

	def _response( self, msg ):
		if msg.command == 'SET' and 'commands/permitted' in msg.arguments:
			return

		self.signal_emit( 'result', msg )

	def pid( self ):
		return self.__pid

class Processor( signals.Provider ):
	def __init__( self, username, password ):
		self.__username = username
		self.__password = password
		# default interface is 'web'
		self.__interface = 'web'
		signals.Provider.__init__( self )

		# initialize the handler modules
		self.__manager = Manager()

		# stores the module processes [ modulename ] = <>
		self.__processes = {}
		self.__locale = None

		self.__killtimer = {}

		lo = ldap.open( umc.baseconfig[ 'ldap/server/name' ] )

		try:
			userdn = lo.search_s( umc.baseconfig[ 'ldap/base' ], ldap.SCOPE_SUBTREE,
								  '(&(objectClass=person)(uid=%s))' % self.__username )[ 0 ][ 0 ]

			self.lo = univention.uldap.access( host = umc.baseconfig[ 'ldap/server/name' ],
											   base = umc.baseconfig[ 'ldap/base' ], binddn = userdn,
											   bindpw = self.__password, start_tls = 2 )
		except:
			self.lo = None

		# read the ACLs
		self.acls = ConsoleACLs( self.lo, self.__username, umc.baseconfig[ 'ldap/base' ] )

		self.__command_list = self.__manager.get_command_descriptions( umc.baseconfig['hostname'],
																	   self.acls )

		self.signal_new( 'response' )


	def __del__( self ):
		ud.debug( ud.ADMIN, ud.PROCESS, 'Processor: dying' )
		for process in self.__processes.values():
			del process

	def request( self, msg ):

		if msg.command == 'EXIT':
			self.handle_request_exit( msg )

		elif msg.command == 'GET':
			self.handle_request_get( msg )

		elif msg.command == 'SET':
			self.handle_request_set( msg )

		elif msg.command == 'VERSION':
			self.handle_request_version( msg )

		elif msg.command == 'COMMAND':
			self.handle_request_command( msg )

		elif msg.command == 'STATUS':
			self.handle_request_unknown( msg )

		elif msg.command == 'CANCEL':
			self.handle_request_unknown( msg )

		elif msg.command == 'CLOSE':
			self.handle_request_unknown( msg )

		else:
			self.handle_request_unknown( msg )

	def _purge_child(self, module_name):
		if self.__processes.has_key( module_name ):
			ud.debug( ud.ADMIN, ud.INFO, 'session.py: module %s is still running - purging module out of memory' % module_name)
			pid = self.__processes[ module_name ].pid()
			os.kill(pid, 9)
		return False

	def handle_request_exit( self, msg ):
		if len( msg.arguments ) < 1:
			return self.handle_request_unknown( msg )

		module_name = msg.arguments[0]
		if module_name:
			if self.__processes.has_key( module_name ):
				self.__processes[ module_name ].request( msg )
				ud.debug( ud.ADMIN, ud.INFO, 'session.py: got EXIT: asked module %s to shutdown gracefully' % module_name)
				# added timer to kill away module after 3000ms
				cb = notifier.Callback( self._purge_child, module_name )
				self.__killtimer[ module_name ] = notifier.timer_add( 3000, cb )
			else:
				ud.debug( ud.ADMIN, ud.INFO, 'session.py: got EXIT: module %s is not running' % module_name )

	def handle_request_version( self, msg ):
		res = Response( msg )
		res.status( 200 ) # Ok
		res.body[ 'version' ] = VERSION

		self.signal_emit( 'response', res )


	def handle_request_get( self, msg ):
		res = Response( msg )

		if 'modules/list' in msg.arguments:

			res.body[ 'modules' ] = self.__command_list
			res.body[ 'categories' ] = categories.get()
			ud.debug( ud.ADMIN, ud.INFO, 'session.py: modules: %s' % self.__command_list.keys() )
			ud.debug( ud.ADMIN, ud.INFO, 'session.py: categories: %s' % res.body[ 'categories' ] )
			res.status( 200 ) # Ok

		elif 'hosts/list' in msg.arguments:
			# only support for localhost
			res.body = { 'hosts': [ '%s' % umc.baseconfig[ 'hostname' ] ] }
			res.status( 200 ) # Ok

		else:
			res.status( 402 ) # invalid command arguments

		self.signal_emit( 'response', res )

	def handle_request_set( self, msg ):
		res = Response( msg )
		if len( msg.arguments ) < 2:
			return self.handle_request_unknown( msg )

		if msg.arguments[ 0 ] == 'locale':
			res.status( 200 )
			self.__locale = msg.arguments[ 1 ]
			try:
				locale.setlocale( locale.LC_MESSAGES,
								  locale.normalize( msg.arguments[ 1 ] ) )
			except locale.Error:
				# specified locale is not available
				res.status( 601 )
				ud.debug( ud.ADMIN, ud.WARN,
						 'session.py: handle_request_set: setting locale: status=601: specified locale is not available (%s)' % \
						 self.__locale )
			self.signal_emit( 'response', res )

		elif msg.arguments[ 0 ] == 'interface':
			if len( msg.arguments ) == 2 and msg.arguments[ 1 ]:
				self.__interface = msg.arguments[ 1 ]
				res.status( 200 )
			else:
				# invalid command arguments
				res.status( 402 )
			self.signal_emit( 'response', res )

		else:
			return self.handle_request_unknown( msg )

	def __is_command_known( self, msg ):
		# only one command?
		command = None
		if len( msg.arguments ) > 0:
			command = msg.arguments[ 0 ]

		module_name = self.__manager.search_command( command )
		if not module_name:
			res = Response( msg )
			res.status( 401 ) # unknown command
			res.report = status_information( 401 )
			self.signal_emit( 'response', res )
			return None

		return module_name

	def handle_request_command( self, msg ):
		module_name = self.__is_command_known( msg )
		if module_name:
			if not self.__processes.has_key( module_name ):
				if umc.baseconfig.has_key( 'umc/module/debug/level' ):
					mod_proc = ModuleProcess( module_name, self.__interface,
								  debug = umc.baseconfig[ 'umc/module/debug/level' ],
								  locale = self.__locale )
				else:
					mod_proc = ModuleProcess( module_name, self.__interface,
											  locale = self.__locale  )
				mod_proc.signal_connect( 'result', self._mod_result )
				cb = notifier.Callback( self._mod_died, msg )
				mod_proc.signal_connect( 'finished', cb )
				self.__processes[ module_name ] = mod_proc
				cb = notifier.Callback( self._mod_connect, mod_proc, msg )
				notifier.timer_add( 500, cb )
			else:
				self.__processes[ module_name ].request( msg )

	def _mod_connect( self, mod, msg ):
		ud.debug( ud.ADMIN, ud.PROCESS, 'trying to connect' )
		if not mod.connect():
			ud.debug( ud.ADMIN, ud.PROCESS, 'failed' )
			if mod._connect_retries > 20:
				ud.debug( ud.ADMIN, ud.ERROR, 'connection to module process failed')
				res = Response( msg )
				res.status( 503 ) # error connecting to module process
				res.report = status_information( 503 )
				self.signal_emit( 'response', res )
			else:
				mod._connect_retries += 1
				return True
		else:
			ud.debug( ud.ADMIN, ud.INFO, 'ok')

			# send acls
			acls = self.acls.acls
			req = Request( 'SET', args = [ 'commands/permitted' ],
								opts = { 'acls' : acls } )
			mod.request( req )

			# set credentials
			req = Request( 'SET', args = [ 'credentials' ],
						   opts = { 'username' : self.__username, 'password' : self.__password } )
			mod.request( req )

			# set locale
			if self.__locale:
				req = Request( 'SET', args = [ 'locale' ],
								opts = { 'locale' : self.__locale } )
				mod.request( req )

			mod.request( msg )

		return False

	def _mod_result( self, msg ):
		self.signal_emit( 'response', msg )

	def _mod_died( self, pid, status, name, msg ):
		if status:
			ud.debug( ud.ADMIN, ud.WARN, 'module process died (%d): %s' % ( pid, str( status ) ) )
			res = Response( msg )
			res.status( 502 ) # module process died unexpectedly
		else:
			ud.debug( ud.ADMIN, ud.INFO, 'module process died: everything fine' )
		# if killtimer has been set then remove it
		if self.__killtimer.has_key( name ):
			ud.debug( ud.ADMIN, ud.INFO, 'module process died: stopping killtimer of "%s"' % name )
			notifier.timer_remove( self.__killtimer[ name ] )
			del self.__killtimer[ name ]
		del self.__processes[ name ]

	def handle_request_status( self, msg ):

		self.handle_request_unknown( msg )


	def handle_request_cancel( self, msg ):

		self.handle_request_unknown( msg )


	def handle_request_close( self, msg ):

		self.handle_request_unknown( msg )


	def handle_request_unknown( self, msg ):
		res = Response( msg )
		res.status( 401 ) # unknown command
		res.report = status_information( 401 )

		self.signal_emit( 'response', res )

if __name__ == '__main__':
	processor = Processor( 'Administrator', 'univention' )
	processor.handle_request_get ( None )
