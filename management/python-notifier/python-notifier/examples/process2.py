#!/usr/bin/env python
#-*- coding: utf-8 -*-
#
# Author: Andreas Büsching <crunchy@bitkipper.net>
#
# an example demonstrating the process handler class RunIt
#
# Copyright (C) 2006
#		Andreas Büsching <crunchy@bitkipper.net>
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

import os, sys

import notifier
import notifier.popen

def tick():
	print 'tick'
	return True

def find_result( pid, status, result ):
	print 'process %d died (%d)' % ( pid, status )
	print 'output:',
	if result:
		print len( result ), 'lines'
	else:
		print result


if __name__ == '__main__':
	notifier.init( notifier.GENERIC )

	# show we can still do things
	notifier.timer_add( 500, tick )

	cmd = '/bin/sh -c "/bin/sleep 2 && /usr/bin/find /usr/bin"'
	# cmd = '/usr/bin/find /var/log'
	proc = notifier.popen.RunIt( cmd, stdout = True )
	proc.signal_connect( 'finished', find_result )
	print 'started process', proc.start()

	notifier.loop()
