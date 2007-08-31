#
# Univention Server Installation
#  listener module: creates PXE boot configurations
#
# Copyright (C) 2004, 2005, 2006, 2007 Univention GmbH
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

import univention.config_registry

baseConfig=univention.config_registry.baseConfig()

name='serverinstallerpxe'
description='PXE configuration for the Server installer'
filter='(|(objectClass=univentionDomainController)(objectClass=univentionMemberServer)(objectClass=univentionClient)(objectClass=univentionMobileClient))'
attributes=['univentionServerReinstall', 'aRecord', 'univentionServerInstallationProfile', 'univentionServerInstallationText']

import listener
import os, re, ldap, string, univention.debug

pxebase = '/var/lib/univention-client-boot/pxelinux.cfg'

def ip_to_hex(ip):
	if ip.count('.') != 3:
		return ''
	o = ip.split('.')
	return '%02X%02X%02X%02X' % (int(o[0]), int(o[1]), int(o[2]), int(o[3]))

def handler(dn, new, old):

	baseConfig.load()

	if baseConfig.has_key('pxe/append'):
		append = baseConfig['pxe/append']
	else:
		append = "root=/dev/ram rw initrd=linux.bin ramdisk_size=98304  flavor=linux nfs"

	pxeconfig_start = \
	'''# Perform an profile installation by default
PROMPT 0
DEFAULT linux
IPAPPEND 1

APPEND %s '''%append
	pxeconfig_end = \
	'''
LABEL linux
  KERNEL linux-server

'''

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

		if new.has_key('univentionServerReinstall') and new['univentionServerReinstall'][0] == '1':
			listener.setuid(0)
			try:
				f=open(filename, 'w')
				f.write(pxeconfig_start)
				if new.has_key('univentionServerInstallationText') and new['univentionServerInstallationText'][0] == '1':
					f.write(' use_text ')
				if new.has_key('univentionServerInstallationProfile') and new['univentionServerInstallationProfile'][0]:
					f.write('profile=%s \n' % new['univentionServerInstallationProfile'][0])
				else:
					f.write('\n')
				f.write(pxeconfig_end)
				f.close()
			finally:
				listener.unsetuid()
