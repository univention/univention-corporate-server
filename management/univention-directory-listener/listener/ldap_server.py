# -*- coding: utf-8 -*-
#
# Univention Directory Listener
"""listener script for setting ldap server."""
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

from __future__ import absolute_import

import listener
import univention.config_registry

import univention.debug as ud
import univention.misc

name = 'ldap_server'
description = 'Update ldap server master list'
filter = '(&(objectClass=univentionDomainController)(|(univentionServerRole=master)(univentionServerRole=backup)))'
attributes = []


def handler(dn, new, old):
	"""Handle change in LDAP."""
	ucr = univention.config_registry.ConfigRegistry()
	ucr.load()

	if ucr['server/role'] == 'domaincontroller_master':
		return

	listener.setuid(0)
	try:
		if 'univentionServerRole' in new:
			try:
				domain = new['associatedDomain'][0]
			except LookupError:
				domain = ucr['domainname']
			add_ldap_server(ucr, new['cn'][0], domain, new['univentionServerRole'][0])
		elif 'univentionServerRole' in old and not new:
			try:
				domain = old['associatedDomain'][0]
			except LookupError:
				domain = ucr['domainname']
			remove_ldap_server(ucr, old['cn'][0], domain, old['univentionServerRole'][0])
	finally:
		listener.unsetuid()


def add_ldap_server(ucr, name, domain, role):
	"""Add LDAP server."""
	ud.debug(ud.LISTENER, ud.INFO, 'LDAP_SERVER: Add ldap_server %s' % name)

	server_name = "%s.%s" % (name, domain)

	if role == 'master':
		old_master = ucr.get('ldap/master')

		changes = ['ldap/master=%s' % server_name]

		if ucr.get('kerberos/adminserver') == old_master:
			changes.append('kerberos/adminserver=%s' % server_name)

		if ucr.get('ldap/server/name') == old_master:
			changes.append('ldap/server/name=%s' % server_name)

		univention.config_registry.handler_set(changes)

	if role == 'backup':
		backup_list = ucr.get('ldap/backup', '').split()
		if server_name not in backup_list:
			backup_list.append(server_name)
			univention.config_registry.handler_set(['ldap/backup=%s' % (' '.join(backup_list),)])


def remove_ldap_server(ucr, name, domain, role):
	"""Remove LDAP server."""
	ud.debug(ud.LISTENER, ud.INFO, 'LDAP_SERVER: Remove ldap_server %s' % name)

	server_name = "%s.%s" % (name, domain)

	if role == 'backup':
		backup_list = ucr.get('ldap/backup', '').split()
		if server_name in backup_list:
			backup_list.remove(server_name)
			univention.config_registry.handler_set(['ldap/backup=%s' % (' '.join(backup_list),)])
