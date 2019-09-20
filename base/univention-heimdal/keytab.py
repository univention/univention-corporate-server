# -*- coding: utf-8 -*-
#
# Univention Heimdal
#  generating keytab entries
#
# Copyright 2004-2019 Univention GmbH
#
# https://www.univention.de/
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
# <https://www.gnu.org/licenses/>.
__package__ = ''  # workaround for PEP 366
import listener
import os
import time
import univention.debug as ud
from subprocess import call

hostname = listener.configRegistry['hostname']
domainname = listener.configRegistry['domainname']
base_domain = listener.configRegistry['ldap/base'].replace('dc=', '').replace(',', '.')
realm = listener.configRegistry['kerberos/realm']
server_role = listener.configRegistry['server/role']
ldap_master = listener.configRegistry['ldap/master']
samba4_role = listener.configRegistry.get('samba4/role', '')


name = 'keytab'
description = 'Kerberos 5 keytab maintainance'
filter = (
	'(&'
	'(objectClass=krb5Principal)'
	'(objectClass=krb5KDCEntry)'
	'(krb5KeyVersionNumber=*)'
	'(|'
	'(krb5PrincipalName=host/%(hostname)s@%(realm)s)'
	'(krb5PrincipalName=ldap/%(hostname)s@%(realm)s)'
	'(krb5PrincipalName=host/%(hostname)s.%(domainname)s@%(realm)s)'
	'(krb5PrincipalName=ldap/%(hostname)s.%(domainname)s@%(realm)s)'
	'(krb5PrincipalName=host/%(hostname)s.%(base_domain)s@%(realm)s)'
	'(krb5PrincipalName=ldap/%(hostname)s.%(base_domain)s@%(realm)s)'
	')'
	')'
) % locals()

K5TAB = '/etc/krb5.keytab'


def clean():
	# don't do anything here if this system is joined as a Samba 4 DC
	if samba4_role.upper() in ('DC', 'RODC'):
		return

	listener.setuid(0)
	try:
		if os.path.exists(K5TAB):
			os.unlink(K5TAB)
	finally:
		listener.unsetuid()


def handler(dn, new, old):
	# don't do anything here if this system is joined as a Samba 4 DC
	if samba4_role.upper() in ('DC', 'RODC'):
		return

	if not new.get('krb5Key'):
		return

	if server_role == 'memberserver':
		ud.debug(ud.LISTENER, ud.PROCESS, 'Fetching %s from %s' % (K5TAB, ldap_master))
		listener.setuid(0)
		try:
			if os.path.exists(K5TAB):
				os.remove(K5TAB)
			count = 0
			while not os.path.exists(K5TAB):
				call(['univention-scp', '/etc/machine.secret', '%s$@%s:/var/lib/univention-heimdal/%s' % (hostname, ldap_master, hostname), K5TAB])
				if not os.path.exists(K5TAB):
					if count > 30:
						ud.debug(ud.LISTENER, ud.ERROR, 'E: failed to download keytab for memberserver')
						return -1
					ud.debug(ud.LISTENER, ud.WARN, 'W: failed to download keytab for memberserver, retry')
					count += 1
					time.sleep(2)
			os.chown(K5TAB, 0, 0)
			os.chmod(K5TAB, 0o600)
		finally:
			listener.unsetuid()
	else:
		ud.debug(ud.LISTENER, ud.PROCESS, 'Exporting %s on %s' % (K5TAB, server_role))
		listener.setuid(0)
		try:
			if old:
				call(['ktutil', 'remove', '-p', old['krb5PrincipalName'][0]])
			if new:
				call(['kadmin', '-l', 'ext', new['krb5PrincipalName'][0]])
		finally:
			listener.unsetuid()


def initialize():
	ud.debug(ud.LISTENER, ud.INFO, 'init keytab')
