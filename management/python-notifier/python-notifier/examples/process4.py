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
	cmd = ['ps', 'h', '-eo', 'pcpu,vsize,rssize,pmem,user,pid,command', '--sort=-pcpu']
	proc = notifier.popen.Process( cmd, stdout = True )
	proc.signal_connect( 'stdout', find_result )
	proc.start()

	return True

def find_result( pid, result ):
	for line in result:
		print line

if __name__ == '__main__':
	notifier.init( notifier.GENERIC )

	notifier.timer_add( 5000, tick )

	notifier.loop()
