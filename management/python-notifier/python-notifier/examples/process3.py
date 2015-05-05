#!/usr/bin/env python
#-*- coding: utf-8 -*-
#
# Author: Andreas Büsching <crunchy@bitkipper.net>
#
# an example demonstrating the process handler class RunIt
#
# Copyright (C) 2009
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

def give_birth():
	ls = notifier.popen.run( '/bin/ls -ltr /etc', stderr = False, shell = False )
	# process dead?
	if ls.pid == None:
		print ls.stdout.read()
		ls.stdout.close()

	sleep = notifier.popen.run( 'sleep 5', timeout = 3, stderr = False, stdout = False, shell = False )
	if sleep.pid:
		print 'process still running', sleep.pid
		ret = notifier.popen.kill( sleep )
		print 'killed', ret

	return False

if __name__ == '__main__':
	notifier.init( notifier.GENERIC )

	# run processes
	notifier.timer_add( 1500, give_birth )

	# show we can still do things
	notifier.timer_add( 500, tick )

	notifier.loop()
