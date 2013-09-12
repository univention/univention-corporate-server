# -*- coding: utf-8 -*-
#
# Univention Directory Manager
"""listener script for UDM extension modules."""
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
import apt
import exceptions

name = 'udm_extension'
description = 'Handle UDM module, hook an syntax extensions'
filter = '(|(objectClass=univentionUDMModule)(objectClass=univentionUDMHook)(objectClass=univentionUDMSyntax))'
attributes = []

PYSHARED_DIR = '/usr/share/pyshared/'
PYMODULES_DIR = '/usr/lib/pymodules/'

class moduleCreationFailed(exceptions.Exception):
	message='Module creation failed.'

def create_pyshared_moduledir(target_subdir, module_directory):
	if not module_directory:
		return

	if module_directory.startswith('/'):
		raise moduleCreationFailed, 'Module directory must not be absolute: %s' % (module_directory, )

	parent_dir = os.path.dirname(module_directory)
	if parent_dir and not os.path.exists(os.path.join(PYSHARED_DIR, target_subdir, parent_dir)):
		create_pyshared_moduledir(target_subdir, parent_dir)
	else:
		targetpath = os.path.join(PYSHARED_DIR, target_subdir, module_directory)
		if not os.path.isdir(targetpath):
			try:
				os.mkdir(targetpath)
			except OSError as e:
				raise moduleCreationFailed, 'Directory creation of %s failed: %s.' % (targetpath, e)

		python_init_filename = os.path.join(targetpath,'__init__.py')
		if not os.path.exists(python_init_filename):
			open(python_init_filename, 'a').close()

def install_pyshared_file(target_subdir, target_filename, data):
	"""Install a public python module file"""
	relative_filename = os.path.join(target_subdir, target_filename)
	if not relative_filename:
		ud.debug(ud.LISTENER, ud.ERROR, '%s: No python file to install.' % (name, relative_filename))
		return False

	if relative_filename.startswith('/'):
		ud.debug(ud.LISTENER, ud.ERROR, '%s: Module path must not be absolute: %s.' % (name, relative_filename))
		return False

	try:
		create_pyshared_moduledir(target_subdir, os.path.dirname(target_filename))
	except moduleCreationFailed as e:
		ud.debug(ud.LISTENER, ud.ERROR, '%s: %s' % (name, e))
		return False

	filename = os.path.join(PYSHARED_DIR, target_subdir, relative_filename)
	try:
		with open(filename, 'r') as f:
			file_hash = hashlib.sha256(f.read()).hexdigest()
	except IOError:
		file_hash = None

	if file_hash and file_hash == hashlib.sha256(data).hexdigest():
		ud.debug(ud.LISTENER, ud.INFO, '%s: data %s unchanged.' % (name, filename))
		return True
	else:
		try:
			with open(filename, 'w') as f:
				f.write(data)
			ud.debug(ud.LISTENER, ud.INFO, '%s: %s installed.' % (name, relative_filename))
			return True
		except Exception, e:
			ud.debug(ud.LISTENER, ud.ERROR, '%s: Writing new data to %s failed: %s.' % (name, filename, e))
			return False

def create_pymodules_moduledir(pymodules_version_path, target_subdir, module_directory):
	if not module_directory:
		return

	if module_directory.startswith('/'):
		raise moduleCreationFailed, 'Module directory must not be absolute: %s' % (module_directory, )

	parent_dir = os.path.dirname(module_directory)
	if parent_dir and not os.path.exists(os.path.join(pymodules_version_path, target_subdir, parent_dir)):
		create_pymodules_moduledir(pymodules_version_path, target_subdir, parent_dir)
	else:
		targetpath = os.path.join(pymodules_version_path, target_subdir, module_directory)
		if not os.path.isdir(targetpath):
			try:
				os.mkdir(targetpath)
			except OSError as e:
				raise moduleCreationFailed, 'Directory creation of %s failed: %s.' % (targetpath, e)

		linkname = os.path.join(targetpath, '__init__.py')
		filename = os.path.join(PYSHARED_DIR, target_subdir, module_directory, '__init__.py')
		if os.path.lexists(linkname):
			if os.path.exists(linkname) and os.path.realpath(linkname) == filename:
					return
			else:
				os.unlink(linkname)
		try:
			os.symlink(filename, linkname)
		except OSError, e:
			raise moduleCreationFailed, 'Symlink creation of %s failed: %s.' % (linkname, e)

def create_pymodules_links(target_subdir, target_filename):
	links_created = 0
	is_default_link_present = False

	p = subprocess.Popen(['/usr/bin/pyversions', '-d'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	(stdout, stderr) = p.communicate()
	default_python_version = stdout.strip()

	p = subprocess.Popen(['/usr/bin/pyversions', '-i'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	(stdout, stderr) = p.communicate()
	pyversions_list = stdout.strip().split(' ')

	relative_filename = os.path.join(target_subdir, target_filename)
	for pyversion in pyversions_list:
		pymodules_version_path = os.path.join(PYMODULES_DIR, pyversion)
		if os.path.isdir(pymodules_version_path):
			try:
				create_pymodules_moduledir(pymodules_version_path, target_subdir, os.path.dirname(target_filename))
			except moduleCreationFailed as e:
				ud.debug(ud.LISTENER, ud.ERROR, '%s: %s' % (name, e))

			linkname = os.path.join(pymodules_version_path, relative_filename)
			filename = os.path.join(PYSHARED_DIR, relative_filename)
			try:
				os.symlink(filename, linkname)
				links_created += 1
				if pyversion == default_python_version:
					is_default_link_present = True
			except OSError, e:
				ud.debug(ud.LISTENER, ud.ERROR, '%s: Symlink creation of %s failed: %s.' % (name, linkname, e))
	if links_created:
		ud.debug(ud.LISTENER, ud.INFO, '%s: symlinks to %s created.' % (name, relative_filename))

	return is_default_link_present


def install_python_file(target_subdir, relative_filename, data):
	"""Install and link a public python module file"""

	if install_pyshared_file(target_subdir, relative_filename, data) and create_pymodules_links(target_subdir, relative_filename):
		return True
	else:
		return False

def remove_python_file(target_subdir, target_filename):
	"""Unlink and remove a public python module file"""
	relative_filename = os.path.join(target_subdir, target_filename)
	if not target_filename:
		ud.debug(ud.LISTENER, ud.ERROR, '%s: No python file to remove.' % (name, ))
		return False

	filename = os.path.join(PYSHARED_DIR, relative_filename)
	relative_basedir = os.path.dirname(relative_filename)

	links_removed = 0
	for entry in os.listdir(PYMODULES_DIR):
		pyversion_path = os.path.join(PYMODULES_DIR, entry)
		if os.path.isdir(pyversion_path):
			pymodules_target_dir = os.path.join(pyversion_path, relative_basedir)
			linkname = os.path.join(pyversion_path, relative_filename)
			if os.path.lexists(linkname):
				try:
					os.unlink(linkname)
					links_removed += 1
				except OSError, e:
					ud.debug(ud.LISTENER, ud.ERROR, '%s: Removal of symlink %s failed: %s.' % (name, linkname, e))
	if links_removed:
		ud.debug(ud.LISTENER, ud.INFO, '%s: links to %s removed.' % (name, relative_filename))
	
	if os.path.isfile(filename):
		## Only remove the file if it was not shipped as part of a debian package.
		p = subprocess.Popen(['dpkg', '-S', filename], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
		p.wait()
		if p.returncode != 0:
			try:
				os.unlink(filename)
				ud.debug(ud.LISTENER, ud.INFO, '%s: %s removed.' % (name, relative_filename))
			except OSError, e:
				ud.debug(ud.LISTENER, ud.ERROR, '%s: Removal of %s failed: %s.' % (name, filename, e))

	if links_removed:
		return True
	else:
		return False


def handler(dn, new, old):
	"""Handle UDM extension modules"""

	if new:
		ocs = new.get('objectClass', [])

		univentionUCSVersionStart = new.get('univentionUCSVersionStart', [None])[0]
		univentionUCSVersionEnd = new.get('univentionUCSVersionEnd', [None])[0]
		current_UCR_version = "%s-%s" % ( listener.configRegistry.get('version/version'), listener.configRegistry.get('version/patchlevel') )
		if univentionUCSVersionStart and current_UCR_version < univentionUCSVersionStart:
			ud.debug(ud.LISTENER, ud.INFO, '%s: extension %s requires at least UCR version %s.' % (name, new['cn'][0], univentionUCSVersionStart))
			new=None
		elif univentionUCSVersionEnd and current_UCR_version >= univentionUCSVersionEnd:
			ud.debug(ud.LISTENER, ud.INFO, '%s: extension %s specifies compatibility only up to UCR version %s.' % (name, new['cn'][0], univentionUCSVersionEnd))
			new=None
	elif old:
		ocs = old.get('objectClass', [])

	if 'univentionUDMModule' in ocs:
		objectclass = 'univentionUDMModule'
		udm_module_name = 'settings/udm_module'
		target_subdir = 'univention/admin/handlers'
	elif 'univentionUDMHook' in ocs:
		objectclass = 'univentionUDMHook'
		udm_module_name = 'settings/udm_hook'
		target_subdir = 'univention/admin/hooks.d'
	elif 'univentionUDMSyntax' in ocs:
		objectclass = 'univentionUDMSyntax'
		udm_module_name = 'settings/udm_syntax'
		target_subdir = 'univention/admin/syntax.d'
	else:
		ud.debug(ud.LISTENER, ud.ERROR, '%s: Undetermined error: unknown objectclass: %s.' % (name, ocs))

	if new:
		new_version = new.get('univentionOwnedByPackageVersion', [None])[0]
		if not new_version:
			return

		new_pkgname = new.get('univentionOwnedByPackage', [None])[0]
		if not new_pkgname:
			return

		if old:	## check for trivial changes
			diff_keys = [ key for key in new.keys() if new.get(key) != old.get(key)  and key not in ('entryCSN', 'modifyTimestamp')]
			if diff_keys == ['%sActive' % objectclass]:
				ud.debug(ud.LISTENER, ud.INFO, '%s: %s: activation status changed.' % (name, new['cn'][0]))
				return
			elif diff_keys == ['univentionAppIdentifier']:
				ud.debug(ud.LISTENER, ud.INFO, '%s: %s: App identifier changed.' % (name, new['cn'][0]))
				return

			if new_pkgname == old.get('univentionOwnedByPackage', [None])[0]:
				old_version = old.get('univentionOwnedByPackageVersion', ['0'])[0]
				rc = apt.apt_pkg.version_compare(new_version, old_version)
				if rc != 1:
					if not rc in (1, 0, -1):
						ud.debug(ud.LISTENER, ud.ERROR, '%s: Package version comparison to old version failed (%s), skipping update.' % (name, old_version))
					else:
						ud.debug(ud.LISTENER, ud.WARN, '%s: New version is not higher than version of old object (%s), skipping update.' % (name, old_version))
					return
		

		## ok, basic checks passed, handle the data
		try:
			new_object_data = zlib.decompress(new.get('%sData' % objectclass)[0], 16+zlib.MAX_WBITS)
		except TypeError:
			ud.debug(ud.LISTENER, ud.ERROR, '%s: Error uncompressing data of object %s.' % (name, dn))
			return

		new_relative_filename = new.get('%sFilename' % objectclass)[0]
		listener.setuid(0)
		try:
			if not install_python_file(target_subdir, new_relative_filename, new_object_data):
				return
		finally:
			listener.unsetuid()

	elif old:

		## ok, basic checks passed, handle the change
		old_relative_filename = old.get('%sFilename' % objectclass)[0]
		listener.setuid(0)
		try:
			remove_python_file(target_subdir, old_relative_filename)
		finally:
			listener.unsetuid()

	### Kill running univention-cli-server and mark new extension object active

	listener.setuid(0)
	try:
		ud.debug(ud.LISTENER, ud.INFO, '%s: Terminating running univention-cli-server processes.' % (name,) )
		p = subprocess.Popen(['pkill', '-f', 'univention-cli-server'], close_fds=True)
		p.wait()
		if p.returncode != 0:
			ud.debug(ud.LISTENER, ud.ERROR, '%s: Termination of univention-cli-server processes failed: %s.' % (name, p.returncode))

		if new:
			try:
				lo, ldap_position = udm_uldap.getAdminConnection()
				udm_modules.update()
				udm_module = udm_modules.get(udm_module_name)
				udm_modules.init(lo, ldap_position, udm_module)

				try:
					udm_object = udm_module.object(None, lo, ldap_position, dn)
					udm_object.open()
					udm_object['active']=True
					udm_object.modify()
				except udm_errors.ldapError, e:
					ud.debug(ud.LISTENER, ud.ERROR, '%s: Error modifying %s: %s.' % (name, dn, e))
				except udm_errors.noObject, e:
					ud.debug(ud.LISTENER, ud.ERROR, '%s: Error modifying %s: %s.' % (name, dn, e))

			except udm_errors.ldapError, e:
				ud.debug(ud.LISTENER, ud.ERROR, '%s: Error accessing UDM: %s' % (name, e))

	finally:
		listener.unsetuid()

