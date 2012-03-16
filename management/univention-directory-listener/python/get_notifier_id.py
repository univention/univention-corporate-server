#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention Directory Listener
#  read the notifier id from the dc master
#
# Copyright 2004-2012 Univention GmbH
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

import socket
import univention.config_registry
import sys

configRegistry = univention.config_registry.ConfigRegistry()
configRegistry.load()

if not configRegistry.has_key( 'ldap/master' ):
	print 'Error: ldap/master not set'
	sys.exit(-1)

s = socket.socket( socket.AF_INET, socket.SOCK_STREAM );
s.connect ( (configRegistry['ldap/master'], 6669) )

s.send('Version: 2\nCapabilities: \n\n')
s.recv(100)

s.send('MSGID: 1\nGET_ID\n\n')
notifierResult = s.recv(100)

if notifierResult:
	print "%s" % notifierResult.split('\n')[1]

