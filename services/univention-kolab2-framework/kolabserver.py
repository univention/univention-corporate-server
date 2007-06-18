#
# Univention Kolab2 Framework
#  listener module: basic kolab server configuration
#
# Copyright (C) 2005, 2006 Univention GmbH
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
import univention_baseconfig
import os
import univention.debug

name='kolabserver'
description='Update Kolabhome Server'
filter="(&(|(objectClass=univentionDomainController)(objectClass=univentionMemberServer))(univentionService=kolab2))"
attributes=[]

def initialize():
	pass

def handler(dn, new, old):
	baseConfig = univention_baseconfig.baseConfig()
	baseConfig.load()
	listener.setuid(0)
	try:
		if new and new.has_key('univentionService') and 'kolab2' in new['univentionService']:
			name="%s.%s" % (new['cn'][0], baseConfig['domainname'])
			if baseConfig.has_key('postfix/permithosts'):
				if not name in baseConfig['postfix/permithosts'].split(' '):
					listener.run('/usr/sbin/univention-baseconfig', ['univention-baseconfig','set', 'postfix/permithosts=%s %s' % ( baseConfig['postfix/permithosts'], name)], uid=0)
			else:
				listener.run('/usr/sbin/univention-baseconfig', ['univention-baseconfig','set', 'postfix/permithosts=%s' % (name)], uid=0)
		elif old and old.has_key('cn'):
			name="%s.%s" % (old['cn'][0], baseConfig['domainname'])
			if name in baseConfig['postfix/permithosts'].split(' '):
				listener.run('/usr/sbin/univention-baseconfig', ['univention-baseconfig','set', 'postfix/permithosts=%s' % ( baseConfig['postfix/permithosts'].replace(name, ''))], uid=0)
	finally:
		listener.unsetuid()


def postrun():
	listener.setuid(0)
	try:
		os.spawnv(os.P_WAIT, '/bin/sh', ['sh', '/etc/init.d/postfix', 'restart'])
	finally:
		listener.unsetuid()
