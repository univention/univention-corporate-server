#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Author: Andreas Büsching <crunchy@bitkipper.net>
#
# Copyright (C) 2004, 2005, 2006, 2007, 2008, 2009, 2010
#	Andreas Büsching <crunchy@bitkipper.net>
#
# This library is free software; you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License version
# 2.1 as published by the Free Software Foundation.
#
# This library is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301 USA

"""child process control using notifier."""

__all__ = [ 'Process', 'RunIt', 'Shell' ]

# python imports
import os
import fcntl
import glob
import re
import shlex
import tempfile
import time
import types
import subprocess

# notifier imports
import notifier
import signals
import log

_processes = []

class Process( signals.Provider ):
	"""
	Base class for starting child processes and monitoring standard
	output and error.
	"""
	def __init__( self, cmd, stdout = True, stderr = True, shell = False ):
		""" Init the child process 'cmd'. This can either be a string or a list
		of arguments (similar to popen2). stdout and stderr of the child
		process can be handled by connecting to the signals 'stdout'
		and/or 'stderr'. The signal functions have one argument that is
		of type list and contains all new lines. By setting one of the
		boolean arguments 'stdout' and 'stderr' to False the monitoring
		of these files can be deactivated.


		Signals:
		'stderr' ( pid, line )
			emitted when the IO_Handler reported another line of input
			(from stdout).
			pid			: PID of the process that produced the output
			line		: line of output
		'stdout' ( pid, line )
			emitted when the IO_Handler reported another line of input
			(from stderr).
			pid			: PID of the process that produced the output
			line		: line of output
		"""
		signals.Provider.__init__( self )
		if stderr: self.signal_new( 'stderr' );
		if stdout: self.signal_new( 'stdout' );
		self.signal_new( 'killed' );

		if not shell and not isinstance( cmd, ( list, tuple ) ):
			self._cmd = shlex.split( str( cmd ) ) # shlex.split can not handle Unicode strings
		else:
			self._cmd = cmd

		self._shell = shell
		if not shell and self._cmd:
			self._name = self._cmd[ 0 ].split( '/' )[ -1 ]
		else:
			self._name = '<unknown>'
		self.stopping = False
		self.pid = None
		self.child = None

		self.__dead = True
		self.__kill_timer = None

		global _processes
		if not _processes:
			notifier.dispatcher_add( _watcher )
		_processes.append( self )

	def _read_stdout( self, line ):
		"""emit signal 'stdout', announcing that there is another line
		of output"""
		self.signal_emit( 'stdout', self.pid, line )

	def _read_stderr( self, line ):
		"""emit signal 'stdout', announcing that there is another line
		of output"""
		self.signal_emit( 'stderr', self.pid, line )

	def start( self, args = None ):
		"""
		Starts the process.	 If args is not None, it can be either a list or
		string, as with the constructor, and is appended to the command line
		specified in the constructor.
		"""
		if not self.__dead:
			raise SystemError, "process is already running."
		if self.stopping:
			raise SystemError, "process is currently dying."

		if not args:
			cmd = self._cmd
		else:
			if not self._shell:
				cmd = self._cmd + shlex.split( args )
			else:
				cmd = '%s %s' % ( self._cmd, args )


		self.__kill_timer = None
		self.__dead = False
		self.binary = cmd[ 0 ]

		self.stdout = self.stderr = None
		if not self.signal_exists( 'stdout' ) and not self.signal_exists( 'stderr' ):
			self.pid =  subprocess.Popen( cmd, shell = self._shell ).pid
		else:
			if self.signal_exists( 'stdout' ):
				self.stdout = subprocess.PIPE
			if self.signal_exists( 'stderr' ):
				self.stderr = subprocess.PIPE

			# line buffered, no shell
			self.child = subprocess.Popen( cmd, bufsize = 1, shell = self._shell,
										   stdout = self.stdout, stderr = self.stderr )
			self.pid = self.child.pid

			if self.stdout:
				# IO_Handler for stdout
				self.stdout = IO_Handler( 'stdout', self.child.stdout,
										  self._read_stdout, self._name )
				self.stdout.signal_connect( 'closed', self._closed )

			if self.stderr:
				# IO_Handler for stderr
				self.stderr = IO_Handler( 'stderr', self.child.stderr,
										  self._read_stderr, self._name )
				self.stderr.signal_connect( 'closed', self._closed )

		log.info( 'running %s (pid=%s)' % ( self.binary, self.pid ) )

		return self.pid

	def dead( self, pid, status ):
		self.__dead = True
		# check io handlers if there is pending output
		for output in ( self.stdout, self.stderr ):
			if output:
				output._handle_input(flush_partial_lines=True)
		self.signal_emit( 'killed', pid, status )

	def _closed( self, name ):
		if name == 'stderr':
			self.stderr = None
		elif name == 'stdout':
			self.stdout = None

		if not self.stdout and not self.stderr:
			try:
				pid, status = os.waitpid( self.pid, os.WNOHANG )
				if pid:
					self.dead( pid, status )
			except OSError: # already dead and buried
				pass

	def write( self, line ):
		"""
		Pass a string to the process
		"""
		try:
			self.child.communicate( line )
		except ( IOError, ValueError ):
			pass

	def is_alive( self ):
		"""
		Return True if the process is still running
		"""
		return not self.__dead

	def stop( self ):
		"""
		Stop the child. Tries to kill the process with signal 15 and after that
		kill -9 will be used to kill the app.
		"""
		if self.stopping:
			return

		self.stopping = True

		if self.is_alive() and not self.__kill_timer:
			cb = notifier.Callback( self.__kill, 15 )
			self.__kill_timer = notifier.timer_add( 0, cb )

	def __kill( self, signal ):
		"""
		Internal kill helper function
		"""
		if not self.is_alive():
			self.__dead = True
			self.stopping = False
			return False
		# child needs some assistance with dying ...
		try:
			os.kill( self.pid, signal )
		except OSError:
			pass

		if signal == 15:
			cb = notifier.Callback( self.__kill, 9 )
		else:
			cb = notifier.Callback( self.__killall, 15 )

		self.__kill_timer = notifier.timer_add( 3000, cb )
		return False

	def __killall( self, signal ):
		"""
		Internal killall helper function
		"""
		if not self.is_alive():
			self.__dead = True
			self.stopping = False
			return False
		# child needs some assistance with dying ...
		try:
			# kill all applications with the string <appname> in their
			# commandline. This implementation uses the /proc filesystem,
			# it is Linux-dependent.
			unify_name = re.compile( '[^A-Za-z0-9]' ).sub
			appname = unify_name( '', self.binary )

			cmdline_filenames = glob.glob( '/proc/[0-9]*/cmdline' )

			for cmdline_filename in cmdline_filenames:
				try:
					fd = open( cmdline_filename )
					cmdline = fd.read()
					fd.close()
				except IOError:
					continue
				if unify_name( '', cmdline ).find( appname ) != -1:
					# Found one, kill it
					pid = int( cmdline_filename.split( '/' )[ 2 ] )
					try:
						os.kill( pid, signal )
					except:
						pass
		except OSError:
			pass

		log.info( 'kill -%d %s' % ( signal, self.binary ) )
		if signal == 15:
			cb = notifier.Callback( self.__killall, 9 )
			self.__kill_timer = notifier.timer_add( 2000, cb )
		else:
			log.critical( 'PANIC %s' % self.binary )

		return False

def _watcher():
	global _processes
	finished = []

	for proc in _processes:
		try:
			if not proc.pid:
				continue
			pid, status = os.waitpid( proc.pid, os.WNOHANG )
			if pid:
				proc.dead( pid, status )
				finished.append( proc )
		except OSError: # already dead and buried
			finished.append( proc )

	for i in finished:
		_processes.remove( i )

	return ( len( _processes ) > 0 )

class IO_Handler( signals.Provider ):
	"""
	Reading data from socket (stdout or stderr)

	Signals:
	'closed' ( name )
		emitted when the file was closed.
		name			: name of the IO_Handler
	"""
	def __init__( self, name, fp, callback, logger = None ):
		signals.Provider.__init__( self )

		self.name = name
		self.fp = fp
		fcntl.fcntl( self.fp.fileno(), fcntl.F_SETFL, os.O_NONBLOCK )
		self.callback = callback
		self.saved = ''
		notifier.socket_add( fp, self._handle_input )
		self.signal_new( 'closed' )

	def close( self ):
		"""
		Close the IO to the child.
		"""
		notifier.socket_remove( self.fp )
		self.fp.close()
		self.signal_emit( 'closed', self.name )

	def _handle_input( self, socket=None, flush_partial_lines=False ):
		"""
		Handle data input from socket.
		"""
		try:
			self.fp.flush()
			data = self.fp.read( 65535 )
		except IOError, (errno, msg):
			if errno == 11:
				# Resource temporarily unavailable; if we try to read on a
				# non-blocking descriptor we'll get this message.
				return True
			data = None

		if not data:
			if self.saved:
				# Although socket has no data anymore, we still have data left
				# over in the buffer.
				self.flush_buffer()
				return True
			self.close()
			return False

		data  = data.replace( '\r', '\n' )
		partial_line = data[ -1 ] != '\n'
		lines = data.split( '\n' )

		# split creates an empty line of string ends with line break
		if not lines[ -1 ]:
			del lines[ -1 ]
		# prepend saved data to first line
		if self.saved:
			lines[ 0 ] = self.saved + lines[ 0 ]
			self.saved = ''
		# Only one partial line?
		if partial_line and not flush_partial_lines:
			self.saved = lines[ -1 ]
			del lines[ -1 ]

		# send lines
		self.callback( lines )

		return True

	def flush_buffer( self ):
		if self.saved:
			self.callback( self.saved.split( '\n' ) )
			self.saved = ''

class RunIt( Process ):
	"""Is a more simple child process handler based on Process that
	caches the output and provides it to the caller with the signal
	'finished'.

	Signals:
	'finished' ( pid, status[, stdout[, stderr ] ] )
		emitted when the child process is dead.
		pid				: process ID
		status			: exit code of the child process
		stdout, stderr	: are only provided when stdout and/or stderr is
						  monitored
		"""
	def __init__( self, command, stdout = True, stderr = False, shell = False ):
		Process.__init__( self, command, stdout = stdout, stderr = stderr, shell = shell )
		if stdout:
			self.__stdout = []
			cb = notifier.Callback( self._output, self.__stdout )
			self.signal_connect( 'stdout', cb )
		else:
			self.__stdout = None
		if stderr:
			self.__stderr = []
			cb = notifier.Callback( self._output, self.__stderr )
			self.signal_connect( 'stderr', cb )
		else:
			self.__stderr = None
		self.signal_connect( 'killed', self._finished )
		self.signal_new( 'finished' )

	def _output( self, pid, line, buffer ):
		if isinstance( line, list ):
			buffer.extend( line )
		else:
			buffer.append( line )

	def _finished( self, pid, status ):
		exit_code = os.WEXITSTATUS( status )
		if self.__stdout != None:
			if self.__stderr == None:
				self.signal_emit( 'finished', pid, exit_code, self.__stdout )
			else:
				self.signal_emit( 'finished', pid, exit_code ,self.__stdout, self.__stderr )
		elif self.__stderr != None:
			self.signal_emit( 'finished', pid, exit_code, self.__stderr )
		else:
			self.signal_emit( 'finished', pid, exit_code )

class Shell( RunIt ):
	'''A simple interface for running shell commands as child processes'''
	def __init__( self, command, stdout = True, stderr = False ):
		RunIt.__init__( self, command, stdout = stdout, stderr = stderr, shell = True )

class CountDown( object ):
	'''This class provides a simple method to measure the expiration of
	an amount of time'''
	def __init__( self, timeout ):
		self.start = time.time() * 1000
		self.timeout = timeout

	def __call__( self ):
		now = time.time() * 1000
		return not self.timeout or ( now - self.start < self.timeout )

class Child( object ):
	'''Describes a child process and is used for return values of the
	run method.'''
	def __init__( self, stdout = None, stderr = None ):
		self.pid = None
		self.exitcode = None
		self.stdout = stdout
		self.stderr = stderr

def run( command, timeout = 0, stdout = True, stderr = True, shell = True ):
	'''Runs a child process with the <command> and waits <timeout>
	seconds for its termination. If <stdout> is True the standard output
	is written to a temporary file. The same can be done for the standard
	error output with the argument <stderr>. If <shell> is True the
	command is passed to a shell. The return value is a Child
	object. The member variable <pid> is set if the process is still
	running after <timeout> seconds otherwise <exitcode> is set.'''
	# a dispatcher function required to activate the minimal timeout
	def fake_dispatcher(): return True
	notifier.dispatcher_add( fake_dispatcher )

	countdown = CountDown( timeout )
	out = err = None
	if stdout:
		out = tempfile.NamedTemporaryFile()
	if stderr:
		err = tempfile.NamedTemporaryFile()

	if isinstance( command, basestring ):
		command = shlex.split( command )
	child = subprocess.Popen( command, shell = shell, stdout = out, stderr = err )

	while countdown():
		exitcode = child.poll()
		if exitcode != None:
			break
		notifier.step()

	# remove dispatcher function
	notifier.dispatcher_remove( fake_dispatcher )

	# prepare return code
	ret = Child( stdout = out, stderr = err )
	if child.returncode == None:
		ret.pid = child.pid
	else:
		# move to beginning of files
		if out:
			out.seek( 0 )
		if err:
			err.seek( 0 )
		ret.exitcode = child.returncode

	return ret

def kill( pid, signal = 15, timeout = 0 ):
	'''kills the process specified by pid that may be a process id or a
	Child object. The process is killed with the provided signal (by
	default 15). If the process is not dead after <timeout> seconds the
	function exist anyway'''
	# a dispatcher function required to activate the minimal timeout
	def fake_dispatcher(): return True
	notifier.dispatcher_add( fake_dispatcher )

	if isinstance( pid, Child ):
		if pid.pid:
			pid = pid.pid
		else:
			return pid.exitcode

	os.kill( pid, signal )
	countdown = CountDown( timeout )
	while countdown():
		dead_pid, sts = os.waitpid( pid, os.WNOHANG )
		if dead_pid == pid:
			break
		notifier.step()
	else:
		# remove dispatcher function
		notifier.dispatcher_remove( fake_dispatcher )
		return None

	# remove dispatcher function
	notifier.dispatcher_remove( fake_dispatcher )

	if os.WIFSIGNALED( sts ):
		return -os.WTERMSIG( sts )

	return os.WEXITSTATUS( sts )
