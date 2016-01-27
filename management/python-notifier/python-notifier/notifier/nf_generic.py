#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Author: Andreas Büsching <crunchy@bitkipper.net>
#
# generic notifier implementation
#
# Copyright (C) 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012
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

"""Simple mainloop that watches sockets and timers."""

# python core packages
from time import time, sleep as time_sleep

import select
import socket

# internal packages
import log
import dispatch

IO_READ = select.POLLIN
IO_WRITE = select.POLLOUT
IO_EXCEPT = select.POLLERR
IO_ALL = IO_READ | IO_WRITE | IO_EXCEPT

( INTERVAL, TIMESTAMP, CALLBACK ) = range( 3 )

__poll = select.poll()
__sock_objects = {}
__sockets = {}
__sockets[ IO_READ ] = {}
__sockets[ IO_WRITE ] = {}
__sockets[ IO_EXCEPT ] = {}
__timers = {}
__timer_id = 0
__min_timer = None
__in_step = False
__step_depth = 0
__step_depth_max = 0

_options = {
	'recursive_depth' : 10,
	'catch_select_errors' : True,
}

class NotifierException( Exception ):
	pass

def _get_fd( obj ):
	"""Returns a file descriptor. obj can be a file descriptor or an
	object of type socket.socket, file or socket._socketobject"""
	if isinstance( obj, int ):
		return obj
	if hasattr(obj, 'fileno'):
		return obj.fileno()

	return -1

def socket_add( id, method, condition = IO_READ ):
	"""The first argument specifies a socket, the second argument has to
	be a function that is invoked whenever there is data ready on the
	socket. The socket/file object is passed to the callback method."""
	global __sockets, __sock_objects, __poll

	# ensure that already registered condition do not get lost
	conditions = condition
	for cond in ( IO_READ, IO_WRITE, IO_EXCEPT ):
		if id in __sockets[ cond ]:
			conditions |= cond

	fd = _get_fd( id )
	if fd >= 0:
		__sock_objects[ fd ] = id
		__sockets[ condition ][ fd ] = method
		__poll.register( fd, conditions )
	else:
		raise AttributeError( 'could not get file description: %s' % id )

def socket_remove( id, condition = IO_READ ):
	"""Removes the given socket from scheduler. If no condition is
	specified the default is IO_READ."""
	global __sockets, __poll, __sock_objects

	if condition & IO_ALL == IO_ALL:
		for c in ( IO_READ, IO_WRITE, IO_EXCEPT ):
			socket_remove( id, c )
		return

	try:
		fd = _get_fd( id )
		valid = True
	except:
		fd = None
		valid = False
		# file descriptor already closed
		for cond in ( IO_READ, IO_WRITE, IO_EXCEPT ):
			for descriptor, item in __sock_objects.items():
				if item == id:
					fd = descriptor
					break
			if fd: break

	if valid:
		# a valid file descriptor may still be registered for other conditions
		remain = 0
		for cond in ( IO_READ, IO_WRITE, IO_EXCEPT ):
			if fd in __sockets[ cond ] and condition != cond:
				remain |= cond

		if remain:
			__poll.register( id, remain )
			return
	# if the file descriptor is invalid (e.g. connection closed) or
	# there are no remaining conditions it has to be removed completely
	if fd in __sockets[ condition ]:
		del __sockets[ condition ][ fd ]
	if fd in __sock_objects:
		__poll.unregister( fd )
		del __sock_objects[ fd ]

def timer_add( interval, method ):
	"""The first argument specifies an interval in milliseconds, the
	second argument is a function that is called after interval
	seconds. If it returns true it is called again after interval
	seconds, otherwise it is removed from the scheduler. The third
	(optional) argument is passwd to the invoked function.

	The return value is an unique identifier that can be used to remove
	this timer"""
	global __timer_id

	try:
		__timer_id += 1
	except OverflowError:
		__timer_id = 0

	__timers[ __timer_id ] = \
	[ interval, int( time() * 1000 ) + interval, method ]

	return __timer_id

def timer_remove( id ):
	"""Removes the timer identified by the unique ID from the main loop."""
	if id in __timers:
		del __timers[ id ]

def dispatcher_add( method, min_timeout = True ):
	"""Adds a dispatcher function. These methods are invoked by the
	mainloop as the last action of a step."""
	global __min_timer
	__min_timer = dispatch.dispatcher_add( method, min_timeout )

def dispatcher_remove( method ):
	"""Removes a registered dispatcher function"""
	global __min_timer
	__min_timer = dispatch.dispatcher_remove( method )

def step( sleep = True, external = True ):
	"""Do one step forward in the main loop. First all timers are
	checked for expiration and if necessary the associated callback
	function is called. After that the timer list is searched for the
	next timer that will expire. This will define the maximum timeout
	for the following poll statement evaluating the registered
	sockets. Returning from the pool statement the callback functions
	from the sockets reported by the poll system call are invoked. As a
	final task in a notifier step all registered external dispatcher
	functions are invoked."""

	global __in_step, __step_depth, __step_depth_max, __min_timer, _options

	__in_step = True
	__step_depth += 1

	try:
		if __step_depth > __step_depth_max:
			log.exception( 'maximum recursion depth reached' )
			raise NotifierException( 'error: maximum recursion depth reached' )

		# get minInterval for max timeout
		timeout = None
		if not sleep:
			timeout = 0
		else:
			now = int( time() * 1000 )
			for interval, timestamp, callback in __timers.values():
				if not timestamp:
					# timer is blocked (recursion), ignore it
					continue
				nextCall = timestamp - now
				if timeout is None or nextCall < timeout:
					if nextCall > 0:
						timeout = nextCall
					else:
						timeout = 0
						break
			if __min_timer and ( __min_timer < timeout or timeout is None ):
				timeout = __min_timer

		# wait for event
		fds = []
		if __sockets[ IO_READ ] or __sockets[ IO_WRITE ] or __sockets[ IO_EXCEPT ]:
			try:
				fds = __poll.poll( timeout )
			except select.error, e:
				log.error( 'error: poll system call interrupted: %s' % str( e ) )
				if not _options[ 'catch_select_errors' ]:
					raise
		elif timeout:
			time_sleep( timeout / 1000.0 )
		elif timeout is None: # if there are no timers and no sockets, do not burn the CPU
			time_sleep( dispatch.MIN_TIMER / 1000.0 )

		# handle timers
		for i, timer in __timers.items():
			timestamp = timer[ TIMESTAMP ]
			if not timestamp or i not in __timers:
				# timer was unregistered by previous timer, or would
				# recurse, ignore this timer
				continue
			now = int( time() * 1000 )
			if timestamp <= now:
				# Update timestamp on timer before calling the callback
				# to prevent infinite recursion in case the callback
				# calls step().
				timer[ TIMESTAMP ] = 0
				if not timer[ CALLBACK ]():
					if i in __timers:
						del __timers[ i ]
				else:
					# Find a moment in the future. If interval is 0, we
					# just reuse the old timestamp, doesn't matter.
					if timer[ INTERVAL ]:
						now = int( time() * 1000 )
						timestamp += timer[ INTERVAL ]
						while timestamp <= now:
							timestamp += timer[ INTERVAL ]
					timer[ TIMESTAMP ] = timestamp

		# handle sockets
		if fds:
			for fd, condition in fds:
				try:
					sock_obj = __sock_objects[ fd ]
				except KeyError:
					continue  # ignore recently removed socket (by timer in this step() call)
				# check for closed pipes/sockets
				if condition in ( select.POLLHUP, select.POLLNVAL ):
					socket_remove( sock_obj, IO_ALL )
					continue
				# check for errors
				if condition == select.POLLERR:
					if fd in __sockets[ IO_EXCEPT ] and not __sockets[ IO_EXCEPT ][ fd ]( sock_obj ):
						socket_remove( sock_obj, IO_EXCEPT )
					continue
				for cond in ( IO_READ, IO_WRITE ):
					if cond & condition and fd in __sockets[ cond ] and \
						   not __sockets[ cond ][ fd ]( sock_obj ):
						socket_remove( sock_obj, cond )

		# handle external dispatchers
		if external:
			__min_timer = dispatch.dispatcher_run()
	finally:
		__step_depth -= 1
		__in_step = False

def loop():
	"""Executes the 'main loop' forever by calling step in an endless loop"""
	while True:
		step()

def _init():
	global __step_depth_max

	log.set_level( log.CRITICAL )
	__step_depth_max = _options[ 'recursive_depth' ]
