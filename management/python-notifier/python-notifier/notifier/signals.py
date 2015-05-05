#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Author: Andreas Büsching	<crunchy@bitkipper.net>
#
# a generic signal implementation for propagating asynchron events
#
# Copyright (C) 2005, 2006, 2010, 2011
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

__signals = {}

# exception classes
class UnknownSignalError( Exception ):
	pass

class SignalExistsError( Exception ):
	pass

class Signal( object ):
	def __init__( self, name ):
		self.name = name
		self.__callbacks = []

	def emit( self, *args ):
		for cb in self.__callbacks:
			cb( *args )

	def connect( self, callback ):
		self.__callbacks.append( callback )

	def disconnect( self, callback ):
		try:
			self.__callbacks.remove( callback )
		except:
			pass

	def __str__( self ):
		return self.name

class Provider( object ):
	def __init__( self ):
		self.__signals = {}

	def signal_new( self, signal ):
		new( signal, self.__signals )

	def signal_exists( self, signal ):
		return exists( signal, self.__signals )

	def signal_connect( self, signal, callback ):
		connect( signal, callback, self.__signals )

	def signal_disconnect( self, signal, callback ):
		disconnect( signal, callback, self.__signals )

	def signal_emit( self, signal, *args ):
		if isinstance( signal, Signal ) and signal.name in self.__signals:
			self.__signals[ signal.name ].emit( *args )
		elif isinstance( signal, basestring ) and signal in self.__signals:
			self.__signals[ signal ].emit( *args )

def _select_signals( signals ):
	global __signals
	if signals is None:
		return __signals
	return signals

def new( signal, signals = None ):
	_signals = _select_signals( signals )
	if isinstance( signal, basestring ):
		signal = Signal( signal )

	if signal.name in _signals:
		raise SignalExistsError( "Signal '%s' already exists" % signal.name )
	else:
		_signals[ signal.name ] = signal

def exists( signal, signals = None ):
	_signals = _select_signals( signals )
	if isinstance( signal, basestring ):
		return signal in _signals
	else:
		return signal.name in _signals

def connect( signal, callback, signals = None ):
	_signals = _select_signals( signals )
	if isinstance( signal, Signal ) and signal.name in _signals:
		_signals[ signal.name ].connect( callback )
	elif isinstance( signal, basestring ):
		if signal in _signals:
			_signals[ signal ].connect( callback )
		else:
			raise UnknownSignalError( "unknown signal '%s'" % signal )


def disconnect( signal, callback, signals = None ):
	_signals = _select_signals( signals )
	if isinstance( signal, Signal ) and signal.name in _signals:
		_signals[ signal.name ].disconnect( callback )
	elif isinstance( signal, basestring ) and signal in _signals:
		_signals[ signal ].disconnect( callback )

def emit( signal, *args ):
	if isinstance( signal, Signal ) and signal.name in __signals:
		__signals[ signal.name ].emit( *args )
	elif isinstance( signal, basestring ):
		if signal in __signals:
			__signals[ signal ].emit( *args )
		else:
			raise UnknownSignalError( "unknown signal '%s'" % signal )
