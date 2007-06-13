# -*- coding: utf-8 -*-
#
# Univention Heimdal
#  generating keytab entries
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
import listener, os, pwd, types, time, univention.debug

hostname = listener.baseConfig['hostname']
domainname = listener.baseConfig['domainname']
realm = listener.baseConfig['kerberos/realm']
server_role = listener.baseConfig['server/role']
ldap_master = listener.baseConfig['ldap/master']


name='keytab'
description='Kerberos 5 keytab maintainance'
filter='(&(objectClass=krb5Principal)(objectClass=krb5KDCEntry)(krb5KeyVersionNumber=*)(|(krb5PrincipalName=host/%s@%s)(krb5PrincipalName=ldap/%s@%s)(krb5PrincipalName=host/%s.%s@%s)(krb5PrincipalName=ldap/%s.%s@%s)(krb5PrincipalName=host/%s.%s@%s)(krb5PrincipalName=ldap/%s.%s@%s)))' % (hostname, realm, hostname, realm, hostname, domainname, realm, hostname, domainname, realm, hostname, listener.baseConfig['ldap/base'].replace('dc=','').replace(',','.'), realm, hostname, listener.baseConfig['ldap/base'].replace('dc=','').replace(',','.'), realm)

etypes = ['des-cbc-crc', 'des-cbc-md4', 'des3-cbc-sha1', 'des-cbc-md5', 'arcfour-hmac-md5']
listener.setuid(0)

def clean():
	global keytab

	listener.setuid(0)
	try:
		if os.path.exists('/etc/krb5.keytab'):
			os.unlink('/etc/krb5.keytab')
	finally:
		listener.unsetuid()

def handler(dn, new, old):
	global keytab

	if server_role == 'memberserver':
		listener.setuid(0)
		if os.path.exists('/etc/krb5.keytab'):
			os.remove('/etc/krb5.keytab')
		count=0
		while not os.path.exists('/etc/krb5.keytab'):
			os.spawnv(os.P_WAIT, '/usr/sbin/univention-scp', ['univention-scp', '/etc/machine.secret', '%s$@%s:/var/lib/univention-heimdal/%s' % (hostname, ldap_master, hostname), '/etc/krb5.keytab'])
			if not os.path.exists('/etc/krb5.keytab'):
				univention.debug.debug(univention.debug.LISTENER, univention.debug.WARN, 'W: failed to download keytab for memberserver, retry')
				if count > 30:
					univention.debug.debug(univention.debug.LISTENER, univention.debug.ERROR, 'E: failed to download keytab for memberserver')
					listener.unsetuid()
					return -1
				count=count+1
				time.sleep(2)
		os.chown('/etc/krb5.keytab', 0, 0)
		os.chmod('/etc/krb5.keytab', 0600)
		listener.unsetuid()
	else:
		listener.setuid(0)
		try:
			if old:
				os.spawnv(os.P_WAIT, '/usr/sbin/ktutil', ['ktutil', 'remove', '-p', old['krb5PrincipalName'][0]])
			if new:
				#FIXME: otherwise the keytab entry is duplicated
				os.spawnv(os.P_WAIT, '/usr/sbin/ktutil', ['ktutil', 'remove', '-p', new['krb5PrincipalName'][0]])
				os.spawnv(os.P_WAIT, '/usr/sbin/kadmin', ['kadmin', '-l', 'ext', new['krb5PrincipalName'][0]])

		finally:
			listener.unsetuid()
def initialize():
	univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, 'init keytab')

