# -*- coding: utf-8 -*-
#
# Univention Heimdal
#  listener script for generating memberserver keytab entry
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
import listener, os, pwd, types
import univention.debug
import univention_baseconfig

name='keytab-member'
description='Kerberos 5 keytab maintainance for memberserver'
filter='(&(objectClass=krb5Principal)(objectClass=krb5KDCEntry)(krb5KeyVersionNumber=*)(objectClass=univentionMemberServer))'

etypes = ['des-cbc-crc', 'des-cbc-md4', 'des3-cbc-sha1', 'des-cbc-md5', 'arcfour-hmac-md5']
listener.setuid(0)

def clean():
	pass

def handler(dn, new, old):
	global keytab

	baseConfig = univention_baseconfig.baseConfig()
	baseConfig.load()

	server_role = baseConfig['server/role']
	if server_role == 'domaincontroller_master':
			
		listener.setuid(0)
		try:
			if old:
				try:
					os.unlink('/var/lib/univention-heimdal/%s' %old['cn'][0])
				except:
					pass
			if new:
				#FIXME: otherwise the keytab entry is duplicated
				os.spawnv(os.P_WAIT, '/usr/sbin/kadmin', ['kadmin', '-l', 'ext', '--keytab=/var/lib/univention-heimdal/%s' % new['cn'][0], new['krb5PrincipalName'][0]])
				try:
					userID=pwd.getpwnam('%s$'%new['cn'][0])[2]
					os.chown('/var/lib/univention-heimdal/%s' %new['cn'][0], userID, 0)
					os.chmod('/var/lib/univention-heimdal/%s' %new['cn'][0],0660)
				except:
					pass


		finally:
			listener.unsetuid()
