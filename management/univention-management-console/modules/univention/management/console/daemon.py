#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  main for the UMC daemon
#
# Copyright (C) 2006, 2007 Univention GmbH
#
# http://www.univention.de/
#
# All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# Binary versions of this file provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import os
import signal
import univention.debug as ud

'''helper function to daemonize a process'''

def daemonize( name ):
	try:
		pid = os.fork()
	except OSError, e:
		ud.debug( ud.ADMIN, ud.ERROR, 'Daemon Mode Error: %s' % e.strerror)
		return False

	if (pid == 0):
		os.setsid()
		signal.signal(signal.SIGHUP, signal.SIG_IGN)
		try:
			pid = os.fork()
		except OSError, e:
			ud.debug( ud.ADMIN, ud.ERROR, 'Daemon Mode Error: %s' % e.strerror)
			return False

		if (pid == 0):
			os.chdir("/")
			os.umask(0)
		else:
			pf = open( '/var/run/univention-management-console/%s.pid' % name,
					   'w+' )
			pf.write( str( pid ) )
			pf.close()
			os._exit( 0 )
	else:
		os._exit(0)

	__close_files()

	os.open("/dev/null", os.O_RDONLY)
	os.open("/dev/null", os.O_RDWR)
	os.open("/dev/null", os.O_RDWR)

	return True

def __close_files():
	try:
		maxfd = os.sysconf( "SC_OPEN_MAX" )
	except ( AttributeError, ValueError ):
		maxfd = 256       # default maximum

	for fd in range( 0, maxfd ):
		try:
			os.close( fd )
		except OSError:   # ERROR (ignore)
			pass
