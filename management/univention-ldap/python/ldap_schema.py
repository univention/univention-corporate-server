# -*- coding: utf-8 -*-
#
# Univention LDAP
"""listener script for ldap schema extensions."""
#
# Copyright 2013-2014 Univention GmbH
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

__package__ = ''	# workaround for PEP 366
import listener
from univention.config_registry import configHandlers, ConfigRegistry
import univention.debug as ud
import hashlib
import os
import univention.admin.uldap as udm_uldap
import univention.admin.modules as udm_modules
import univention.admin.uexceptions as udm_errors
import subprocess
import zlib
udm_modules.update()

name = 'ldap_schema'
description = 'Configure LDAP schema extensions'
filter = '(objectClass=univentionLDAPExtensionSchema)'
attributes = []

BASEDIR = '/var/lib/univention-ldap/local-schema'

__do_reload = False
__todo_list = []

def handler(dn, new, old):
	"""Handle LDAP schema extensions on DC Master and DC Backup"""

	if not listener.configRegistry.get('ldap/server/type') == 'master':
		return

	if new:
		if not 'univentionLDAPExtensionPackageVersion' in new:
			return

		new_schema_data = new.get('univentionLDAPSchemaData')[0]
		try:
			new_schema = zlib.decompress(new_schema_data, 16+zlib.MAX_WBITS)
			new_hash = hashlib.sha256(new_schema).hexdigest()
		except TypeError:
			ud.debug(ud.LISTENER, ud.ERROR, '%s: Error uncompressing and hashing data of object %s.' % (name, dn))
			return

		if not os.path.isdir(BASEDIR):
			if os.path.exists(BASEDIR):
				ud.debug(ud.LISTENER, ud.WARN, '%s: Directory name %s occupied, renaming blocking file.' % (name, BASEDIR))
				os.rename(BASEDIR, "%s.bak" % BASEDIR)
			ud.debug(ud.LISTENER, ud.INFO, '%s: Create directory %s.' % (name, BASEDIR))
			os.makedirs(BASEDIR, 0755)

		new_filename = os.path.join(BASEDIR, new.get('univentionLDAPSchemaFilename')[0])
		listener.setuid(0)
		try:
			backup_file = None
			if old:
				old_filename = os.path.join(BASEDIR, old.get('univentionLDAPSchemaFilename')[0])
				if new_filename != old_filename:
					backup_file = '%s.disabled' % old_filename
					try:
						os.rename(old_filename, backup_file)
					except IOError:
						ud.debug(ud.LISTENER, ud.WARN, '%s: Error renaming old schema file %s, removing it directly.' % (name, old_filename))
						os.unlink(old_filename)	## no choice

			try:
				with open(new_filename, 'r') as f:
					file_hash = hashlib.sha256(f.read()).hexdigest()
			except IOError:
				file_hash = None
			
			if new_hash == file_hash:
				ud.debug(ud.LISTENER, ud.INFO, '%s: Schema file %s unchanged.' % (name, new_filename))
				return

			try:
				with open(new_filename, 'w') as f:
					f.write(new_schema)
			except IOError:
				ud.debug(ud.LISTENER, ud.ERROR, '%s: Error writing schema file %s.' % (name, new_filename))
				return

			if backup_file and os.path.exists(backup_file):
				ud.debug(ud.LISTENER, ud.INFO, '%s: Removing backup of old schema file %s.' % (name, backup_file))
				os.unlink(backup_file)

			ucr = ConfigRegistry()
			ucr.load()
			ucr_handlers.commit(ucr, ['/etc/ldap/slapd.conf'])

			global __todo_list, __do_reload
			__todo_list.append(new['dn'])
			__do_reload = True

		finally:
			listener.unsetuid()

def postrun():
	"""Restart LDAP server Master and mark new schema extension objects active"""

	if not listener.configRegistry.get('server/role') == 'domaincontroller_master':
		return

	global __todo_list, __do_reload

	initscript='/etc/init.d/slapd'
	if os.path.exists(initscript):
		listener.setuid(0)
		try:
			if __do_reload:
				ud.debug(ud.LISTENER, ud.INFO, '%s: Reloading LDAP server.' % (name,) )
				p = subprocess.Popen([initscript, 'graceful-restart'], close_fds=True)
				p.wait()
				if p.returncode != 0:
					ud.debug(ud.LISTENER, ud.ERROR, '%s: LDAP server restart returned %s.' % (name, p.returncode))
					return

			lo, ldap_position = udm_uldap.getAdminConnection()
			udm_settings_ldapschema = udm_modules.get('settings/ldapschema')
			udm_modules.init(lo, ldap_position, udm_settings_ldapschema)

			failed_list = []
			for object_dn in __todo_list:
				try:
					schema_object = module_groups_group.object(None, lo, ldap_position, object_dn)
					schema_object.open()
					schema_object['active']=True
					schema_object.modify()
				except udm_errors.ldapError, e:
					ud.debug(ud.LISTENER, ud.ERROR, '%s: Error modifying %s: %s, keeping on todo list.' % (name, object_dn, e))
					failed_list.append(object_dn)
			__todo_list = failed_list

		except udm_errors.ldapError, e:
			ud.debug(ud.LISTENER, ud.ERROR, '%s: Error accessing UDM: %s' % (name, e))

		finally:
			listener.unsetuid()


