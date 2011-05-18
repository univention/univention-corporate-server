#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  session handling
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

import ldap
import locale
import os
import string
import sys

import notifier
import notifier.signals as signals
import notifier.popen as popen

from OpenSSL import *

import univention.uldap

from .message import *
from .client import *
from .version import *
from .definitions import *

from ..resources import *
from ..verify import SyntaxVerificationError
from ..auth import AuthHandler
from ..acl import ConsoleACLs
from ..locales import Translation, LocaleNotFound
from ..log import *

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
		self.running = False

	def __del__( self ):
		CORE.process( 'State: dying' )
		del self.processor

	def _authenticated( self, success ):
		self.signal_emit( 'authenticated', success, self )

	def authenticate( self, username, password ):
		self.__auth.authenticate( username, password )

	def credentials( self ):
		return self.__auth.credentials()


class ModuleProcess( Client ):
	COMMAND = '/usr/sbin/univention-management-console-module'

	def __init__( self, module, debug = '0', locale = None ):
		socket = '/var/run/univention-management-console/%u-%lu.socket' % ( os.getpid(), long( time.time() * 1000 ) )
		# determine locale settings
		args = [ ModuleProcess.COMMAND, '-m', module, '-s', socket, '-d', debug ]
		if locale:
			args.extend( ( '-l', '%s' % locale ) )
			self.__locale = locale
		else:
			self.__locale = None
		Client.__init__( self, unix = socket, ssl = False, auth = False )
		self.signal_connect( 'response', self._response )
		CORE.process( 'running: %s' % args )
		self.__process = popen.RunIt( args, stdout = False )
		self.__process.signal_connect( 'finished', self._died )
		self.__pid = self.__process.start()
		self._connect_retries = 1
		self.signal_new( 'result' )
		self.signal_new( 'finished' )
		self.name = module
		self.running = False
		self._queued_requests = []

	def __del__( self ):
		CORE.process( 'ModuleProcess: dying' )
		self.disconnect()
		self.__process.stop()
		CORE.process( 'ModuleProcess: child stopped' )

	def _died( self, pid, status ):
		CORE.process( 'ModuleProcess: child died' )
		self.signal_emit( 'finished', pid, status, self.name )

	def _response( self, msg ):
		if msg.command == 'SET' and 'commands/permitted' in msg.arguments:
			return

		self.signal_emit( 'result', msg )

	def pid( self ):
		return self.__pid

class Processor( signals.Provider, Translation ):
	'''Implements a proxy and command handler. It handles all internal
	UMCP commands and passes the commands for a module to the
	subprocess.'''

	def __init__( self, username, password ):
		self.__username = username
		self.__password = password
		signals.Provider.__init__( self )
		Translation.__init__( self, 'univention-management-console' )

		# stores the module processes [ modulename ] = <>
		self.__processes = {}
		self.__locale = None
		self.__sessionid = None

		self.__killtimer = {}

		lo = ldap.open( umc.configRegistry[ 'ldap/server/name' ] )

		try:
			userdn = lo.search_s( umc.configRegistry[ 'ldap/base' ], ldap.SCOPE_SUBTREE,
								  '(&(objectClass=person)(uid=%s))' % self.__username )[ 0 ][ 0 ]

			self.lo = univention.uldap.access( host = umc.configRegistry[ 'ldap/server/name' ],
											   base = umc.configRegistry[ 'ldap/base' ], binddn = userdn,
											   bindpw = self.__password, start_tls = 2 )
		except:
			self.lo = None

		# read the ACLs
		self.acls = ConsoleACLs( self.lo, self.__username, umc.configRegistry[ 'ldap/base' ] )
		self.__command_list = moduleManager.permitted_commands( umc.configRegistry[ 'hostname' ], self.acls )

		self.signal_new( 'response' )


	def __del__( self ):
		CORE.process( 'Processor: dying' )
		for process in self.__processes.values():
			del process

	def get_module_name( self, command ):
		return moduleManager.module_providing( self.__comand_list, command )

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
		elif msg.command in ( 'STATUS', 'CANCEL', 'CLOSE' ):
			self.handle_request_unknown( msg )
		else:
			self.handle_request_unknown( msg )

	def _purge_child(self, module_name):
		if module_name in self.__processes:
			CORE.process( 'module %s is still running - purging module out of memory' % module_name)
			pid = self.__processes[ module_name ].pid()
			os.kill(pid, 9)
		return False

	def handle_request_exit( self, msg ):
		if len( msg.arguments ) < 1:
			return self.handle_request_unknown( msg )

		module_name = msg.arguments[ 0 ]
		if module_name:
			if module_name in self.__processes:
				self.__processes[ module_name ].request( msg )
				CORE.info( 'session.py: got EXIT: asked module %s to shutdown gracefully' % module_name)
				# added timer to kill away module after 3000ms
				cb = notifier.Callback( self._purge_child, module_name )
				self.__killtimer[ module_name ] = notifier.timer_add( 3000, cb )
			else:
				CORE.info( 'session.py: got EXIT: module %s is not running' % module_name )

	def handle_request_version( self, msg ):
		res = Response( msg )
		res.status = 200 # Ok
		res.body[ 'version' ] = VERSION

		self.signal_emit( 'response', res )


	def handle_request_get( self, msg ):
		res = Response( msg )

		if 'modules/list' in msg.arguments:
			modules = {}
			for id, module in self.__command_list.items():
				modules[ id ] = { 'name' : module.name, 'description' : module.description, 'icon' : module.icon, 'categories' : module.categories }
			res.body[ 'modules' ] = modules
			res.body[ 'categories' ] = categoryManager.all()
			CORE.info( 'session.py: modules: %s' % str( self.__command_list ) )
			CORE.info( 'session.py: categories: %s' % str( res.body[ 'categories' ] ) )
			res.status = 200 # Ok

		elif 'categories/list' in msg.arguments:
			res.body[ 'categories' ] = categoryManager.all()
			res.status = 200 # Ok
		elif 'syntax/verification' in msg.arguments:
			syntax_name = msg.options.get( 'syntax' )
			value = msg.options.get( 'value' )
			if not value or not syntax_name:
				res.status = 600 # failed to process command
			else:
				res.status = 200
				try:
					syntaxManager.verify( syntax_name, value )
					res.result = True
				except SyntaxVerificationError, e:
					res.result = False
					res.message = str( e )
		elif 'hosts/list' in msg.arguments:
			# only support for localhost
			res.body = { 'hosts': [ '%s' % umc.configRegistry[ 'hostname' ] ] }
			res.status = 200 # Ok

		else:
			res.status = 402 # invalid command arguments

		self.signal_emit( 'response', res )

	def handle_request_set( self, msg ):
		res = Response( msg )
		if len( msg.arguments ) < 2:
			return self.handle_request_unknown( msg )

		if msg.arguments[ 0 ] == 'locale':
			res.status = 200
			self.__locale = msg.arguments[ 1 ]
			try:
				self.set_language( msg.arguments[ 1 ] )
			except LocaleNotFound, e:
				# specified locale is not available
				res.status = 601
				CORE.warn( 'handle_request_set: setting locale: status=601: specified locale is not available (%s)' % self.__locale )
			self.signal_emit( 'response', res )

		elif msg.arguments[ 0 ] == 'sessionid':
			res.status = 200
			self.__sessionid = msg.arguments[ 1 ]
			self.signal_emit( 'response', res )

		else:
			return self.handle_request_unknown( msg )

	def __is_command_known( self, msg ):
		# only one command?
		command = None
		if len( msg.arguments ) > 0:
			command = msg.arguments[ 0 ]

		module_name = moduleManager.module_providing( self.__command_list, command )
		if not module_name:
			res = Response( msg )
			res.status = 404 # unknown command
			res.message = status_information( 404 )
			self.signal_emit( 'response', res )
			return None

		return module_name

	def handle_request_command( self, msg ):
		module_name = self.__is_command_known( msg )
		if module_name and msg.arguments:
			if not self.acls.is_command_allowed( msg.arguments[ 0 ], options = msg.options ):
				response = Response( msg )
				response.status = 405 # not allowed
				response.message = status_information( 405 )
				self.signal_emit( 'response', response )
				return
			if not module_name in self.__processes:
				CORE.info( 'creating new module and passing new request to module %s: %s' % (module_name, str(msg._id)) )
				mod_proc = ModuleProcess( module_name, debug = umc.configRegistry.get( 'umc/module/debug/level', '0' ), locale = self.__locale )
				mod_proc.signal_connect( 'result', self._mod_result )
				cb = notifier.Callback( self._socket_died, module_name, msg )
				mod_proc.signal_connect( 'closed', cb )
				cb = notifier.Callback( self._mod_died, msg )
				mod_proc.signal_connect( 'finished', cb )
				self.__processes[ module_name ] = mod_proc
				cb = notifier.Callback( self._mod_connect, mod_proc, msg )
				notifier.timer_add( 50, cb )
			else:
				CORE.info( 'passing new request to running module %s' % module_name )
				proc = self.__processes[ module_name ]
				if proc.running:
					proc.request( msg )
				else:
					proc._queued_requests.append( msg )

	def _mod_connect( self, mod, msg ):
		if not mod.connect():
			CORE.process( 'No connection to module process yet' )
			if mod._connect_retries > 200:
				CORE.error( 'Connection to module process failed' )
				res = Response( msg )
				res.status = 503 # error connecting to module process
				res.message = status_information( 503 )
				self.signal_emit( 'response', res )
			else:
				mod._connect_retries += 1
				return True
		else:
			CORE.info( 'Connected to new module process')
			mod.running = True

			# send acls
			req = Request( 'SET', arguments = [ 'commands/permitted' ], options = { 'acls' : self.acls.json(), 'commands' : self.__command_list[ mod.name ].json() } )
			mod.request( req )

			# set credentials
			req = Request( 'SET', arguments = [ 'credentials' ], options = { 'username' : self.__username, 'password' : self.__password } )
			mod.request( req )

			# set locale
			if self.__locale:
				req = Request( 'SET', arguments = [ 'locale' ], options = { 'locale' : self.__locale } )
				mod.request( req )

			# set sessionid
			if self.__sessionid:
				req = Request( 'SET', arguments = [ 'sessionid' ], options = { 'sessionid' : self.__sessionid } )
				mod.request( req )

			mod.request( msg )
			# send queued request that were received during start procedure
			for req in mod._queued_requests:
				mod.request( req )
			mod._queued_requests = []

		return False

	def _mod_result( self, msg ):
		self.signal_emit( 'response', msg )

	def _socket_died( self, module_name, msg):
		CORE.warn( 'socket died (module=%s)' % module_name )
		res = Response( msg )
		res.status = 502 # module process died unexpectedly
		self._mod_died(0, 1, module_name, msg)

	def _mod_died( self, pid, status, name, msg ):
		if status:
			CORE.warn( 'Module process died (%d): %s' % ( pid, str( status ) ) )
			res = Response( msg )
			res.status = 502 # module process died unexpectedly
		else:
			CORE.info( 'module process died: everything fine' )
		if name in self.__processes:
			CORE.warn( 'module process died: cleaning up requests')
			self.__processes[ name ].invalidate_all_requests()
		# if killtimer has been set then remove it
		if name in self.__killtimer:
			CORE.info( 'module process died: stopping killtimer of "%s"' % name )
			notifier.timer_remove( self.__killtimer[ name ] )
			del self.__killtimer[ name ]
		if name in self.__processes:
			del self.__processes[ name ]

	def handle_request_status( self, msg ):

		self.handle_request_unknown( msg )


	def handle_request_cancel( self, msg ):

		self.handle_request_unknown( msg )


	def handle_request_close( self, msg ):

		self.handle_request_unknown( msg )


	def handle_request_unknown( self, msg ):
		res = Response( msg )
		res.status = 404 # unknown command
		res.message = status_information( 404 )

		self.signal_emit( 'response', res )

if __name__ == '__main__':
	processor = Processor( 'Administrator', 'univention' )
	processor.handle_request_get ( None )
