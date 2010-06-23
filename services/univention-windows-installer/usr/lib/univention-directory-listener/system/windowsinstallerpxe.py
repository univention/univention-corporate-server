# -*- coding: utf-8 -*-
#
# Univention Windows Installer
#  listener module for the pxe files
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

name='windowsinstallerpxe'
description='PXE configuration for the Windows installer'
filter='(objectClass=univentionWindows)'
attributes=['univentionWindowsReinstall', 'aRecord']

import listener, univention.config_registry
import os, re, ldap, string, univention.debug

pxebase = '/var/lib/univention-client-boot/pxelinux.cfg'

baseConfig = univention.config_registry.baseConfig()
baseConfig.load()

pxeconfig_install = \
'''# Perform an unattended installation by default
default inst

# Always prompt
prompt 0

# Display the bootup message
display windows-installer.msg

# Boot automatically after 30 seconds from local disk
timeout 300

label local
	localboot 0

label inst
	# Boot the universal PXE driver disk-image and append the DNS-Server
        kernel bzImage
        append initrd=initrd z_path=//%s/install y_path=//%s/insthelp x_path=//%s/instdone
''' % (baseConfig['hostname'], baseConfig['hostname'], baseConfig['hostname'])

pxeconfig_local = \
'''default local
label local
	localboot 0
'''

def ip_to_hex(ip):
	if ip.count('.') != 3:
		return ''
	o = ip.split('.')
	return '%02X%02X%02X%02X' % (int(o[0]), int(o[1]), int(o[2]), int(o[3]))

def handler(dn, new, old):

	# remove pxe host file
	if old and old.has_key('aRecord'):
		basename = ip_to_hex(old['aRecord'][0])
		if not basename:
			univention.debug.debug(univention.debug.LISTENER, univention.debug.ERROR, 'PXE: invalid IP address %s' % old['aRecord'][0])
			return
		filename = os.path.join(pxebase, basename)
		if os.path.exists(filename):
			listener.setuid(0)
			try:
				os.unlink(filename)
			finally:
				listener.unsetuid()

	# create pxe host file(s)
	if new and new.has_key('aRecord'):

		cn = new['cn'][0]
		univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, 'PXE: writing configuration for host %s' % cn)
			
		basename = ip_to_hex(new['aRecord'][0])
		if not basename:
			univention.debug.debug(univention.debug.LISTENER, univention.debug.ERROR, 'PXE: invalid IP address %s' % new['aRecord'][0])
			return
		filename = os.path.join(pxebase, basename)

		if new.has_key('univentionWindowsReinstall') and new['univentionWindowsReinstall'][0] == '1':
			path = os.path.join('/var/lib/univention-windows-installer', new['aRecord'][0])
			listener.setuid(0)
			try:
				if os.path.exists(path):
					for i in os.listdir(path):
						os.unlink(os.path.join(path,i))
					os.rmdir(path)
			finally:
				listener.unsetuid()
		
			pxeconfig = pxeconfig_install
		else:
			pxeconfig = pxeconfig_local

		listener.setuid(0)
		try:
			f=open(filename, 'w')
			f.write(pxeconfig)
			f.close()
		finally:
			listener.unsetuid()
