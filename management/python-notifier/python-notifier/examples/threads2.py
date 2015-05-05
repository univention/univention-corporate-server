#!/usr/bin/env python
#-*- coding: utf-8 -*-
#
# Author: Andreas Büsching <crunchy@bitkipper.net>
#
# an example demonstrating the thread handling
#
# Copyright (C) 2011
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

import notifier
import notifier.threads as threads

import os
import random
import sys
import time

def my_thread( words ):
	number = random.randint( 50, 100 )
	for i in range( number ):
		time.sleep( 0.1 )
	if random.randint( 0, 10 ) < 6:
		raise Exception( 'mysterious problem' )
	return number

def done_with_it( thread, result, another ):
	print "-> Thread '%s' is finished" % thread.name
	print "  Argument:", another
	if isinstance( thread.result, BaseException ):
		print "  Error occurred during thread processing:", type( thread.result ), thread.result
		print "  Details:\n%s" % ''.join( thread.trace )
	else:
		print "  Counted from 0 to %d" % result

def doing_something_else():
	print 'tick'
	return True

if __name__ == '__main__':
	notifier.init( notifier.GENERIC )

	_stdout = os.fdopen( sys.stdout.fileno(), 'w', 0 )
	_stdout.write( 'Starting threads ' )
	for i in range( 100 ):
		_stdout.write( '.' )
		task = threads.Simple( 'test%d' % i,
							   notifier.Callback( my_thread, [ 'hello', 'world' ] ),
							   notifier.Callback( done_with_it, 'another argument' ) )
		task.run()
		time.sleep( 0.05 )
		_stdout.write( '\033[1D*' )
	_stdout.write( '\n' )
	notifier.timer_add( 1000, doing_something_else )
	notifier.loop()
