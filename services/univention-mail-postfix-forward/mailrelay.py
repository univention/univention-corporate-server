#
# Univention mail Postfix Forward
#  listener module: sets mail relay configuration and restarts postfixs
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

import listener
import os, string
import univention.debug
import univention_baseconfig

name='mailrelay'
description='Update Mail Relay'
filter='(&(objectClass=univentionMailDomain)(mailRelay=*))'
attributes=['mailRelay']


def initialize():
	pass

def handler(dn, new, old):
	listener.setuid(0)

	baseConfig = univention_baseconfig.baseConfig()
	baseConfig.load()

	try:
		if new and new.has_key('mailRelay'):
			relays=''
			for i in range(0,len(new['mailRelay'])):
				relays+=new['mailRelay'][i]
				relays+=' '
			baseConfig['mail/relay']=relays
			baseConfig.save()
		if not new and old:
			baseConfig['mail/relay']=''
			baseConfig.save()
		try:
			os.spawnv(os.P_WAIT, '/usr/sbin/univention-baseconfig', ['univention-baseconfig', 'commit', '/etc/postfix/main.cf'])
		except Exceptionn, e:
			univention.debug.debug(univention.debug.ADMIN, univention.debug.WARN, 'Reload postfix failed: %s' % str(e))

	finally:
		listener.unsetuid()

def postrun():
	listener.setuid(0)
	try:
		univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, 'mailrelay: Reloading postfix')
		try:
			os.spawnv(os.P_WAIT, '/etc/init.d/postfix', ['postfix', 'reload'])
		except Exceptionn, e:
			univention.debug.debug(univention.debug.ADMIN, univention.debug.WARN, 'Reload postfix failed: %s' % str(e))
	finally:
		listener.unsetuid()
