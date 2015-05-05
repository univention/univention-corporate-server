#!/usr/bin/env python
#-*- coding: utf-8 -*-
#
# Author: Andreas Büsching <crunchy@bitkipper.net>
#
# an example demonstrating the process handler class
#
# Copyright (C) 2006
#	Andreas Büsching <crunchy@bitkipper.net>
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

import os, sys

import notifier
import notifier.popen

proc = None
output = False

lineno = 0

def stdout( pid, line ):
	global output

	output.extend( line )
	if not type( line ) in ( list, tuple ):
		line = [ line ]

def stderr( pid, line ):
	if not type( line ) in ( list, tuple ):
		line = [ line ]
	for l in line:
		print "(%d>2): %s" % ( pid, l )

def died( pid, status ):
	global output, lineno
	print ">>> process %d died" % pid, status

	if not output:
		print ">>> process %d produced NO output" % pid, status
	elif lineno and len( output ) != lineno:
		print 'NUMBERS OF LINES DO NOT MATCH!', len( output ), lineno
		fd = open( 'ls_mismatch', 'w' )
		fd.write( '\n'.join( output ) )
		sys.exit( 0 )
	lineno = len( output )
	notifier.timer_add( 100, run_ls )

def tick():
	return True

def runit():
	global proc
	print 'runit ...',
	proc = notifier.popen.Process( '/bin/sleep 5' )
	proc = notifier.popen.Process( '/bin/ls -ltr' )
	proc.signal_connect( 'stdout', stdout )
	proc.signal_connect( 'stderr', stderr )
	proc.signal_connect( 'killed', died )
	proc.start()
	while True:
		if proc.is_alive():
			notifier.step()
		else:
			break

def run_ls():
	global output

	output = []
	proc = notifier.popen.Process( '/bin/ls -latr --color=never /usr/lib' )
	proc.signal_connect( 'stdout', stdout )
	proc.signal_connect( 'stderr', stderr )
	proc.signal_connect( 'killed', died )
	proc.start()

	return False

if __name__ == '__main__':
	notifier.init( notifier.GENERIC )

	# run a process and wait for its death
#	notifier.timer_add( 500, runit )

	# show we can still do things
	notifier.timer_add( 100, tick )

	notifier.timer_add( 500, run_ls )

	notifier.loop()
