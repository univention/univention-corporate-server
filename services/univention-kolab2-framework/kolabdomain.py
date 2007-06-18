#
# Univention Kolab2 Framework
#  listener module: mail domain configuration
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

name='kolabdomain'
description='Update Kolabdomains'
filter='(&(objectClass=univentionMailDomainname)(cn=*))'
attributes=[]

def initialize():
	pass

def handler(dn, new, old):
	baseConfig = univention_baseconfig.baseConfig()
	baseConfig.load()
	listener.setuid(0)
	try:
		if new and new.has_key('cn') and new['cn']:
			if baseConfig.has_key('mail/hosteddomains'):
				if not new['cn'][0] in baseConfig['mail/hosteddomains'].split(' '):
					listener.run('/usr/sbin/univention-baseconfig', ['univention-baseconfig','set', 'mail/hosteddomains=%s %s' % ( baseConfig['mail/hosteddomains'], new['cn'][0])], uid=0)
			else:
				listener.run('/usr/sbin/univention-baseconfig', ['univention-baseconfig','set', 'mail/hosteddomains=%s' % (new['cn'][0])], uid=0)
		elif old and old.has_key('cn'):
			if name in baseConfig['mail/hosteddomains'].split(' '):
				list=baseConfig['mail/hosteddomains'].split(' ')
				nlist=[]
				for entry in list:
					if entry != old['cn'][0]:
						nlist.append(entry)
				listener.run('/usr/sbin/univention-baseconfig', ['univention-baseconfig','set', 'mail/hosteddomains=%s' % ( string.join(nlist, ' '))], uid=0)
	finally:
		listener.unsetuid()

def postrun():
	listener.setuid(0)
	try:
		os.spawnv(os.P_WAIT, '/usr/sbin/postmap', ['postmap', '/etc/postfix/transport'])
		os.spawnv(os.P_WAIT, '/etc/init.d/postfix', ['postfix', 'restart'])
	finally:
		listener.unsetuid()
