#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  main for the UMC daemon
#
# Copyright 2006-2010 Univention GmbH
#
# http://www.univention.de/
#
# All rights reserved.
#
# The source code of this program is made available
# under the terms of the GNU Affero General Public License version 3
# (GNU AGPL V3) as published by the Free Software Foundation.
#
# Binary versions of this program provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention and not subject to the GNU AGPL V3.
#
# In the case you use this program under the terms of the GNU AGPL V3,
# the program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <http://www.gnu.org/licenses/>.

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
