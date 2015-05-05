#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Author: Andreas Büsching <crunchy@bitkipper.net>
#
# QT notifier wrapper
#
# Copyright (C) 2004, 2005, 2006, 2007
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

"""notifier wrapper for QT 4"""

import PyQt4.Qt as qt
import socket

import dispatch
import log

_qt_socketIDs = {} # map of sockets/condition/methods -> qt.QSocketNotifier

IO_READ = qt.QSocketNotifier.Read
IO_WRITE = qt.QSocketNotifier.Write
IO_EXCEPT = qt.QSocketNotifier.Exception

_qt_socketIDs[ IO_READ ] = {}
_qt_socketIDs[ IO_WRITE ] = {}
_qt_socketIDs[ IO_EXCEPT ] = {}

__min_timer = None
__exit = None

class NotifierErrorQtApplicationUnset(Exception):
	pass

def _get_fd( obj ):
	"""Returns a file descriptor. obj can be a file descriptor or an
	object of type socket.socket, file or socket._socketobject"""
	if isinstance( obj, int ):
		return obj
	if hasattr(obj, 'fileno'):
		return obj.fileno()

	return -1

class Socket( qt.QSocketNotifier ):
	def __init__( self, socket, method, condition ):
		qt.QSocketNotifier.__init__( self, _get_fd( socket ), condition )
		self.method = method
		self.socket = socket
		self.activated.connect( self.notified )

	@qt.pyqtSlot( int )
	def notified( self, socket ):
		log.warn( 'QT: socket: %d event on socket %s' % ( self.type(), str( socket ) ) )
		if not self.method( self.socket ):
			self.setEnabled( 0 )
			socket_remove( self.socket, self.type() )

class Timer( qt.QTimer ):
	def __init__( self, ms, method ):
		if qt.QCoreApplication.instance() is None:
			# create a new Qt Application instance before calling timer_add, e.g.
			# app = qt.QCoreApplication([])
			raise NotifierErrorQtApplicationUnset()
		qt.QTimer.__init__(self, qt.QCoreApplication.instance())
		self.method = method
		self.timeout.connect( self.slotTick )
		self.start( ms )

	def slotTick( self ):
		try:
			if not self.method():
				self.stop()
				del self
		except BaseException, e:
			log.warn( 'TIMER FAILED: %s' % str( e ) )

def socket_add( socket, method, condition = IO_READ ):
	"""The first argument specifies a socket, the second argument has to be a
	function that is called whenever there is data ready in the socket."""
	global _qt_socketIDs
	if _get_fd( socket ) in map( lambda s: _get_fd( s ), _qt_socketIDs[ condition ].keys() ):
		log.warn( 'Socket %d already registered for condition %d' % ( _get_fd( socket ), condition ) )
		return
	_qt_socketIDs[ condition ][ socket ] = Socket( socket, method, condition )

def socket_remove( socket, condition = IO_READ ):
	"""Removes the given socket from scheduler."""
	global _qt_socketIDs
	if socket in _qt_socketIDs[ condition ]:
		_qt_socketIDs[ condition ][ socket ].setEnabled( 0 )
		del _qt_socketIDs[ condition ][ socket ]

def timer_add( interval, method ):
	"""The first argument specifies an interval in milliseconds, the
	second argument a function. This function is called after
	interval milliseconds. If it returns True it's called again after
	interval milliseconds, otherwise it is removed from the
	scheduler."""
	return Timer( interval, method )

def timer_remove( id ):
	"""Removes _all_ function calls to the method given as argument from the
	scheduler."""
	if isinstance( id, Timer ):
		id.stop()
		del id

def dispatcher_add( method, min_timeout = True ):
	global __min_timer
	__min_timer = dispatch.dispatcher_add( method, min_timeout )

def dispatcher_remove( method ):
	global __min_timer
	__min_timer = dispatch.dispatcher_remove( method )

def loop():
	"""Execute main loop forever."""
	global __exit

	while __exit is None:
		step()

	return __exit

def step( sleep = True, external = True ):
	global __min_timer

	if __min_timer and sleep:
		time = qt.QTime()
		time.start()
		qt.QCoreApplication.processEvents( qt.QEventLoop.AllEvents | qt.QEventLoop.WaitForMoreEvents,
									   __min_timer )
		if time.elapsed() < __min_timer:
			qt.QThread.usleep( __min_timer - time.elapsed() )
	else:
		qt.QCoreApplication.processEvents( qt.QEventLoop.AllEvents | qt.QEventLoop.WaitForMoreEvents )

	if external:
		dispatch.dispatcher_run()

def _exit( dummy, code = 0 ):
	global __exit
	__exit = code

qt.QCoreApplication.exit = _exit
qt.QCoreApplication.quit = _exit
