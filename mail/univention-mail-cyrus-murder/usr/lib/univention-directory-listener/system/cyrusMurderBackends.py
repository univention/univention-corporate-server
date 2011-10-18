# -*- coding: utf-8 -*-
#
# Univention Cyrus Murder
#  listener module: Cyrus Murder backend and frontend list
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

name='cyrusMurderBackends'
description='Update Cyrus Murder Backend List'
filter="(&(|(objectClass=univentionDomainController)(objectClass=univentionMemberServer))(univentionService=kolab2-backend))"
attributes=[]

def initialize():
	pass

def handler(dn, new, old):
	configRegistry = univention.config_registry.ConfigRegistry()
	configRegistry.load()
	listener.setuid(0)
	try:
		if new and new.has_key('mailPrimaryAddress'):
			emailId = "%s" % new['mailPrimaryAddress'][0]
			fqdn = "%s.%s" % (new['cn'][0], configRegistry['domainname'])
			if configRegistry.has_key('mail/cyrus/murder/backends'):
				if not emailId in configRegistry['mail/cyrus/murder/backends'].split(' '):
					listener.run('/usr/sbin/univention-config-registry', ['univention-config-registry','set', 'mail/cyrus/murder/backends=%s %s' % ( configRegistry['mail/cyrus/murder/backends'], emailId)], uid=0)
			else:
				listener.run('/usr/sbin/univention-config-registry', ['univention-config-registry','set', 'mail/cyrus/murder/backends=%s' % (emailId)], uid=0)

		elif old and old.has_key('mailPrimaryAddress'):
			emailId = "%s" % old['mailPrimaryAddress'][0]
			if emailId in configRegistry['mail/cyrus/murder/backends'].split(' '):
				listener.run('/usr/sbin/univention-config-registry', ['univention-config-registry','set', 'mail/cyrus/murder/backends=%s' % ( configRegistry['mail/cyrus/murder/backends'].replace(emailId, ''))], uid=0)
			# leave the backend/hostname set, so the service can be switched on again easily
	finally:
		listener.unsetuid()


def postrun():
	listener.setuid(0)
	try:
		os.spawnv(os.P_WAIT, '/bin/sh', ['sh', '/etc/init.d/cyrus2.2', 'restart'])
	finally:
		listener.unsetuid()
