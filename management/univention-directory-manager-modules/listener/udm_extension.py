# -*- coding: utf-8 -*-
#
# Univention Directory Manager
"""listener script for UDM extension modules."""
#
# Copyright 2013-2015 Univention GmbH
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
import os
import univention.admin.uldap as udm_uldap
import univention.admin.modules as udm_modules
import univention.admin.uexceptions as udm_errors
from univention.lib.ucs import UCS_Version
from univention.lib.umc_module import UMC_ICON_BASEDIR, imagecategory_of_buffer, default_filename_suffix_for_mime_type
import subprocess
import bz2
import tempfile
import datetime
import apt

name = 'udm_extension'
description = 'Handle UDM module, hook an syntax extensions'
filter = '(|(objectClass=univentionUDMModule)(objectClass=univentionUDMHook)(objectClass=univentionUDMSyntax))'
attributes = []

PYSHARED_DIR = '/usr/share/pyshared/'
PYSUPPORT_DIR = '/usr/share/python-support'
LOCALE_BASEDIR = "/usr/share/locale"	## mo files go to /usr/share/locale/<language-tag>/LC_MESSAGES/
MODULE_DEFINTION_BASEDIR = "/usr/share/univention-management-console/modules"	## UMC registration xml files go here

class moduleCreationFailed(Exception):
	default_message='Module creation failed.'
	def __init__(self, message = default_message):
		Exception.__init__(self, message)

class moduleRemovalFailed(Exception):
	default_message = 'Module removal failed.'
	def __init__(self, message = default_message):
		Exception.__init__(self, message)


def handler(dn, new, old):
	"""Handle UDM extension modules"""

	if new:
		ocs = new.get('objectClass', [])

		univentionUCSVersionStart = new.get('univentionUCSVersionStart', [None])[0]
		univentionUCSVersionEnd = new.get('univentionUCSVersionEnd', [None])[0]
		current_UCS_version = "%s-%s" % ( listener.configRegistry.get('version/version'), listener.configRegistry.get('version/patchlevel') )
		if univentionUCSVersionStart and UCS_Version(current_UCS_version) < UCS_Version(univentionUCSVersionStart):
			ud.debug(ud.LISTENER, ud.INFO, '%s: extension %s requires at least UCR version %s.' % (name, new['cn'][0], univentionUCSVersionStart))
			new=None
		elif univentionUCSVersionEnd and UCS_Version(current_UCS_version) > UCS_Version(univentionUCSVersionEnd):
			ud.debug(ud.LISTENER, ud.INFO, '%s: extension %s specifies compatibility only up to and including UCR version %s.' % (name, new['cn'][0], univentionUCSVersionEnd))
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
			diff_keys = [ key for key in new.keys() if new.get(key) != old.get(key)  and key not in ('entryCSN', 'modifyTimestamp', 'modifiersName')]
			if diff_keys == ['%sActive' % objectclass] and new.get('%sActive' % objectclass)[0] == 'TRUE':
				ud.debug(ud.LISTENER, ud.INFO, '%s: %s: activation status changed.' % (name, new['cn'][0]))
				return
			elif diff_keys == ['univentionAppIdentifier']:
				ud.debug(ud.LISTENER, ud.INFO, '%s: %s: App identifier changed.' % (name, new['cn'][0]))
				return

			if new_pkgname == old.get('univentionOwnedByPackage', [None])[0]:
				old_version = old.get('univentionOwnedByPackageVersion', ['0'])[0]
				rc = apt.apt_pkg.version_compare(new_version, old_version)
				if not rc > -1:
					ud.debug(ud.LISTENER, ud.WARN, '%s: New version is lower than version of old object (%s), skipping update.' % (name, old_version))
					return

		## ok, basic checks passed, handle the data
		try:
			new_object_data = bz2.decompress(new.get('%sData' % objectclass)[0])
		except TypeError:
			ud.debug(ud.LISTENER, ud.ERROR, '%s: Error uncompressing data of object %s.' % (name, dn))
			return

		new_relative_filename = new.get('%sFilename' % objectclass)[0]
		listener.setuid(0)
		try:
			if not install_python_file(objectclass, target_subdir, new_relative_filename, new_object_data):
				return
			if objectclass == 'univentionUDMModule':
				install_messagecatalog(dn, new)
				install_umcregistration(dn, new)
				install_umcicons(dn, new)
		finally:
			listener.unsetuid()

	elif old:

		## ok, basic checks passed, handle the change
		old_relative_filename = old.get('%sFilename' % objectclass)[0]
		listener.setuid(0)
		try:
			remove_python_file(objectclass, target_subdir, old_relative_filename)
			if objectclass == 'univentionUDMModule':
				remove_umcicons(dn, old)
				remove_umcregistration(dn, old)
				remove_messagecatalog(dn, old)
		finally:
			listener.unsetuid()

	### Kill running univention-cli-server and mark new extension object active

	listener.setuid(0)
	try:
		if new:
			if not listener.configRegistry.get('server/role') == 'domaincontroller_master':
				## Only set active flag on Master
				return

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


##### helper functions #####
## pretty much all of the functions below mimic update-python-modules, additionally creating the __init__.py module file if nexessary
def install_python_file(objectclass, target_subdir, relative_filename, data):
	"""Install and link a python module file"""

	init_file_list = []
	if install_pyshared_file(target_subdir, relative_filename, data, init_file_list) and create_pymodules_links(objectclass, target_subdir, relative_filename, init_file_list):
		return True
	else:
		return False


def remove_python_file(objectclass, target_subdir, target_filename):
	"""Remove pymodules symlinks and compiled files as well as the python module file"""

	if remove_pymodules_links(objectclass, target_subdir, target_filename) and remove_pyshared_file(target_subdir, target_filename):
		return True
	else:
		return False

def install_pyshared_file(target_subdir, target_filename, data, init_file_list):
	"""Install a python module file"""
	## input validation
	relative_filename = os.path.join(target_subdir, target_filename)
	if not relative_filename:
		ud.debug(ud.LISTENER, ud.ERROR, '%s: No python file to install.' % (name,))
		return False

	if relative_filename.startswith('/'):
		ud.debug(ud.LISTENER, ud.ERROR, '%s: Module path must not be absolute: %s.' % (name, relative_filename))
		return False

	## trivial checks passed, go for it
	try:
		_init_file_list = create_python_moduledir(PYSHARED_DIR, target_subdir, os.path.dirname(target_filename))
		if _init_file_list:
			init_file_list.extend(_init_file_list)
	except moduleCreationFailed as e:
		ud.debug(ud.LISTENER, ud.ERROR, '%s: %s' % (name, e))
		return False

	filename = os.path.join(PYSHARED_DIR, relative_filename)
	try:
		with open(filename, 'w') as f:
			f.write(data)
		ud.debug(ud.LISTENER, ud.INFO, '%s: %s installed.' % (name, relative_filename))
		return True
	except Exception, e:
		ud.debug(ud.LISTENER, ud.ERROR, '%s: Writing new data to %s failed: %s.' % (name, filename, e))
		return False


def remove_pyshared_file(target_subdir, target_filename):
	"""Remove pyshared parts of public python module file"""
	## input validation
	relative_filename = os.path.join(target_subdir, target_filename)
	if not relative_filename:
		ud.debug(ud.LISTENER, ud.ERROR, '%s: No python file to remove.' % (name,))
		return False

	if relative_filename.startswith('/'):
		ud.debug(ud.LISTENER, ud.ERROR, '%s: Module path must not be absolute: %s.' % (name, relative_filename))
		return False

	## trivial checks passed, go for it
	filename = os.path.join(PYSHARED_DIR, relative_filename)
	if os.path.isfile(filename):
		## Only remove the file if it was not shipped as part of a debian package.
		p = subprocess.Popen(['dpkg', '-S', filename], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
		p.wait()
		if p.returncode == 0:
			## ok, we should not remove this file
			## but at least check if the __init__.py file should be cleaned up. cleanup_python_moduledir would not do it since $filename is sill there.
			target_path = os.path.dirname(filename)
			skipfiles = (os.path.basename(filename), '__init__.py')
			for entry in os.listdir(target_path):
				if entry not in skipfiles:
					return

			python_init_filename = os.path.join(target_path, '__init__.py')
			if os.path.exists(python_init_filename):
				if  os.path.getsize(python_init_filename) != 0:
					return

			## Only remove the file if it was not shipped as part of a debian package.
			p = subprocess.Popen(['dpkg', '-S', python_init_filename], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
			p.wait()
			if p.returncode != 0:
				try:
					os.unlink(python_init_filename)
					ud.debug(ud.LISTENER, ud.INFO, '%s: %s removed.' % (name, python_init_filename))
				except OSError, e:
					ud.debug(ud.LISTENER, ud.ERROR, '%s: Removal of %s failed: %s.' % (name, python_init_filename, e))
			## return, nothing more to do in this case
			return
		else:
			try:
				os.unlink(filename)
				ud.debug(ud.LISTENER, ud.INFO, '%s: %s removed.' % (name, filename))
			except OSError, e:
				ud.debug(ud.LISTENER, ud.ERROR, '%s: Removal of %s failed: %s.' % (name, filename, e))

	try:
		cleanup_python_moduledir(PYSHARED_DIR, target_subdir, os.path.dirname(target_filename))
	except moduleRemovalFailed as e:
		ud.debug(ud.LISTENER, ud.ERROR, '%s: %s' % (name, e))
		return False


def create_pymodules_links(objectclass, target_subdir, target_filename, init_file_list):
	"""Install the links for a public python module file"""

	p = subprocess.Popen(['/usr/bin/pyversions', '-d'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	(stdout, stderr) = p.communicate()
	default_python_version = stdout.strip()
	if default_python_version.startswith("python"):
		default_python_version = default_python_version[6:]

	relative_filename = os.path.join(target_subdir, target_filename)

	pyshared_content = "pyversions=%s\n\n" % default_python_version
	pyshared_content += "%s\n" % (os.path.join(PYSHARED_DIR, relative_filename),)
	for filename in init_file_list:
		pyshared_content += "%s\n" % (filename,)

	target_filename_parts = os.path.splitext(target_filename)
	if len(target_filename_parts) > 1 and target_filename_parts[-1] == ".py":
		pysupport_filename = ".".join(target_filename_parts[:-1])
	else:
		pysupport_filename = target_filename

	pysupport_filename = '%s_%s.public' % (objectclass, pysupport_filename.replace('/', '_'))
	pysupport_filename = os.path.join(PYSUPPORT_DIR, pysupport_filename)

	with open(pysupport_filename, 'w') as f:
		f.write(pyshared_content)

	try:
		p = subprocess.Popen(['/usr/sbin/update-python-modules', '-p', pysupport_filename], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		(stdout, stderr) = p.communicate()
	except OSError, e:
		ud.debug(ud.LISTENER, ud.ERROR, '%s: update-python-modules -p %s failed: %s.' % (name, pysupport_filename, e))

	if p.returncode == 0:
		ud.debug(ud.LISTENER, ud.INFO, '%s: symlinks to %s created.' % (name, relative_filename))
		return True

	ud.debug(ud.LISTENER, ud.ERROR, '%s: update-python-modules -p %s failed: %s.' % (name, pysupport_filename, stderr))
	return False


def remove_pymodules_links(objectclass, target_subdir, target_filename):
	"""Remove pymodules parts: pyc, pyo, and file itself. Clean up directories in target_filename if empty."""
	## input validation
	relative_filename = os.path.join(target_subdir, target_filename)
	if not relative_filename:
		ud.debug(ud.LISTENER, ud.ERROR, '%s: No python file to remove.' % (name,))
		return False

	if relative_filename.startswith('/'):
		ud.debug(ud.LISTENER, ud.ERROR, '%s: Module path must not be absolute: %s.' % (name, relative_filename))
		return False

	## trivial checks passed, go for it
	target_filename_parts = os.path.splitext(target_filename)
	if len(target_filename_parts) > 1 and target_filename_parts[-1] == ".py":
		pysupport_filename = ".".join(target_filename_parts[:-1])
	else:
		pysupport_filename = target_filename

	pysupport_filename = '%s_%s.public' % (objectclass, pysupport_filename.replace('/', '_'))
	pysupport_filename = os.path.join(PYSUPPORT_DIR, pysupport_filename)

	if os.path.isfile(pysupport_filename):
		try:
			os.unlink(pysupport_filename)
			ud.debug(ud.LISTENER, ud.INFO, '%s: %s removed.' % (name, pysupport_filename))
		except OSError, e:
			ud.debug(ud.LISTENER, ud.ERROR, '%s: Removal of %s failed: %s.' % (name, pysupport_filename, e))

	try:
		p = subprocess.Popen(['/usr/sbin/update-python-modules', '-p'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		(stdout, stderr) = p.communicate()
	except OSError, e:
		ud.debug(ud.LISTENER, ud.ERROR, '%s: update-python-modules -p failed: %s.' % (name, e))

	if p.returncode == 0:
		ud.debug(ud.LISTENER, ud.INFO, '%s: symlinks to %s removed.' % (name, relative_filename))
		return True

	ud.debug(ud.LISTENER, ud.ERROR, '%s: update-python-modules -p failed: %s.' % (name, stderr))
	return False


def create_python_moduledir(python_basedir, target_subdir, module_directory):
	"""create directory and __init__.py (file or link). Recurse for all parent directories in path module_directory"""
	## input validation
	if not module_directory:
		return

	if module_directory.startswith('/'):
		raise moduleCreationFailed, 'Module directory must not be absolute: %s' % (module_directory, )
	target_dir = os.path.join(python_basedir, target_subdir)
	target_path = os.path.join(target_dir, module_directory)
	if not os.path.realpath(target_path).startswith(target_dir):
		raise moduleCreationFailed, 'Target directory %s not below %s' % (module_directory, target_dir)

	## trivial checks passed, go for it
	init_file_list = []
	parent_dir = os.path.dirname(module_directory)
	if parent_dir and not os.path.exists(os.path.join(python_basedir, target_subdir, parent_dir)):
		_init_file_list = create_python_moduledir(python_basedir, target_subdir, parent_dir)
		if _init_file_list:
			init_file_list.extend(_init_file_list)

	if not os.path.isdir(target_path):
		try:
			os.mkdir(target_path)
		except OSError as e:
			raise moduleCreationFailed, 'Directory creation of %s failed: %s.' % (target_path, e)

	python_init_filename = os.path.join(target_path,'__init__.py')
	if not os.path.exists(python_init_filename):
		open(python_init_filename, 'a').close()
	init_file_list.append(python_init_filename)

	return init_file_list


def cleanup_python_moduledir(python_basedir, target_subdir, module_directory):
	"""remove __init__.py and directory from if no other file is in the directory. Recurse for all parent directories in path module_directory"""
	## input validation
	if not module_directory:
		return

	if module_directory.startswith('/'):
		raise moduleRemovalFailed, 'Module directory must not be absolute: %s' % (module_directory, )
	target_dir = os.path.join(python_basedir, target_subdir)
	target_path = os.path.join(target_dir, module_directory)
	if not os.path.realpath(target_path).startswith(target_dir):
		raise moduleCreationFailed, 'Target directory %s not below %s' % (module_directory, target_dir)

	if not os.path.isdir(target_path):
		return

	## trivial checks passed, go for it
	for entry in os.listdir(target_path):
		if os.path.splitext(entry)[0] != '__init__':
			return

	python_init_filename = os.path.join(target_path, '__init__.py')
	if os.path.exists(python_init_filename):
		if os.path.getsize(python_init_filename) != 0:
			return

		if python_basedir == PYSHARED_DIR:
			## Only remove the file if it was not shipped as part of a debian package.
			p = subprocess.Popen(['dpkg', '-S', python_init_filename], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
			p.wait()
			if p.returncode == 0:
				return
		else:
			## remove pyc and pyo
			basename, ext = os.path.splitext(python_init_filename)
			if ext == '.py':
				for ext in ('.pyc', '.pyo'):
					derived_filename = basename + ext
					if os.path.exists(derived_filename):
						os.unlink(derived_filename)

		try:
			os.unlink(python_init_filename)
			ud.debug(ud.LISTENER, ud.INFO, '%s: %s removed.' % (name, python_init_filename))
		except OSError, e:
			ud.debug(ud.LISTENER, ud.ERROR, '%s: Removal of %s failed: %s.' % (name, python_init_filename, e))

	try:
		os.rmdir(target_path)
	except OSError as e:
		raise moduleRemovalFailed, 'Removal of directory %s failed: %s.' % (target_path, e)

	parent_dir = os.path.dirname(module_directory)
	if parent_dir:
		cleanup_python_moduledir(python_basedir, target_subdir, parent_dir)

def install_messagecatalog(dn, attrs):
	translationfile_ldap_attribute = "univentionMessageCatalog"
	translationfile_ldap_attribute_and_tag_prefix = "%s;entry-lang-" % (translationfile_ldap_attribute,)

	values = {}
	for ldap_attribute in attrs.keys():
		if ldap_attribute.startswith(translationfile_ldap_attribute_and_tag_prefix):
			language_tag = ldap_attribute.split(translationfile_ldap_attribute_and_tag_prefix, 1)[1]
			values[language_tag] = attrs.get(ldap_attribute)[0]
	if not values:
		return

	module_name = attrs.get('cn')[0]
	for language_tag, mo_data_binary in values.items():
		targetdir = os.path.join(LOCALE_BASEDIR, language_tag, 'LC_MESSAGES')
		filename = os.path.join(targetdir, "univention-admin-handlers-%s.mo" % (module_name.replace('/', '-'),) )
		if not os.path.exists(targetdir):
			ud.debug(ud.LISTENER, ud.ERROR, '%s: Error writing %s. Parent directory does not exist.' % (name, filename))
			continue
		with open(filename, 'w') as f:
			f.write(mo_data_binary)

def remove_messagecatalog(dn, attrs):
	translationfile_ldap_attribute = "univentionMessageCatalog"
	translationfile_ldap_attribute_and_tag_prefix = "%s;entry-lang-" % (translationfile_ldap_attribute,)

	language_tags = []
	for ldap_attribute in attrs.keys():
		if ldap_attribute.startswith(translationfile_ldap_attribute_and_tag_prefix):
			language_tag = ldap_attribute.split(translationfile_ldap_attribute_and_tag_prefix, 1)[1]
			language_tags.append(language_tag)
	if not language_tags:
		return

	module_name = attrs.get('cn')[0]
	for language_tag in language_tags:
		targetdir = os.path.join(LOCALE_BASEDIR, language_tag, 'LC_MESSAGES')
		filename = os.path.join(targetdir, "univention-admin-handlers-%s.mo" % (module_name.replace('/', '-'),) )
		if not os.path.exists(targetdir):
			ud.debug(ud.LISTENER, ud.ERROR, '%s: Error writing %s. Parent directory does not exist.' % (name, filename))
			continue
		ud.debug(ud.LISTENER, ud.INFO, '%s: Removing %s.' % (name, filename))
		if os.path.exists(filename):
			os.unlink(filename)
		else:
			ud.debug(ud.LISTENER, ud.INFO, '%s: Warning: %s does not exist.' % (name, filename))

def install_umcregistration(dn, attrs):
	compressed_data = attrs.get('univentionUMCRegistrationData', [None])[0]
	if not compressed_data:
		return

	try:
		object_data = bz2.decompress(compressed_data)
	except TypeError:
		ud.debug(ud.LISTENER, ud.ERROR, '%s: Error uncompressing univentionUMCRegistrationData of object %s.' % (name, dn))
		return

	module_name = attrs.get('cn')[0]
	filename = os.path.join(MODULE_DEFINTION_BASEDIR, "udm-%s.xml" % (module_name.replace('/', '-'),))
	if not os.path.exists(MODULE_DEFINTION_BASEDIR):
		ud.debug(ud.LISTENER, ud.ERROR, '%s: Error writing %s. Parent directory does not exist.' % (name, filename))
		return
	with open(filename, 'w') as f:
		f.write(object_data)

def remove_umcregistration(dn, attrs):
	if not attrs.get('univentionUMCRegistrationData'):
		return

	module_name = attrs.get('cn')[0]
	filename = os.path.join(MODULE_DEFINTION_BASEDIR, "udm-%s.xml" % (module_name.replace('/', '-'),))
	ud.debug(ud.LISTENER, ud.INFO, '%s: Removing %s.' % (name, filename))
	if os.path.exists(filename):
		os.unlink(filename)
	else:
		ud.debug(ud.LISTENER, ud.INFO, '%s: Warning: %s does not exist.' % (name, filename))

def install_umcicons(dn, attrs):
	for object_data in attrs.get('univentionUMCIcon', []):
		module_name = attrs.get('cn')[0]
		(mime_type, compression_mime_type, subdir) = imagecategory_of_buffer(object_data)
		targetdir = os.path.join(UMC_ICON_BASEDIR, subdir)

		filename_suffix = default_filename_suffix_for_mime_type(mime_type, compression_mime_type)
		filename = os.path.join(targetdir, "udm-%s%s" % (module_name.replace('/', '-'), filename_suffix))

		if not os.path.exists(targetdir):
			ud.debug(ud.LISTENER, ud.ERROR, '%s: Error writing %s. Parent directory does not exist.' % (name, filename))
			continue
		with open(filename, 'w') as f:
			f.write(object_data)

def remove_umcicons(dn, attrs):
	for object_data in attrs.get('univentionUMCIcon', []):
		module_name = attrs.get('cn')[0]
		(mime_type, compression_mime_type, subdir) = imagecategory_of_buffer(object_data)
		targetdir = os.path.join(UMC_ICON_BASEDIR, subdir)

		filename_suffix = default_filename_suffix_for_mime_type(mime_type, compression_mime_type)
		filename = os.path.join(targetdir, "udm-%s%s" % (module_name.replace('/', '-'), filename_suffix))

		ud.debug(ud.LISTENER, ud.INFO, '%s: Removing %s.' % (name, filename))
		if os.path.exists(filename):
			os.unlink(filename)
		else:
			ud.debug(ud.LISTENER, ud.INFO, '%s: Warning: %s does not exist.' % (name, filename))
