#!/usr/bin/python2.4
#
# Univention LDAP Listener
#  read the notifier id from the dc master
#
# Copyright (C) 2004, 2005, 2006 Univention GmbH
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

import socket
import univention_baseconfig
import sys

baseConfig = univention_baseconfig.baseConfig()
baseConfig.load()

if not baseConfig.has_key( 'ldap/master' ):
	print 'Error: ldap/master not set'
	sys.exit(-1)

s = socket.socket( socket.AF_INET, socket.SOCK_STREAM );
s.connect ( (baseConfig['ldap/master'], 6669) )

s.send('Version: 2\nCapabilities: \n\n')
s.recv(100)

s.send('MSGID: 1\nGET_ID\n\n')
notifierResult = s.recv(100)

if notifierResult:
	print "%s" % notifierResult.split('\n')[1]

