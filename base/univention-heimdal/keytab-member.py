# -*- coding: utf-8 -*-
#
# Univention Heimdal
#  listener script for generating memberserver keytab entry
#
# Copyright 2004-2014 Univention GmbH
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
__package__='' 	# workaround for PEP 366
import listener, os, pwd, types
import univention.debug
import univention.config_registry

name='keytab-member'
description='Kerberos 5 keytab maintainance for memberserver'
filter='(&(objectClass=krb5Principal)(objectClass=krb5KDCEntry)(krb5KeyVersionNumber=*)(objectClass=univentionMemberServer))'

etypes = ['des-cbc-crc', 'des-cbc-md4', 'des3-cbc-sha1', 'des-cbc-md5', 'arcfour-hmac-md5']
listener.setuid(0)

def clean():
	pass

def handler(dn, new, old):
	global keytab

	configRegistry = univention.config_registry.ConfigRegistry()
	configRegistry.load()

	server_role = configRegistry['server/role']
	if server_role == 'domaincontroller_master':
			
		if not new.get('krb5Key'):
			return

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
