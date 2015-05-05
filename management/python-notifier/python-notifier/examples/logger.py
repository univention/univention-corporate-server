#!/usr/bin/env python
#-*- coding: utf-8 -*-
#
# Author: Andreas Büsching <crunchy@bitkipper.net>
#
# logger
#
# Copyright (C) 2005, 2006, 2009
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

import os

import notifier

def tail_minus_f( logfile ):
	new_size = os.stat( logfile.name )[ 6 ]
	if new_size > logfile.tell():
		buffer = logfile.read( 65536 )
		if buffer: print buffer,

	return True

if __name__ == '__main__':
	notifier.init()
	filename = '/var/log/messages'
	if not os.path.isfile( filename ):
		filename = '/var/log/syslog'
	log = open( filename, 'rb' )
	log.seek( os.stat( filename )[ 6 ] )
	notifier.timer_add( 100, notifier.Callback( tail_minus_f, log ) )
	notifier.loop()
