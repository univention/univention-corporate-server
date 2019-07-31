#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2013-2019 Univention GmbH
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
from datetime import date
from glob import glob
import fnmatch
import getpass
import json
import magic
import mimetypes
import os
import re
import shutil
import socket
import sys
import traceback

import univention.debhelper as dh_ucs
import univention.dh_umc as dh_umc
import sourcefileprocessing
import message_catalogs

REFERENCE_LANG = 'de'
# Use this set to ignore whole sub trees of a given source tree
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

	@property
	def python_po_files(self):
		for path in super(UMCModuleTranslation, self).python_po_files:
			if os.path.isfile(os.path.join(self['abs_path_to_src_pkg'], os.path.dirname(path), '{}.po'.format(REFERENCE_LANG))):
				yield path

	@property
	def js_po_files(self):
		for path in super(UMCModuleTranslation, self).js_po_files:
			if os.path.isfile(os.path.join(self['abs_path_to_src_pkg'], os.path.dirname(path), '{}.po'.format(REFERENCE_LANG))):
				yield path

	@property
	def xml_po_files(self):
		for lang, path in super(UMCModuleTranslation, self).xml_po_files:
			if os.path.isfile(os.path.join(self['abs_path_to_src_pkg'], os.path.dirname(path), '{}.po'.format(REFERENCE_LANG))):
				yield lang, path

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
				raise AttributeError('UMC module definition incomplete. key {} is missing a value.'.format(required))
		attrs['module_name'] = module.get('module_name')
		attrs['abs_path_to_src_pkg'] = module.get('abs_path_to_src_pkg')
		attrs['relative_path_src_pkg'] = module.get('relative_path_src_pkg')
		return UMCModuleTranslation(attrs, target_language)


class SpecialCase():

	"""Consumes special case definition and determines matching sets of source
	files"""

	def __init__(self, special_case_definition, source_dir, path_to_definition, target_language):
		# FIXME: this would circumvent custom getters and setter?
		self.__dict__.update(special_case_definition)
		def_relative = os.path.relpath(path_to_definition, start=source_dir)
		matches = re.match(r'(.*)/debian/(.*).univention-l10n', def_relative)
		if matches:
			self.package_dir, self.binary_package_name = matches.groups()
		else:
			self.binary_package_name = re.match(r'debian/(.*).univention-l10n', def_relative).groups()[0]
			self.package_dir = os.getcwd()
		self.source_dir = source_dir
		if hasattr(self, 'po_path'):
			self.new_po_path = self.po_path.format(lang=target_language)
		else:
			self.po_subdir = self.po_subdir.format(lang=target_language)
			self.new_po_path = os.path.join(self.po_subdir, '{}.po'.format(target_language))
		self.destination = self.destination.format(lang=target_language)
		self.path_to_definition = path_to_definition

	def _get_files_matching_patterns(self):
		try:
			src_pkg_path = os.path.join(self.source_dir, self.package_dir)
		except AttributeError:
			src_pkg_path = os.path.join(os.getcwd())
			pass
		matched = list()
		regexs = list()
		for pattern in [os.path.join(src_pkg_path, pattern) for pattern in self.input_files]:
			try:
				regexs.append(re.compile(r'{}$'.format(pattern)))
			except re.error:
				sys.exit("Invalid input_files statement in: {}. Value must be valid regular expression.".format(self.path_to_definition))
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
				source_file_sets.append(sourcefileprocessing.from_mimetype(os.path.join(self.source_dir, self.package_dir), self.binary_package_name, mime, file_set))
			except sourcefileprocessing.UnsupportedSourceType:
				continue
		return source_file_sets

	def create_po_template(self, output_path=os.path.curdir):
		base, ext = os.path.splitext(os.path.join(output_path, self.new_po_path))
		pot_path = '{}.pot'.format(base)
		message_catalogs.create_empty_po(self.binary_package_name, pot_path)
		partial_pot_path = '{}.pot.partial'.format(base)
		for sfs in self.get_source_file_sets():
			sfs.process_po(partial_pot_path)
			message_catalogs.concatenate_po(partial_pot_path, pot_path)
			os.unlink(partial_pot_path)
		return pot_path


class MIMEChecker():

	# FIXME: this is not need as mimetypes implements it already. The get()
	# method should be adjusted to first use mimetypes.guess_type() and then
	# resort to libmagic
	suffixes = {
		'.js': 'application/javascript',
		'.py': 'text/x-python',
		'.html': 'text/html',
		'.sh': 'text/x-shellscript',
	}

	def __init__(self):
		self._ms = magic.open(magic.MIME_TYPE)
		self._ms.load()

	def __enter__(self):
		return self

	def __exit__(self, exc_type, exc_value, traceback):
		self._ms.close()

	def get(self, file_path):
		_path, suffix = os.path.splitext(file_path)
		if suffix in self.suffixes:
			return self.suffixes[suffix]
		with open(file_path, 'rb') as fd:
			mime = self._ms.buffer(fd.read(4096))
		if 'text/plain' in mime:
			with open(file_path) as source_file:
				if 'ucs-test/selenium' in source_file.readline():
					mime = 'text/x-python'
				else:
					mime = mimetypes.guess_type(file_path)[0]
		return mime


def update_package_translation_files(module, output_dir):
	print("Creating directories and PO files for {module_name} in translation source package".format(**module))
	start_dir = os.getcwd()
	try:
		os.chdir(module.get('abs_path_to_src_pkg'))
		if not module.get('core'):
			def _create_po_files(po_files, src_files, language):
				for po_file in po_files:
					po_path = os.path.join(output_dir, module['relative_path_src_pkg'], po_file)
					make_parent_dir(po_path)
					try:
						dh_umc.create_po_file(po_path, module['module_name'], src_files, language)
					except dh_umc.Error as exc:
						print(str(exc))

			# build python po files
			_create_po_files(module.python_po_files, module.python_files, 'Python')
			_create_po_files(module.js_po_files, module.js_files, 'JavaScript')

		# xml always has to be present
		for lang, po_file in module.xml_po_files:
			po_path = os.path.join(output_dir, module['relative_path_src_pkg'], po_file)
			make_parent_dir(po_path)
			try:
				dh_umc.module_xml2po(module, po_path, lang)
			except dh_umc.Error as exc:
				print(str(exc))

	except OSError as exc:
		print(traceback.format_exc())
		print("error in update_package_translation_files: %s" % (exc,))
	finally:
		os.chdir(start_dir)


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
		print("Warning: Path defined under 'package_dir' not found. Please check the definitions in the *.univention-l10n file in {}".format(special_case.package_dir))
		return
	new_po_path = os.path.join(output_dir, special_case.package_dir, special_case.new_po_path)
	make_parent_dir(new_po_path)
	pot_path = special_case.create_po_template(output_path=os.path.join(os.getcwd(), output_dir, special_case.package_dir))
	message_catalogs.univention_location_lines(pot_path, os.path.join(source_dir, special_case.package_dir))
	os.rename(pot_path, new_po_path)


def read_special_case_definition(definition_path, source_tree_path, target_language):
	with open(definition_path) as fd:
		try:
			sc_definitions = json.load(fd)
		except ValueError:
			sys.exit('Error: Invalid syntax in {}. File must be valid JSON.'.format(definition_path))
		for scdef in sc_definitions:
			yield SpecialCase(scdef, source_tree_path, definition_path, target_language)


def get_special_cases_from_srcpkg(source_tree_path, target_language):
	special_case_files = glob('debian/*.univention-l10n')
	special_cases = []
	for sc_definitions in special_case_files:
		for sc in read_special_case_definition(sc_definitions, os.getcwd(), target_language):
			special_cases.append(sc)
	return special_cases


def get_special_cases_from_checkout(source_tree_path, target_language):
	"""Process *.univention-l10n files in the whole SVN branch. Currently they
	lay 3 (UCS@school) or 4(UCS) directory levels deep in the SVN repository.
	"""
	# FIXME: This should check for SVN metadata or the like to be more robust.
	special_cases = []
	sc_files = glob(os.path.join(source_tree_path, '*/*/debian/*.univention-l10n')) or glob(os.path.join(source_tree_path, '*/debian/*.univention-l10n'))
	if not sc_files:
		raise NoSpecialCaseDefintionsFound()
	for definition_path in sc_files:
		special_cases.extend([sc for sc in read_special_case_definition(definition_path, source_tree_path, target_language)])
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


def make_parent_dir(path):
	"""If path is a directory path the directory and its parents will be created, if path is a file create its parents will be created."""
	dir_path = os.path.dirname(path)
	try:
		os.makedirs(dir_path)
	except OSError:
		if not os.path.isdir(dir_path):
			raise


def write_debian_rules(debian_dir_path):
	with open(os.path.join(debian_dir_path, 'rules'), 'w') as f:
		f.write("""#!/usr/bin/make -f
#
# Copyright 2016-{year} Univention GmbH
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
	dh $@""".format(year=date.today().year))


def create_new_package(new_package_dir, target_language, target_locale, language_name, startdir):
	new_package_dir_debian = os.path.join(new_package_dir, 'debian')
	if not os.path.exists(new_package_dir_debian):
		print("creating directory: %s" % new_package_dir_debian)
		os.makedirs(new_package_dir_debian)
	translation_package_name = os.path.basename(new_package_dir)
	translation_creator = getpass.getuser()
	translation_host = socket.getfqdn()
	with open(os.path.join(new_package_dir_debian, 'copyright'), 'w') as f:
		f.write("""\
Format: https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/
Upstream-Name: Univention GmbH
Upstream-Contact: <package@univention.de>
Source: https://updates.software-univention.de/

Files: *
Copyright: {years} Univention GmbH
License: AGPL-3.0-only
 The source code of the software contained in this package
 as well as the source package itself are made available
 under the terms of the GNU Affero General Public License version 3
 (GNU AGPL V3) as published by the Free Software Foundation.
 .
 Binary versions of this program provided by Univention to you as
 well as other copyrighted, protected or trademarked materials like
 Logos, graphics, fonts, specific documentations and configurations,
 cryptographic keys etc. are subject to a license agreement between
 you and Univention and not subject to the GNU AGPL V3.
 .
 In the case you use this program under the terms of the GNU AGPL V3,
 the program is provided in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 GNU Affero General Public License for more details.
 .
 You should have received a copy of the GNU Affero General Public
 License with the Debian GNU/Linux or Univention distribution in file
 /usr/share/common-licenses/AGPL-3; if not, see
 <http://www.gnu.org/licenses/>.""".format(years=date.today().year))

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
