#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2013-2016 Univention GmbH
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
from email.Utils import formatdate
from glob import glob
import fnmatch
import getpass
import json
import magic
import mimetypes
import os
import pofile
import re
import shutil
import socket
import sourcefileprocessing
import sys
import traceback
import univention.debhelper as dh_ucs
import univention.dh_umc as dh_umc

# Use this set to ignore whole subtrees of a given source tree
DIR_BLACKLIST = set([
	'./doc',
	'./test',
])
# do not translate modules with these names, as they are examples and thus not worth the effort
MODULE_BLACKLIST = [
	'PACKAGENAME',
	'0001-6-7'
]


class NoSpecialCaseDefintionsFound(Exception):
	pass


class UMCModuleTranslation(dh_umc.UMC_Module):

	def __init__(self, attrs, target_language):
		attrs['target_language'] = target_language
		return super(UMCModuleTranslation, self).__init__(attrs)

	def python_mo_destinations(self):
		for po_file in self.python_po_files:
			yield os.path.join(self.get('target_language'), self.get('relative_path_src_pkg'), po_file), 'usr/share/locale/{target_language}/LC_MESSAGES/{module_name}.mo'.format(**self)

	def json_targets(self):
		for js_po in self.js_po_files:
			yield os.path.join(self.get('target_language'), self.get('relative_path_src_pkg'), js_po), 'usr/share/univention-management-console-frontend/js/umc/modules/i18n/{target_language}/{Module}.json'.format(**self)

	def xml_mo_destinations(self):
		for _, xml_po in self.xml_po_files:
			yield os.path.join(self.get('target_language'), self.get('relative_path_src_pkg'), xml_po), 'usr/share/univention-management-console/i18n/{target_language}/{Module}.mo'.format(**self)

	@staticmethod
	def from_source_package(module_in_source_tree, target_language):
		try:
			# read package content with dh_umc
			module = UMCModuleTranslation._get_module_from_source_package(module_in_source_tree, target_language)
		except AttributeError as e:
			print("%s AttributeError in module, trying to load as core module" % str(e))
		else:
			module['core'] = False
			return module

		try:
			module = UMCModuleTranslation._get_core_module_from_source_package(module_in_source_tree, target_language)
		except AttributeError as e:
			print("%s core module load failed" % str(e))
		else:
			print("Successfully loaded as core module: {}".format(module_in_source_tree.get('abs_path_to_src_pkg')))
			module['core'] = True
			return module

	@staticmethod
	def _read_module_attributes_from_source_package(module):
		umc_module_definition_file = os.path.join(module.get('abs_path_to_src_pkg'), 'debian/', '{}.umc-modules'.format(module.get('module_name')))
		with open(umc_module_definition_file, 'r') as fd:
			def_file = fd.read()
		return dh_ucs.parseRfc822(def_file)[0]

	@staticmethod
	def _get_core_module_from_source_package(module, target_language):
		attrs = UMCModuleTranslation._read_module_attributes_from_source_package(module)
		attrs['module_name'] = module.get('module_name')
		attrs['abs_path_to_src_pkg'] = module.get('abs_path_to_src_pkg')
		attrs['relative_path_src_pkg'] = module.get('relative_path_src_pkg')
		module = UMCModuleTranslation(attrs, target_language)
		if module.module_name != 'umc-core' or not module.xml_categories:
			raise ValueError('Module definition does not match core module')
		return module

	@staticmethod
	def _get_module_from_source_package(module, target_language):
		attrs = UMCModuleTranslation._read_module_attributes_from_source_package(module)
		for required in (dh_umc.MODULE, dh_umc.PYTHON, dh_umc.DEFINITION, dh_umc.JAVASCRIPT):
			if required not in attrs:
				raise AttributeError('UMC module definition incomplete. key {} missing.'.format(required))
			if required not in attrs:
				raise AttributeError('UMC module defintion incomplete. key {} is missing a value.'.format(required))
		attrs['module_name'] = module.get('module_name')
		attrs['abs_path_to_src_pkg'] = module.get('abs_path_to_src_pkg')
		attrs['relative_path_src_pkg'] = module.get('relative_path_src_pkg')
		return UMCModuleTranslation(attrs, target_language)


class SpecialCase():

	"""Consumes special case definition and computes resulting sets of source
	files"""

	def __init__(self, special_case_definition, source_dir, path_to_definition, target_language):
		self.__dict__.update(special_case_definition)
		def_relative = os.path.relpath(path_to_definition, start=source_dir)
		self.package_dir, self.binary_package_name = re.match(r'(.*)/debian/(.*).univention-l10n', def_relative).groups()
		self.source_dir = source_dir
		self.po_subdir = self.po_subdir.format(lang=target_language)
		self.destination = self.destination.format(lang=target_language)
		self.new_po_path = os.path.join(self.po_subdir, '{}.po'.format(target_language))
		self.path_to_definition = path_to_definition

	def _get_files_matching_patterns(self):
		src_pkg_path = os.path.join(self.source_dir, self.package_dir)
		matched = list()
		regexs = list()
		for pattern in [os.path.join(src_pkg_path, pattern) for pattern in self.input_files]:
			try:
				regexs.append(re.compile(r'{}$'.format(pattern)))
			except re.error:
				sys.exit("""Invalid input_files statement in: {}
Value must be valid regular expression.""".format(self.path_to_definition))
		for parent, dirnames, fnames in os.walk(src_pkg_path):
			paths = [os.path.join(parent, fn) for fn in fnames]
			for rex in regexs:
				matched.extend([path for path in paths if rex.match(path)])
		return matched

	def get_source_file_sets(self):
		files_by_mime = dict()
		with MIMEChecker() as mime:
			for file_path in self._get_files_matching_patterns():
				files_by_mime.setdefault(mime.get(file_path), []).append(file_path)
		source_file_sets = list()
		for mime, file_set in files_by_mime.iteritems():
			try:
				source_file_sets.append(sourcefileprocessing.from_mimetype(os.path.join(self.source_dir, self.package_dir), mime, file_set))
			except sourcefileprocessing.UnsupportedSourceType:
				continue
		return source_file_sets


class MIMEChecker():

	def __init__(self):
		self._ms = magic.open(magic.MIME_TYPE)
		self._ms.load()

	def __enter__(self):
		return self

	def __exit__(self, exc_type, exc_value, traceback):
		self._ms.close()

	def get(self, file_path):
		with open(file_path, 'rb') as fd:
			mime = self._ms.buffer(fd.read(4096))
		if 'text/plain' in mime:
			mime = mimetypes.guess_type(file_path)[0]
		return mime


def update_package_translation_files(module, output_dir):
	print("Creating directories and PO files for {module_name} in translation source package".format(**module))
	start_dir = os.getcwd()
	try:
		# create directories for package translation
		abs_path_translated_src_pkg = os.path.abspath("{}/{relative_path_src_pkg}".format(output_dir, **module))
		if not os.path.exists(abs_path_translated_src_pkg):
			os.makedirs(abs_path_translated_src_pkg)

		os.chdir(module.get('abs_path_to_src_pkg'))
		if not module.get('core'):
			def _create_po_files(po_files, src_files, language):
				for po_file in po_files:
					new_po_file_abs_path = os.path.join(abs_path_translated_src_pkg, po_file)
					if not os.path.exists(os.path.dirname(new_po_file_abs_path)):
						os.makedirs(os.path.dirname(new_po_file_abs_path))
					try:
						dh_umc.create_po_file(new_po_file_abs_path, module['module_name'], src_files, language)
					except dh_umc.Error as exc:
						print(str(exc))

			# build python po files
			_create_po_files(module.python_po_files, module.python_files, 'Python')
			_create_po_files(module.js_po_files, module.js_files, 'JavaScript')

		# xml always has to be present
		for lang, po_file in module.xml_po_files:
			po_file_full_path = os.path.join(abs_path_translated_src_pkg, po_file)
			if not os.path.exists(os.path.dirname(po_file_full_path)):
				os.makedirs(os.path.dirname(po_file_full_path))
			try:
				dh_umc.module_xml2po(module, po_file_full_path, lang)
			except dh_umc.Error as exc:
				print(str(exc))

	except OSError as exc:
		print(traceback.format_exc())
		print("error in update_package_translation_files: %s" % (exc,))
	finally:
		os.chdir(start_dir)
	return abs_path_translated_src_pkg


def write_makefile(all_modules, special_cases, new_package_dir, target_language):
	def _append_to_target_lists(mo_destination, po_file):
		mo_targets_list.append('$(DESTDIR)/{}'.format(mo_destination))
		target_prerequisite.append('$(DESTDIR)/{}: {}'.format(mo_destination, po_file))

	mo_targets_list = list()
	target_prerequisite = list()
	for module in all_modules:
		if not module.get('core'):
			for file_paths in (module.python_mo_destinations, module.json_targets):
				for po_file, mo_destination in file_paths():
					_append_to_target_lists(mo_destination, po_file)
		for po_file, mo_destination in module.xml_mo_destinations():
			_append_to_target_lists(mo_destination, po_file)

	for scase in special_cases:
		_append_to_target_lists(scase.destination, os.path.join(target_language, scase.package_dir, scase.new_po_path))
	with open(os.path.join(new_package_dir, 'all_targets.mk'), 'w') as fd:
		fd.write("# This file is auto-generated by univention-ucs-translation-build-package and should not be edited!\n\n")
		fd.write('ALL_TARGETS = {}\n\n'.format(' \\\n\t'.join(mo_targets_list)))
		fd.write('\n'.join(target_prerequisite))
		fd.write('\n')


def translate_special_case(special_case, source_dir, output_dir):
	path_src_pkg = os.path.join(source_dir, special_case.package_dir)
	if not os.path.isdir(path_src_pkg):
		print("Warning: Path defined under 'package_dir' not found. Check specialcase.json definitions with package_name: {}".format(special_case.package_dir))
		return
	new_po_path = os.path.join(output_dir, special_case.package_dir, special_case.new_po_path)
	new_po_dir = os.path.dirname(new_po_path)
	if not os.path.exists(new_po_dir):
		os.makedirs(new_po_dir)
	# new_po_path = os.path.join(new_po_path, '{}.po'.format(target_language))
	pofile.create_empty_po(special_case.binary_package_name, new_po_path)
	for source_file_set in special_case.get_source_file_sets():
		source_file_set.process(new_po_path)


def get_special_cases(source_tree_path, target_language):
	# currently only svn checkouts on branch level are processed correctly.
	# So the tree in source_tree_path must contain *.univention-l10n files on
	# the third (UCS@school) or fourth (UCS) level
	# FIXME: This should check for SVN metadata or the like
	special_cases = []
	sc_files = glob(os.path.join(source_tree_path, '*/*/debian/*.univention-l10n')) or glob(os.path.join(source_tree_path, '*/debian/*.univention-l10n'))
	if not sc_files:
		raise NoSpecialCaseDefintionsFound()
	for definition_path in sc_files:
		with open(definition_path) as fd:
			try:
				sc_definitions = json.load(fd)
			except ValueError:
				sys.exit('Error: Invalid syntax in {}. File must be valid JSON.'.format(definition_path))
			for scdef in sc_definitions:
				special_cases.append(SpecialCase(scdef, source_tree_path, definition_path, target_language))
	return special_cases


def find_base_translation_modules(startdir, source_dir, module_basefile_name):
	print('looking in %s' % source_dir)
	print('looking for files matching %s' % module_basefile_name)
	os.chdir(source_dir)
	matches = []
	for root, dirnames, filenames in os.walk('.'):
		dirnames[:] = [d for d in dirnames if os.path.join(root, d) not in DIR_BLACKLIST]
		for filename in fnmatch.filter(filenames, "*" + module_basefile_name):
			matches.append(os.path.join(root, filename))

	base_translation_modules = []

	regex = re.compile(".*/(.*)/debian/.*%s$" % re.escape(module_basefile_name))
	for match in matches:
		print(match)
		packagenameresult = regex.search(match)
		if packagenameresult:
			packagename = packagenameresult.group(1)

			modulename = os.path.basename(match.replace(module_basefile_name, ''))
			if modulename in MODULE_BLACKLIST:
				print("Ignoring module %s: Module is blacklisted\n" % modulename)
				continue

			package_dir = os.path.dirname(os.path.dirname(match))
			print("Found package: %s" % package_dir)
			module = {}
			module['module_name'] = modulename
			module['binary_package_name'] = packagename
			module['abs_path_to_src_pkg'] = os.path.abspath(package_dir)
			module['relative_path_src_pkg'] = os.path.relpath(package_dir)
			base_translation_modules.append(module)
		else:
			print("could not obtain packagename from directory %s" % match)

	os.chdir(startdir)
	return base_translation_modules


def write_debian_rules(debian_dir_path):
	with open(os.path.join(debian_dir_path, 'rules'), 'w') as f:
		f.write("""#!/usr/bin/make -f
#
# Copyright 2016 Univention GmbH
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

override_dh_auto_test:
	ucslint -m 0008
	dh_auto_test

%:
	dh $@""")


def create_new_package(new_package_dir, target_language, target_locale, language_name, startdir):
	new_package_dir_debian = os.path.join(new_package_dir, 'debian')
	if not os.path.exists(new_package_dir_debian):
		print("creating directory: %s" % new_package_dir_debian)
		os.makedirs(new_package_dir_debian)
	translation_package_name = os.path.basename(new_package_dir)
	translation_creator = getpass.getuser()
	translation_host = socket.getfqdn()
	with open(os.path.join(new_package_dir_debian, 'copyright'), 'w') as f:
		f.write("""Copyright 2016 Univention GmbH

http://www.univention.de/

All rights reserved.

The source code of the software contained in this package
as well as the source package itself are made available
under the terms of the GNU Affero General Public License version 3
(GNU AGPL V3) as published by the Free Software Foundation.

Binary versions of this package provided by Univention to you as
well as other copyrighted, protected or trademarked materials like
Logos, graphics, fonts, specific documentations and configurations,
cryptographic keys etc. are subject to a license agreement between
you and Univention and not subject to the GNU AGPL V3.

In the case you use the software under the terms of the GNU AGPL V3,
the program is provided in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public
License with the Debian GNU/Linux or Univention distribution in file
/usr/share/common-licenses/AGPL-3; if not, see
<http://www.gnu.org/licenses/>.""")

	with open(os.path.join(new_package_dir_debian, 'changelog'), 'w') as f:
		f.write("""%s (1.0.0-1) unstable; urgency=low

  * Initial release

 -- %s <%s@%s>  %s""" % (translation_package_name, translation_creator, translation_creator, translation_host, formatdate()))

	write_debian_rules(new_package_dir_debian)

	with open(os.path.join(new_package_dir_debian, 'control'), 'w') as f:
                f.write("""Source: %s
Section: univention
Priority: optional
Maintainer: %s <%s@%s>
Build-Depends: debhelper (>= 7.0.50~),
 ucslint,
 univention-config-dev,
 univention-management-console-dev
Standards-Version: 3.8.2

Package: %s
Architecture: all
Depends: ${misc:Depends},
 univention-management-console
Description: UCS Management Console translation files
 This package is part of Univention Corporate Server (UCS),
 an integrated, directory driven solution for managing
 corporate environments. For more information about UCS,
 refer to: http://www.univention.de/""" % (translation_package_name, translation_creator, translation_creator, socket.getfqdn(), translation_package_name))
	# compat
	with open(os.path.join(new_package_dir_debian, 'compat'), 'w') as f:
		f.write("7")
	with open(os.path.join(new_package_dir_debian, '%s.postinst' % translation_package_name), 'w') as f:
		f.write("""#!/bin/sh
#DEBHELPER#

eval \"$(ucr shell locale)\"
new_locale="%s"
case "${locale}" in
	*"${new_locale}"*) echo "Locale ${new_locale} already known" ;;
	*)	ucr set locale="${locale} ${new_locale}" ;;
esac

ucr set ucs/server/languages/%s?"%s"

exit 0""" % (target_locale, target_locale.split('.')[0], language_name))

	language_dict = {"lang": target_language}
	with open(os.path.join(new_package_dir_debian, '%s.dirs' % translation_package_name), 'w') as f:
		f.write("""usr/share/univention-management-console-frontend/js/umc/modules/i18n/%(lang)s
usr/share/univention-management-console-frontend/js/umc/i18n/%(lang)s
usr/share/univention-management-console-frontend/js/umc/help
usr/share/univention-management-console/i18n/%(lang)s
usr/share/locale/%(lang)s/LC_MESSAGES
""" % language_dict)

	shutil.copyfile('/usr/share/univention-ucs-translation-template/base_makefile', os.path.join(new_package_dir, 'Makefile'))
	# Move source files and installed .mo files to new package dir
	if os.path.exists(os.path.join(new_package_dir, 'usr')):
		shutil.rmtree(os.path.join(new_package_dir, 'usr'))
	# shutil.copytree(os.path.join(startdir, 'usr'), os.path.join(new_package_dir, 'usr'))
	# shutil.rmtree(os.path.join(startdir, 'usr'))

	if os.path.exists(os.path.join(new_package_dir, target_language)):
		shutil.rmtree(os.path.join(new_package_dir, target_language))
	shutil.copytree(os.path.join(startdir, target_language), os.path.join(new_package_dir, target_language))
	shutil.rmtree(os.path.join(startdir, target_language))
