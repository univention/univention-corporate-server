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
import tempfile
import datetime
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
	global __todo_list, __do_reload

	if not listener.configRegistry.get('ldap/server/type') == 'master':
		return

	if new:
		if not 'univentionLDAPExtensionPackageVersion' in new:
			return

		if old:	## check for trivial change
			diff_keys = [ key for key in new.keys() if new.get(key) != old.get(key)  and key not in ('entryCSN', 'modifyTimestamp')]
			if diff_keys == ['univentionLDAPSchemaActive']:
				ud.debug(ud.LISTENER, ud.INFO, '%s: LDAP ACL extension %s: activation status changed.' % (name, new['cn'][0]))
				return
		
		new_schema_data = new.get('univentionLDAPSchemaData')[0]
		try:
			new_schema = zlib.decompress(new_schema_data, 16+zlib.MAX_WBITS)
		except TypeError:
			ud.debug(ud.LISTENER, ud.ERROR, '%s: Error uncompressing data of object %s.' % (name, dn))
			return

		new_filename = os.path.join(BASEDIR, new.get('univentionLDAPSchemaFilename')[0])
		listener.setuid(0)
		try:
			backup_filename = None
			if old:
				old_filename = os.path.join(BASEDIR, old.get('univentionLDAPSchemaFilename')[0])
				if os.path.exists(old_filename):
					if new_filename == old_filename:
						try:
							with open(old_filename, 'r') as f:
								file_hash = hashlib.sha256(f.read()).hexdigest()
						except IOError:
							file_hash = None
						
						new_hash = hashlib.sha256(new_schema).hexdigest()
						if new_hash == file_hash:
							ud.debug(ud.LISTENER, ud.INFO, '%s: Schema file %s unchanged.' % (name, old_filename))
							return

					backup_fd, backup_filename = tempfile.mkstemp()
					ud.debug(ud.LISTENER, ud.INFO, '%s: Moving old schema subfile %s to %s.' % (name, old_filename, backup_filename))
					try:
						os.rename(old_filename, backup_filename)
					except IOError:
						ud.debug(ud.LISTENER, ud.WARN, '%s: Error renaming old schema file %s, removing it.' % (name, old_filename))
						os.unlink(old_filename)	## no choice
						backup_filename = None
						os.close(backup_fd)


			if not os.path.isdir(BASEDIR):
				if os.path.exists(BASEDIR):
					ud.debug(ud.LISTENER, ud.WARN, '%s: Directory name %s occupied, renaming blocking file.' % (name, BASEDIR))
					os.rename(BASEDIR, "%s.bak" % BASEDIR)
				ud.debug(ud.LISTENER, ud.INFO, '%s: Create directory %s.' % (name, BASEDIR))
				os.makedirs(BASEDIR, 0755)

			try:
				ud.debug(ud.LISTENER, ud.INFO, '%s: Writing new LDAP schema file %s.' % (name, new_filename))
				with open(new_filename, 'w') as f:
					f.write(new_schema)
			except IOError:
				ud.debug(ud.LISTENER, ud.ERROR, '%s: Error writing schema file %s.' % (name, new_filename))
				return

			ucr = ConfigRegistry()
			ucr.load()
			ucr_handlers = configHandlers()
			ucr_handlers.load()
			ucr_handlers.commit(ucr, ['/etc/ldap/slapd.conf'])

			p = subprocess.Popen(['/usr/sbin/slapschema', ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=True)
			stdout, stderr = p.communicate()
			if p.returncode != 0:
				ud.debug(ud.LISTENER, ud.ERROR, '%s: LDAP schema validation failed:\n%s.' % (name, stdout))
				## Revert changes
				ud.debug(ud.LISTENER, ud.ERROR, '%s: Removing new LDAP schema fragement %s.' % (name, new_filename))
				os.unlink(new_filename)
				if backup_filename:
					ud.debug(ud.LISTENER, ud.ERROR, '%s: Restoring previous LDAP schema %s.' % (name, old_filename))
					try:
						os.rename(backup_filename, old_filename)
						os.close(backup_fd)
					except IOError:
						ud.debug(ud.LISTENER, ud.ERROR, '%s: Error reverting to old schema file %s.' % (name, old_filename))
				## Commit and exit
				ucr_handlers.commit(ucr, ['/etc/ldap/slapd.conf'])
				return

			ud.debug(ud.LISTENER, ud.INFO, '%s: LDAP schema validation successful.' % (name,))
			if backup_filename:
				ud.debug(ud.LISTENER, ud.INFO, '%s: Removing backup of old schema file %s.' % (name, backup_filename))
				os.unlink(backup_filename)
				os.close(backup_fd)

			__todo_list.append(dn)
			__do_reload = True

		finally:
			listener.unsetuid()
	elif old:
		old_filename = os.path.join(BASEDIR, old.get('univentionLDAPSchemaFilename')[0])
		if os.path.exists(old_filename):
			listener.setuid(0)
			try:
				backup_fd, backup_filename = tempfile.mkstemp()
				ud.debug(ud.LISTENER, ud.INFO, '%s: Moving old schema subfile %s to %s.' % (name, old_filename, backup_filename))
				try:
					os.rename(old_filename, backup_filename)
				except IOError:
					ud.debug(ud.LISTENER, ud.WARN, '%s: Error renaming old schema file %s, leaving it untouched.' % (name, old_filename))
					os.close(backup_fd)
					return

				ucr = ConfigRegistry()
				ucr.load()
				ucr_handlers = configHandlers()
				ucr_handlers.load()
				ucr_handlers.commit(ucr, ['/etc/ldap/slapd.conf'])

				p = subprocess.Popen(['/usr/sbin/slapschema', ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=True)
				stdout, stderr = p.communicate()
				if p.returncode != 0:
					ud.debug(ud.LISTENER, ud.WARN, '%s: LDAP schema validation fails without %s:\n%s.' % (name, old_filename, stdout))
					ud.debug(ud.LISTENER, ud.WARN, '%s: Restoring %s.' % (name, old_filename))
					## Revert changes
					try:
						with open(backup_filename, 'r') as original:
							file_data = original.read()
						with open(old_filename, 'w') as target_file:
							target_file.write("### %s: Leftover of removed settings/ldapschema\n" % (datetime.datetime.now(), ) + file_data)
						os.unlink(backup_filename)
						os.close(backup_fd)
					except IOError:
						ud.debug(ud.LISTENER, ud.ERROR, '%s: Error reverting removal of %s.' % (name, old_filename))
					## Commit and exit
					ucr_handlers.commit(ucr, ['/etc/ldap/slapd.conf'])
					return

				ud.debug(ud.LISTENER, ud.INFO, '%s: LDAP schema validation successful, removing backup of old schema file %s.' % (name, backup_filename))
				os.unlink(backup_filename)
				os.close(backup_fd)

				__do_reload = True
				if dn in __todo_list:
					__todo_list = [ x for x in __todo_list if x != dn ]
					if not __todo_list:
						__do_reload = False

			finally:
				listener.unsetuid()

def postrun():
	"""Restart LDAP server Master and mark new schema extension objects active"""
	global __todo_list, __do_reload

	if not listener.configRegistry.get('server/role') == 'domaincontroller_master':
		return

	initscript='/etc/init.d/slapd'
	if os.path.exists(initscript):
		listener.setuid(0)
		try:
			if __do_reload:
				ud.debug(ud.LISTENER, ud.INFO, '%s: Reloading LDAP server.' % (name,) )
				p = subprocess.Popen([initscript, 'graceful-restart'], close_fds=True)
				p.wait()
				__do_reload = False
				if p.returncode != 0:
					ud.debug(ud.LISTENER, ud.ERROR, '%s: LDAP server restart returned %s.' % (name, p.returncode))
					return

			lo, ldap_position = udm_uldap.getAdminConnection()
			udm_settings_ldapschema = udm_modules.get('settings/ldapschema')
			udm_modules.init(lo, ldap_position, udm_settings_ldapschema)

			failed_list = []
			for object_dn in __todo_list:
				try:
					schema_object = udm_settings_ldapschema.object(None, lo, ldap_position, object_dn)
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


