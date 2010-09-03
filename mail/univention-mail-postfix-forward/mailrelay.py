# -*- coding: utf-8 -*-
#
# Univention mail Postfix Forward
#  listener module: sets mail relay configuration and restarts postfixs
#
# Copyright 2004-2010 Univention GmbH
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
		except Exception, e:
			univention.debug.debug(univention.debug.ADMIN, univention.debug.WARN, 'Reload postfix failed: %s' % str(e))

	finally:
		listener.unsetuid()

def postrun():
	listener.setuid(0)
	try:
		univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, 'mailrelay: Reloading postfix')
		try:
			os.spawnv(os.P_WAIT, '/etc/init.d/postfix', ['postfix', 'reload'])
		except Exception, e:
			univention.debug.debug(univention.debug.ADMIN, univention.debug.WARN, 'Reload postfix failed: %s' % str(e))
	finally:
		listener.unsetuid()
