# -*- coding: utf-8 -*-
#
# Univention Directory Manager
"""listener script for UDM extension modules."""
#
# Copyright 2013-2021 Univention GmbH
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

import os
import bz2
import traceback
import subprocess

import apt

import listener

import univention.debug as ud
import univention.admin.uldap as udm_uldap
import univention.admin.modules as udm_modules
import univention.admin.uexceptions as udm_errors
from univention.lib.ldap_extension import safe_path_join
from univention.lib.ucs import UCS_Version
from univention.lib.umc_module import UMC_ICON_BASEDIR, imagecategory_of_buffer, default_filename_suffix_for_mime_type

name = 'udm_extension'
description = 'Handle UDM module, hook and syntax extensions'
filter = '(|(objectClass=univentionUDMModule)(objectClass=univentionUDMHook)(objectClass=univentionUDMSyntax))'
attributes = []

PYSHARED_DIR = '/usr/share/pyshared/'
PYTHON_DIR = '/usr/lib/python2.7/dist-packages/'
PYSUPPORT_DIR = '/usr/share/python-support'
LOCALE_BASEDIR = "/usr/share/locale"  # mo files go to /usr/share/locale/<language-tag>/LC_MESSAGES/
LOCALE_BASEDIR_UMC = "/usr/share/univention-management-console/i18n"  # umc translation files go to /usr/share/univention-management-console/i18n/<language-tag>/<UMCModuleID>.mo
MODULE_DEFINTION_BASEDIR = "/usr/share/univention-management-console/modules"  # UMC registration xml files go here
EXTEND_PATH = "__path__ = __import__('pkgutil').extend_path(__path__, __name__)\n"  # do not change ever!


class moduleCreationFailed(Exception):
	default_message = 'Module creation failed.'

	def __init__(self, message=default_message):
		Exception.__init__(self, message)


class moduleRemovalFailed(Exception):
	default_message = 'Module removal failed.'

	def __init__(self, message=default_message):
		Exception.__init__(self, message)


def initialize():
	listener.setuid(0)
	try:
		migrate_to_dh_python()
	finally:
		listener.unsetuid()


def migrate_to_dh_python():
	ud.debug(ud.LISTENER, ud.WARN, 'Migrating all UDM extensions from python-support to dh-python')
	lo, po = udm_uldap.getMachineConnection()
	for dn, attrs in lo.search('(|(objectClass=univentionUDMModule)(objectClass=univentionUDMSyntax)(objectClass=univentionUDMHook))'):
		ocs = attrs.get('objectClass', [])
		if b'univentionUDMModule' in ocs:
			objectclass = 'univentionUDMModule'
			target_subdir = 'univention/admin/handlers'
		elif b'univentionUDMHook' in ocs:
			objectclass = 'univentionUDMHook'
			target_subdir = 'univention/admin/hooks.d'
		elif b'univentionUDMSyntax' in ocs:
			objectclass = 'univentionUDMSyntax'
			target_subdir = 'univention/admin/syntax.d'
		else:
			continue
		target_filename = attrs.get('%sFilename' % objectclass)[0]
		if os.path.exists(os.path.join(PYSHARED_DIR, target_subdir, target_filename)) or os.path.exists(os.path.join('/usr/lib/pymodules/python2.7', target_subdir, target_filename)):
			try:
				listener.setuid(0)
				handler(dn, attrs, [])  # create files in new location
				listener.setuid(0)
				__remove_pymodules_links(objectclass, target_subdir, target_filename)  # remove obsolete symlinks
				listener.setuid(0)
				__remove_pyshared_file(target_subdir, target_filename)  # drop obsolete pyshared files
				ud.debug(ud.LISTENER, ud.INFO, 'Migrated %s/%s to dh-python.' % (target_subdir, target_filename))
			except Exception:
				ud.debug(ud.LISTENER, ud.ERROR, 'ignoring fatal error %s' % (traceback.format_exc(),))


def handler(dn, new, old):
	"""Handle UDM extension modules"""

	if new:
		ocs = new.get('objectClass', [])

		univentionUCSVersionStart = new.get('univentionUCSVersionStart', [None])[0]
		univentionUCSVersionEnd = new.get('univentionUCSVersionEnd', [None])[0]
		current_UCS_version = "%s-%s" % (listener.configRegistry.get('version/version'), listener.configRegistry.get('version/patchlevel'))
		if univentionUCSVersionStart and UCS_Version(current_UCS_version) < UCS_Version(univentionUCSVersionStart):
			ud.debug(ud.LISTENER, ud.INFO, '%s: extension %s requires at least UCS version %s.' % (name, new['cn'][0], univentionUCSVersionStart))
			new = None
		elif univentionUCSVersionEnd and UCS_Version(current_UCS_version) > UCS_Version(univentionUCSVersionEnd):
			ud.debug(ud.LISTENER, ud.INFO, '%s: extension %s specifies compatibility only up to and including UCR version %s.' % (name, new['cn'][0], univentionUCSVersionEnd))
			new = None
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

	old_relative_filename = None
	if old:
		old_relative_filename = old.get('%sFilename' % objectclass)[0]

	if new:
		new_version = new.get('univentionOwnedByPackageVersion', [None])[0]
		if not new_version:
			return

		new_pkgname = new.get('univentionOwnedByPackage', [None])[0]
		if not new_pkgname:
			return

		if old:  # check for trivial changes
			diff_keys = [key for key in new.keys() if new.get(key) != old.get(key) and key not in ('entryCSN', 'modifyTimestamp', 'modifiersName')]
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

		# ok, basic checks passed, handle the data
		try:
			new_object_data = bz2.decompress(new.get('%sData' % objectclass)[0])
		except TypeError:
			ud.debug(ud.LISTENER, ud.ERROR, '%s: Error uncompressing data of object %s.' % (name, dn))
			return

		new_relative_filename = new.get('%sFilename' % objectclass)[0]
		listener.setuid(0)
		try:
			if old_relative_filename and old_relative_filename != new_relative_filename:
				remove_python_file(objectclass, target_subdir, old_relative_filename)
			if not install_python_file(objectclass, target_subdir, new_relative_filename, new_object_data):
				return
			install_messagecatalog(dn, new, objectclass)
			install_umcmessagecatalogs(new, old)
			if objectclass == 'univentionUDMModule':
				install_umcregistration(dn, new)
				install_umcicons(dn, new)
		finally:
			listener.unsetuid()

	elif old:

		# ok, basic checks passed, handle the change
		listener.setuid(0)
		try:
			remove_python_file(objectclass, target_subdir, old_relative_filename)
			remove_messagecatalog(dn, old, objectclass)
			remove_umcmessagecatalogs(old)
			if objectclass == 'univentionUDMModule':
				remove_umcicons(dn, old)
				remove_umcregistration(dn, old)
		finally:
			listener.unsetuid()

	# Kill running univention-cli-server and mark new extension object active

	listener.setuid(0)
	try:
		if new:
			if not listener.configRegistry.get('server/role') == 'domaincontroller_master':
				# Only set active flag on Master
				return

			try:
				lo, ldap_position = udm_uldap.getAdminConnection()
				udm_modules.update()
				udm_module = udm_modules.get(udm_module_name)
				udm_modules.init(lo, ldap_position, udm_module)

				try:
					udm_object = udm_module.object(None, lo, ldap_position, dn)
					udm_object.open()
					udm_object['active'] = True
					udm_object.modify()
				except udm_errors.ldapError as exc:
					ud.debug(ud.LISTENER, ud.ERROR, '%s: Error modifying %s: %s.' % (name, dn, exc))
				except udm_errors.noObject as exc:
					ud.debug(ud.LISTENER, ud.ERROR, '%s: Error modifying %s: %s.' % (name, dn, exc))

			except udm_errors.ldapError as exc:
				ud.debug(ud.LISTENER, ud.ERROR, '%s: Error accessing UDM: %s' % (name, exc))

	finally:
		listener.unsetuid()


def install_python_file(objectclass, target_subdir, target_filename, data):
	"""Install a python module file"""

	# input validation
	init_file_list = []
	relative_filename = os.path.join(target_subdir, target_filename)
	if not relative_filename:
		ud.debug(ud.LISTENER, ud.ERROR, '%s: No python file to install.' % (name,))
		return False

	if relative_filename.startswith('/'):
		ud.debug(ud.LISTENER, ud.ERROR, '%s: Module path must not be absolute: %s.' % (name, relative_filename))
		return False

	# trivial checks passed, go for it
	try:
		init_file_list.extend(create_python_moduledir(PYTHON_DIR, target_subdir, os.path.dirname(target_filename)))
	except moduleCreationFailed as exc:
		ud.debug(ud.LISTENER, ud.ERROR, '%s: %s' % (name, exc))
		return False

	filename = os.path.join(PYTHON_DIR, relative_filename)
	try:
		with open(filename, 'w') as f:
			f.write(data)
		ud.debug(ud.LISTENER, ud.INFO, '%s: %s installed.' % (name, relative_filename))
		subprocess.call(['/usr/bin/pycompile', '-q', filename])
		return True
	except Exception as exc:
		ud.debug(ud.LISTENER, ud.ERROR, '%s: Writing new data to %s failed: %s.' % (name, filename, exc))
		return False


def remove_python_file(objectclass, target_subdir, target_filename):
	"""Remove python module files"""
	return remove_python_files(PYTHON_DIR, target_subdir, target_filename)


def remove_python_files(python_basedir, target_subdir, target_filename):
	# input validation
	relative_filename = os.path.join(target_subdir, target_filename)
	if not relative_filename:
		ud.debug(ud.LISTENER, ud.ERROR, '%s: No python file to remove.' % (name,))
		return False

	if relative_filename.startswith('/'):
		ud.debug(ud.LISTENER, ud.ERROR, '%s: Module path must not be absolute: %s.' % (name, relative_filename))
		return False

	# trivial checks passed, go for it
	filename = os.path.join(python_basedir, relative_filename)
	if os.path.isfile(filename):
		# Only remove the file if it was not shipped as part of a debian package.
		p = subprocess.Popen(['dpkg', '-S', filename], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
		p.wait()
		if p.returncode == 0:
			# ok, we should not remove this file
			# but at least check if the __init__.py file should be cleaned up. cleanup_python_moduledir would not do it since $filename is sill there.
			target_path = os.path.dirname(filename)
			skipfiles = (os.path.basename(filename), '__init__.py')
			for entry in os.listdir(target_path):
				if entry not in skipfiles:
					return

			python_init_filename = os.path.join(target_path, '__init__.py')
			if os.path.exists(python_init_filename):
				if os.path.getsize(python_init_filename) != 0:
					if open(python_init_filename, 'rb').read() != EXTEND_PATH:
						return

			# Only remove the file if it was not shipped as part of a debian package.
			p = subprocess.Popen(['dpkg', '-S', python_init_filename], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
			p.wait()
			if p.returncode != 0:
				try:
					os.unlink(python_init_filename)
					ud.debug(ud.LISTENER, ud.INFO, '%s: %s removed.' % (name, python_init_filename))
				except OSError as exc:
					ud.debug(ud.LISTENER, ud.ERROR, '%s: Removal of %s failed: %s.' % (name, python_init_filename, exc))
			# return, nothing more to do in this case
			return
		else:
			try:
				os.unlink(filename)
				ud.debug(ud.LISTENER, ud.INFO, '%s: %s removed.' % (name, filename))
			except OSError as exc:
				ud.debug(ud.LISTENER, ud.ERROR, '%s: Removal of %s failed: %s.' % (name, filename, exc))
			if filename.endswith('.py') and os.path.exists(filename + 'c'):
				try:
					os.unlink(filename + 'c')
				except OSError as exc:
					ud.debug(ud.LISTENER, ud.WARN, '%s: Removal of pycompiled %sc failed: %s.' % (name, filename, exc))

	try:
		cleanup_python_moduledir(python_basedir, target_subdir, os.path.dirname(target_filename))
	except moduleRemovalFailed as exc:
		ud.debug(ud.LISTENER, ud.ERROR, '%s: %s' % (name, exc))
		return False


def __remove_pyshared_file(target_subdir, target_filename):
	"""Remove pyshared parts of public python module file"""
	return remove_python_files(PYSHARED_DIR, target_subdir, target_filename)


def __remove_pymodules_links(objectclass, target_subdir, target_filename):
	"""Remove pymodules parts: pyc, pyo, and file itself. Clean up directories in target_filename if empty."""
	# input validation
	relative_filename = os.path.join(target_subdir, target_filename)
	if not relative_filename:
		ud.debug(ud.LISTENER, ud.ERROR, '%s: No python file to remove.' % (name,))
		return False

	if relative_filename.startswith('/'):
		ud.debug(ud.LISTENER, ud.ERROR, '%s: Module path must not be absolute: %s.' % (name, relative_filename))
		return False

	# trivial checks passed, go for it
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
		except OSError as exc:
			ud.debug(ud.LISTENER, ud.ERROR, '%s: Removal of %s failed: %s.' % (name, pysupport_filename, exc))

	try:
		p = subprocess.Popen(['/usr/sbin/update-python-modules', '-p'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		(stdout, stderr) = p.communicate()
	except OSError as exc:
		ud.debug(ud.LISTENER, ud.ERROR, '%s: update-python-modules -p failed: %s.' % (name, exc))

	if p.returncode == 0:
		ud.debug(ud.LISTENER, ud.INFO, '%s: symlinks to %s removed.' % (name, relative_filename))
		return True

	ud.debug(ud.LISTENER, ud.ERROR, '%s: update-python-modules -p failed: %s.' % (name, stderr))
	return False


def create_python_moduledir(python_basedir, target_subdir, module_directory):
	"""create directory and __init__.py (file or link). Recurse for all parent directories in path module_directory"""
	# input validation
	if not module_directory:
		return []

	if module_directory.startswith('/'):
		raise moduleCreationFailed('Module directory must not be absolute: %s' % (module_directory, ))
	target_dir = os.path.join(python_basedir, target_subdir)
	target_path = os.path.join(target_dir, module_directory)
	if not os.path.realpath(target_path).startswith(target_dir):
		raise moduleCreationFailed('Target directory %s not below %s' % (module_directory, target_dir))

	# trivial checks passed, go for it
	init_file_list = []
	parent_dir = os.path.dirname(module_directory)
	if parent_dir and not os.path.exists(os.path.join(python_basedir, target_subdir, parent_dir)):
		init_file_list.extend(create_python_moduledir(python_basedir, target_subdir, parent_dir) or [])

	if not os.path.isdir(target_path):
		try:
			os.mkdir(target_path)
		except OSError as exc:
			raise moduleCreationFailed('Directory creation of %s failed: %s.' % (target_path, exc))

	python_init_filename = os.path.join(target_path, '__init__.py')
	if not os.path.exists(python_init_filename):
		with open(python_init_filename, 'wb') as fd:  # touch
			if target_subdir == 'univention/admin/handlers' and python_basedir == PYTHON_DIR:
				fd.write(EXTEND_PATH)
	init_file_list.append(python_init_filename)

	return init_file_list


def cleanup_python_moduledir(python_basedir, target_subdir, module_directory):
	"""remove __init__.py and directory from if no other file is in the directory. Recurse for all parent directories in path module_directory"""
	# input validation
	if not module_directory:
		return

	if module_directory.startswith('/'):
		raise moduleRemovalFailed('Module directory must not be absolute: %s' % (module_directory, ))
	target_dir = os.path.join(python_basedir, target_subdir)
	target_path = os.path.join(target_dir, module_directory)
	if not os.path.realpath(target_path).startswith(target_dir):
		raise moduleCreationFailed('Target directory %s not below %s' % (module_directory, target_dir))

	if not os.path.isdir(target_path):
		return

	# trivial checks passed, go for it
	for entry in os.listdir(target_path):
		if os.path.splitext(entry)[0] != '__init__':
			return

	python_init_filename = os.path.join(target_path, '__init__.py')
	if os.path.exists(python_init_filename):
		if os.path.getsize(python_init_filename) != 0:
			return

		if python_basedir in (PYTHON_DIR, PYSHARED_DIR):
			# Only remove the file if it was not shipped as part of a debian package.
			p = subprocess.Popen(['dpkg', '-S', python_init_filename], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
			p.wait()
			if p.returncode == 0:
				return
		else:
			# remove pyc and pyo
			basename, ext = os.path.splitext(python_init_filename)
			if ext == '.py':
				for ext in ('.pyc', '.pyo'):
					derived_filename = basename + ext
					if os.path.exists(derived_filename):
						os.unlink(derived_filename)

		try:
			os.unlink(python_init_filename)
			ud.debug(ud.LISTENER, ud.INFO, '%s: %s removed.' % (name, python_init_filename))
		except OSError as exc:
			ud.debug(ud.LISTENER, ud.ERROR, '%s: Removal of %s failed: %s.' % (name, python_init_filename, exc))

	try:
		os.rmdir(target_path)
	except OSError as exc:
		raise moduleRemovalFailed('Removal of directory %s failed: %s.' % (target_path, exc))

	parent_dir = os.path.dirname(module_directory)
	if parent_dir:
		cleanup_python_moduledir(python_basedir, target_subdir, parent_dir)


def install_messagecatalog(dn, attrs, objectclass):
	translationfile_ldap_attribute = "univentionMessageCatalog"
	translationfile_ldap_attribute_and_tag_prefix = "%s;entry-lang-" % (translationfile_ldap_attribute,)
	if objectclass == 'univentionUDMModule':
		prefix = "univention-admin-handlers"
	elif objectclass == 'univentionUDMSyntax':
		prefix = "univention-admin-syntax"
	elif objectclass == 'univentionUDMHook':
		prefix = "univention-admin-hooks"

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
		filename = os.path.join(targetdir, "%s-%s.mo" % (prefix, module_name.replace('/', '-'),))
		if not os.path.exists(targetdir):
			ud.debug(ud.LISTENER, ud.ERROR, '%s: Error writing %s. Parent directory does not exist.' % (name, filename))
			continue
		with open(filename, 'w') as f:
			f.write(mo_data_binary)


def remove_messagecatalog(dn, attrs, objectclass):
	translationfile_ldap_attribute = "univentionMessageCatalog"
	translationfile_ldap_attribute_and_tag_prefix = "%s;entry-lang-" % (translationfile_ldap_attribute,)
	if objectclass == 'univentionUDMModule':
		prefix = "univention-admin-handlers"
	elif objectclass == 'univentionUDMSyntax':
		prefix = "univention-admin-syntax"
	elif objectclass == 'univentionUDMHook':
		prefix = "univention-admin-hooks"

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
		filename = os.path.join(targetdir, "%s-%s.mo" % (prefix, module_name.replace('/', '-'),))
		if not os.path.exists(targetdir):
			ud.debug(ud.LISTENER, ud.ERROR, '%s: Error writing %s. Parent directory does not exist.' % (name, filename))
			continue
		ud.debug(ud.LISTENER, ud.INFO, '%s: Removing %s.' % (name, filename))
		if os.path.exists(filename):
			os.unlink(filename)
		else:
			ud.debug(ud.LISTENER, ud.INFO, '%s: Warning: %s does not exist.' % (name, filename))


def install_umcmessagecatalogs(attrs_new, attrs_old):
	remove_umcmessagecatalogs(attrs_old)
	umcmessagecatalogs = _umcmessagecatalog_ldap_attributes(attrs_new)
	if not umcmessagecatalogs:
		return
	for ldap_filename, mo_data_binary in umcmessagecatalogs.items():
		filename = _parse_filename_from_ldap_attr(ldap_filename)
		if not os.path.exists(os.path.dirname(filename)):
			os.makedirs(os.path.dirname(filename))
		with open(filename, 'w') as f:
			f.write(mo_data_binary)


def remove_umcmessagecatalogs(attrs):
	umcmessagecatalogs = _umcmessagecatalog_ldap_attributes(attrs)
	if not umcmessagecatalogs:
		return
	for ldap_filename, mo_data_binary in umcmessagecatalogs.items():
		filename = _parse_filename_from_ldap_attr(ldap_filename)
		if not os.path.exists(filename):
			ud.debug(ud.LISTENER, ud.INFO, '%s: Warning: %s does not exist.' % (name, filename))
			continue
		else:
			ud.debug(ud.LISTENER, ud.INFO, '%s: Removing %s.' % (name, filename))
			os.unlink(filename)


def _umcmessagecatalog_ldap_attributes(attrs):
	translationfile_ldap_attribute_and_tag_prefix = "univentionUMCMessageCatalog;entry-"
	umcmessagecatalogs = {}
	for ldap_attribute in attrs.keys():
		if ldap_attribute.startswith(translationfile_ldap_attribute_and_tag_prefix):
			filename = ldap_attribute.split(translationfile_ldap_attribute_and_tag_prefix, 1)[1]
			umcmessagecatalogs[filename] = attrs.get(ldap_attribute)[0]
	return umcmessagecatalogs


def _parse_filename_from_ldap_attr(ldap_filename):
	language_tag, module_id = ldap_filename.split('-', 1)
	basedir = os.path.join(LOCALE_BASEDIR_UMC, language_tag.replace('/', '-'))
	return safe_path_join(basedir, '%s.mo' % (module_id,))


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
