#
# Univention Server Installation
#  listener module: creates PXE boot configurations
#
# Copyright 2004-2015 Univention GmbH
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

__package__ = '' 	# workaround for PEP 366
import univention.config_registry

name = 'serverinstallerpxe'
description = 'PXE configuration for the Server installer'
filter = '(|(objectClass=univentionDomainController)(objectClass=univentionMemberServer)(objectClass=univentionClient)(objectClass=univentionMobileClient))'
attributes = ['univentionServerReinstall', 'aRecord', 'univentionServerInstallationProfile', 'univentionServerInstallationOption']

import listener
import os
import univention.debug

ucr = listener.configRegistry

pxebase = '/var/lib/univention-client-boot/pxelinux.cfg'


def ip_to_hex(ip):
	if ip.count('.') != 3:
		return ''
	o = ip.split('.')
	return '%02X%02X%02X%02X' % (int(o[0]), int(o[1]), int(o[2]), int(o[3]))


def handler(dn, new, old):
	ucr.load()

	if 'pxe/installer/append' in ucr:
		append = ucr.get('pxe/installer/append')
	else:
		append = 'auto=true priority=critical video=vesa:ywrap,mtrr '
		append += 'vga=%s ' % ucr.get("pxe/installer/vga", "788")
		append += 'initrd=%s ' % (ucr.get('pxe/installer/initrd', 'initrd.gz'),)
		if ucr.is_true('pxe/installer/quiet', False):
			append += 'quiet '
		append += 'loglevel=%s ' % ucr.get('pxe/installer/loglevel', '0')
		if new.get('univentionServerInstallationProfile'):
			append += 'url=http://%s.%s/installer/./%s ' % (ucr.get('hostname'), ucr.get('domainname'), new.get('univentionServerInstallationProfile')[0])

	pxeconfig = '''# Perform a profile installation by default
PROMPT 0
TIMEOUT 100
DEFAULT linux
%(additional_options)s
LABEL linux
        kernel %(kernel)s
        append %(append)s
''' % {
		'kernel': ucr.get('pxe/installer/kernel', 'linux'),
		'append': append,
		'additional_options': new.get('univentionServerInstallationOption', ''),
		}

	# remove pxe host file
	if old and old.get('aRecord'):
		basename = ip_to_hex(old['aRecord'][0])
		if not basename:
			univention.debug.debug(univention.debug.LISTENER, univention.debug.ERROR, 'PXE: invalid old IP address %s' % old['aRecord'][0])
			return
		filename = os.path.join(pxebase, basename)
		listener.setuid(0)
		try:
			if os.path.exists(filename):
				os.unlink(filename)
		finally:
			listener.unsetuid()

	# create pxe host file(s)
	if new and new.get('aRecord'):
		cn = new['cn'][0]
		univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, 'PXE: writing configuration for host %s' % cn)

		basename = ip_to_hex(new['aRecord'][0])
		if not basename:
			univention.debug.debug(univention.debug.LISTENER, univention.debug.ERROR, 'PXE: invalid new IP address %s' % new['aRecord'][0])
			return
		filename = os.path.join(pxebase, basename)

		if new.get('univentionServerReinstall', [''])[0] == '1':
			listener.setuid(0)
			try:
				with open(filename, 'w') as fd:
					fd.write(pxeconfig)
			finally:
				listener.unsetuid()
