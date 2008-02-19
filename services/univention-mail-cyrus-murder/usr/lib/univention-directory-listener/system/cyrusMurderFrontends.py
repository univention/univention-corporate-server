# -*- coding: utf-8 -*-
#
# Univention Cyrus Murder
#  listener module: Cyrus Murder frontend list
#
# Copyright (C) 2008 Univention GmbH
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
import univention.config_registry
import os
import univention.debug

name='cyrusMurderFrontends'
description='Update Cyrus Murder Frontend List'
filter="(&(objectClass=univentionDomainController)(univentionService=kolab2-frontend))"
attributes=[]

def initialize():
	pass

def handler(dn, new, old):
	configRegistry = univention.config_registry.ConfigRegistry()
	configRegistry.load()
	listener.setuid(0)
	try:
		if new and new.has_key('univentionService') and 'kolab2-frontend' in new['univentionService']:
			fqdn="%s.%s" % (new['cn'][0], configRegistry['domainname'])
			if configRegistry.has_key('mail/cyrus/murder/frontends'):
				if not fqdn in configRegistry['mail/cyrus/murder/frontends'].split(' '):
					listener.run('/usr/sbin/univention-config-registry', ['univention-config-registry','set', 'mail/cyrus/murder/frontends=%s %s' % ( configRegistry['mail/cyrus/murder/frontends'], fqdn)], uid=0)
			else:
				listener.run('/usr/sbin/univention-config-registry', ['univention-config-registry','set', 'mail/cyrus/murder/frontends' % (name)], uid=0)
		elif old and old.has_key('cn'):
			fqdn="%s.%s" % (old['cn'][0], configRegistry['domainname'])
			if fqdn in configRegistry['mail/cyrus/murder/frontends'].split(' '):
				listener.run('/usr/sbin/univention-config-registry', ['univention-config-registry','set', 'mail/cyrus/murder/frontends=%s' % ( configRegistry['mail/cyrus/murder/frontends'].replace(fqdn, ''))], uid=0)
			# if a frontend service is removed, the backend continues to run
			# on the backend/hostname (if running at all)
	finally:
		listener.unsetuid()


def postrun():
	listener.setuid(0)
	try:
		os.spawnv(os.P_WAIT, '/bin/sh', ['sh', '/etc/init.d/cyrus2.2', 'restart'])
	finally:
		listener.unsetuid()
