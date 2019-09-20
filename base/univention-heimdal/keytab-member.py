# -*- coding: utf-8 -*-
#
# Univention Heimdal
#  listener script for generating memberserver keytab entry
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
import pwd
import univention.debug as ud
from subprocess import call

server_role = listener.configRegistry['server/role']


name = 'keytab-member'
description = 'Kerberos 5 keytab maintenance for memberserver'
filter = (
	'(&'
	'(objectClass=krb5Principal)'
	'(objectClass=krb5KDCEntry)'
	'(krb5KeyVersionNumber=*)'
	'(objectClass=univentionMemberServer)'
	')'
)


def handler(dn, new, old):
	if not new.get('krb5Key'):
		return

	if server_role == 'domaincontroller_master':
		listener.setuid(0)
		try:
			if old:
				cn = old['cn'][0]
				ud.debug(ud.LISTENER, ud.PROCESS, 'Purging krb5.keytab of %s' % (cn,))
				ktab = '/var/lib/univention-heimdal/%s' % (cn,)
				try:
					os.unlink(ktab)
				except EnvironmentError:
					pass
			if new:
				cn = new['cn'][0]
				ud.debug(ud.LISTENER, ud.PROCESS, 'Generating krb5.keytab for %s' % (cn,))
				ktab = '/var/lib/univention-heimdal/%s' % (cn,)
				# FIXME: otherwise the keytab entry is duplicated
				call(['kadmin', '-l', 'ext', '--keytab=%s' % (ktab,), new['krb5PrincipalName'][0]])
				try:
					userID = pwd.getpwnam('%s$' % cn)[2]
					os.chown(ktab, userID, 0)
					os.chmod(ktab, 0o660)
				except (KeyError, EnvironmentError):
					pass
		finally:
			listener.unsetuid()
