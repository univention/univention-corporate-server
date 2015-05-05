#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Author: Andreas Büsching <crunchy@bitkipper.net>
#
# log - a logging facility for the generic notifier module
#
# Copyright (C) 2005, 2006, 2010, 2011
#		Andreas Büsching <crunchy@bitkipper.net>
#
# This library is free software; you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License version
# 2.1 as published by the Free Software Foundation.
#
# This library is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301 USA

# CRITICAL is the same as FATAL
from logging import getLogger, Formatter, Handler, StreamHandler, FileHandler, CRITICAL, FATAL, ERROR, WARN, INFO, DEBUG
from sys import stderr

instance = getLogger( 'notifier' )
formatter = Formatter( "%(asctime)s: %(name)s: %(levelname)-8s: %(message)s" )

debug = instance.debug
info = instance.info
warn = instance.warn
error = instance.error
critical = instance.critical
exception = instance.exception

set_level = instance.setLevel

def open( *arg ):
	'''Add the given list of handlers. If no handler is given two
	default handlers will be installed that log to stderr and
	/var/log/python-notifier.log'''
	global formatter, instance

	instance.handlers = []
	if not arg:
		try:
			file_handler = FileHandler( '/var/log/python-notifier.log' )
			file_handler.setFormatter( formatter )
			instance.addHandler( file_handler )
		except:
			pass

		stream_handler = StreamHandler( stderr )
		stream_handler.setFormatter( formatter )
		instance.addHandler( stream_handler )
	else:
		for hdl in arg:
			instance.addHandler( hdl )

open()
