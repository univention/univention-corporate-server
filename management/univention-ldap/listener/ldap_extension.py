# -*- coding: utf-8 -*-
#
# Univention LDAP
"""listener script for ldap schema extensions."""
#
# Copyright 2013-2019 Univention GmbH
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
import univention.debug as ud
import univention.lib.ldap_extension as ldap_extension
import os
import subprocess

name = 'ldap_extension'
description = 'Configure LDAP schema and ACL extensions'
filter = '(|(objectClass=univentionLDAPExtensionSchema)(objectClass=univentionLDAPExtensionACL))'
attributes = []

schema_handler = ldap_extension.UniventionLDAPSchema(listener.configRegistry)
acl_handler = ldap_extension.UniventionLDAPACL(listener.configRegistry)


def handler(dn, new, old):
	"""Handle LDAP schema extensions on Master and Backup"""
	global schema_handler, acl_handler

	if new:
		ocs = new.get('objectClass', [])
	elif old:
		ocs = old.get('objectClass', [])

	if 'univentionLDAPExtensionSchema' in ocs:
		schema_handler.handler(dn, new, old, name=name)
	elif 'univentionLDAPExtensionACL' in ocs:
		acl_handler.handler(dn, new, old, name=name)
	else:
		ud.debug(ud.LISTENER, ud.ERROR, '%s: Undetermined error: unknown objectclass: %s.' % (name, ocs))


def postrun():
	"""Restart LDAP server Master and mark new extension objects active"""
	global schema_handler, acl_handler

	server_role = listener.configRegistry.get('server/role')
	if not server_role == 'domaincontroller_master':
		if not acl_handler._todo_list:
			# In case of schema changes only restart slapd on Master
			return
		# Only set active flags on Master
		schema_handler._todo_list = []
		acl_handler._todo_list = []

	slapd_running = not subprocess.call(['pidof', 'slapd'])
	initscript = '/etc/init.d/slapd'
	if os.path.exists(initscript) and slapd_running:
		listener.setuid(0)
		try:
			if schema_handler._do_reload or acl_handler._do_reload:
				ud.debug(ud.LISTENER, ud.PROCESS, '%s: Reloading LDAP server.' % (name,))
				for handler_object in (schema_handler, acl_handler,):
					handler_object._do_reload = False
				p = subprocess.Popen(
					[initscript, 'graceful-restart'], close_fds=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
				stdout, stderr = p.communicate()
				if p.returncode != 0:
					ud.debug(ud.LISTENER, ud.ERROR, '{}: LDAP server restart returned {} {} ({}).'.format(name, stderr, stdout, p.returncode))
					for handler_object in (schema_handler, acl_handler,):
						if handler_object._todo_list:
							for object_dn in handler_object._todo_list:
								ldap_extension.set_handler_message(name, object_dn, 'LDAP server restart returned {} {} ({}).'.format(stderr, stdout, p.returncode))
					return

			# Only set active flags on Master
			if server_role == 'domaincontroller_master':
				for handler_object in (schema_handler, acl_handler,):
					handler_object.mark_active(handler_name=name)
		finally:
			listener.unsetuid()
