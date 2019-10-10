# -*- coding: utf-8 -*-
#
# Univention Management Console
# Listener module to set save all UMC service providers in UCR
#
# Copyright 2015-2019 Univention GmbH
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

from __future__ import absolute_import

import listener

from univention.config_registry import handler_set, handler_unset
import univention.debug as ud
import os
import subprocess

name = 'umc-service-providers'
description = 'Manage umc/saml/trusted/sp/* variable'
filter = '(|(objectClass=univentionDomainController)(objectClass=univentionMemberServer))'
attributes = ['univentionService', 'cn', 'associatedDomain']

__changed_trusted_sp = False


def handler(dn, new, old):
	global __changed_trusted_sp
	listener.setuid(0)
	try:
		try:
			fqdn = '%s.%s' % (new['cn'][0], new['associatedDomain'][0])
		except (KeyError, IndexError):
			return
		umc_service_active = 'Univention Management Console' in new.get('univentionService', [])
		umc_service_was_active = 'Univention Management Console' in old.get('univentionService', [])
		domain_added = 'associatedDomain' in new and 'associatedDomain' not in old and umc_service_active
		if umc_service_active and (domain_added or not umc_service_was_active):
			handler_set(['umc/saml/trusted/sp/%s=%s' % (fqdn, fqdn)])
			__changed_trusted_sp = True
		elif umc_service_was_active and not umc_service_active:
			handler_unset(['umc/saml/trusted/sp/%s' % (fqdn,)])
			__changed_trusted_sp = True

	finally:
		listener.unsetuid()


def postrun():
	global __changed_trusted_sp

	if __changed_trusted_sp:
		__changed_trusted_sp = False
		slapd_running = not subprocess.call(['pidof', 'slapd'])
		initscript = '/etc/init.d/slapd'
		if os.path.exists(initscript) and slapd_running:
			listener.setuid(0)
			try:
				ud.debug(ud.LISTENER, ud.PROCESS, '%s: Reloading LDAP server.' % (name,))
				p = subprocess.Popen([initscript, 'graceful-restart'], close_fds=True)
				p.wait()
				if p.returncode != 0:
					ud.debug(ud.LISTENER, ud.ERROR, '%s: LDAP server restart returned %s.' % (name, p.returncode))
			finally:
				listener.unsetuid()
