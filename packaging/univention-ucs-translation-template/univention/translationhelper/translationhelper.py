#!/usr/bin/env python
# -*- coding: utf-8 -*-
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
from __future__ import print_function
from email.Utils import formatdate
from datetime import date
from glob import glob
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

from debian.deb822 import Deb822

from . import umc
from . import sourcefileprocessing
from . import message_catalogs
from .helper import make_parent_dir
try:
	from typing import Any, Dict, Iterable, Iterator, List, Optional, Pattern, Tuple, Type  # noqa F401
	from types import TracebackType  # noqa
	from mypy_extensions import TypedDict
	BaseModule = TypedDict('BaseModule', {'module_name': str, 'binary_package_name': str, 'abs_path_to_src_pkg': str, 'relative_path_src_pkg': str})
except ImportError:
	pass


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


class UMCModuleTranslation(umc.UMC_Module):

	def __init__(self, attrs, target_language):
		# type: (Dict[str, Any], str) -> None
		attrs['target_language'] = target_language
		return super(UMCModuleTranslation, self).__init__(attrs)

	@property
	def python_po_files(self):
		# type: () -> Iterator[str]
		for path in super(UMCModuleTranslation, self).python_po_files:
			if os.path.isfile(os.path.join(self['abs_path_to_src_pkg'], os.path.dirname(path), '{}.po'.format(REFERENCE_LANG))):
				yield path

	@property
	def js_po_files(self):
		# type: () -> Iterator[str]
		for path in super(UMCModuleTranslation, self).js_po_files:
			if os.path.isfile(os.path.join(self['abs_path_to_src_pkg'], os.path.dirname(path), '{}.po'.format(REFERENCE_LANG))):
				yield path

	@property
	def xml_po_files(self):
		# type: () -> Iterator[Tuple[str, str]]
		for lang, path in super(UMCModuleTranslation, self).xml_po_files:
			if os.path.isfile(os.path.join(self['abs_path_to_src_pkg'], os.path.dirname(path), '{}.po'.format(REFERENCE_LANG))):
				yield lang, path

	def python_mo_destinations(self):
		# type: () -> Iterator[Tuple[str, str]]
		for po_file in self.python_po_files:
			yield os.path.join(self['target_language'], self['relative_path_src_pkg'], po_file), 'usr/share/locale/{target_language}/LC_MESSAGES/{module_name}.mo'.format(**self)

	def json_targets(self):
		# type: () -> Iterator[Tuple[str, str]]
		for js_po in self.js_po_files:
			yield os.path.join(self['target_language'], self['relative_path_src_pkg'], js_po), 'usr/share/univention-management-console-frontend/js/umc/modules/i18n/{target_language}/{Module}.json'.format(**self)

	def xml_mo_destinations(self):
		# type: () -> Iterator[Tuple[str, str]]
		for _, xml_po in self.xml_po_files:
			yield os.path.join(self['target_language'], self['relative_path_src_pkg'], xml_po), 'usr/share/univention-management-console/i18n/{target_language}/{Module}.mo'.format(**self)

	@classmethod
	def from_source_package(cls, module_in_source_tree, target_language):
		# type: (BaseModule, str) -> UMCModuleTranslation
		try:
			# read package content with umc
			module = cls._get_module_from_source_package(module_in_source_tree, target_language)
		except AttributeError as e:
			print("%s AttributeError in module, trying to load as core module" % (e,))
		else:
			module['core'] = False
			return module

		try:
			module = cls._get_core_module_from_source_package(module_in_source_tree, target_language)
		except AttributeError as e:
			print("%s core module load failed" % (e,))
		else:
			print("Successfully loaded as core module: {}".format(module_in_source_tree['abs_path_to_src_pkg']))
			module['core'] = True
			return module

	@staticmethod
	def _read_module_attributes_from_source_package(module):
		# type: (BaseModule) -> umc.UMC_Module
		umc_module_definition_file = os.path.join(module['abs_path_to_src_pkg'], 'debian/', '{}.umc-modules'.format(module['module_name']))
		with open(umc_module_definition_file, 'r') as fd:
			def_file = fd.read()

		attributes = Deb822(def_file)
		attributes = dict((k, [v]) for k, v in attributes.iteritems())  # simulate dh_ucs.parseRfc822 behaviour
		return attributes

	@classmethod
	def _get_core_module_from_source_package(cls, module, target_language):
		# type: (BaseModule, str) -> UMCModuleTranslation
		attrs = cls._read_module_attributes_from_source_package(module)
		attrs['package'] = module['binary_package_name']
		attrs['module_name'] = module['module_name']
		attrs['abs_path_to_src_pkg'] = module['abs_path_to_src_pkg']
		attrs['relative_path_src_pkg'] = module['relative_path_src_pkg']
		umc_module = cls(attrs, target_language)
		if umc_module.module_name != 'umc-core' or not umc_module.xml_categories:
			raise ValueError('Module definition does not match core module')
		return umc_module

	@classmethod
	def _get_module_from_source_package(cls, module, target_language):
		# type: (BaseModule, str) -> UMCModuleTranslation
		attrs = cls._read_module_attributes_from_source_package(module)
		for required in (umc.MODULE, umc.PYTHON, umc.DEFINITION, umc.JAVASCRIPT):
			if required not in attrs:
				raise AttributeError('UMC module definition incomplete. key {} is missing a value.'.format(required))
		attrs['package'] = module['binary_package_name']
		attrs['module_name'] = module['module_name']
		attrs['abs_path_to_src_pkg'] = module['abs_path_to_src_pkg']
		attrs['relative_path_src_pkg'] = module['relative_path_src_pkg']
		return cls(attrs, target_language)


class SpecialCase():
	"""
	Consumes special case definition and determines matching sets of source
	files.

	:param special_case_definition: Mapping with special case definitions.
	:param source_dir: Base directory.
	:param path_to_definition: Path to definition file.
	:param target_language: 2-letter language code.
	"""

	def __init__(self, special_case_definition, source_dir, path_to_definition, target_language):
		# type: (Dict[str, str], str, str, str) -> None
		# FIXME: this would circumvent custom getters and setter?
		self.__dict__.update(special_case_definition)
		def_relative = os.path.relpath(path_to_definition, start=source_dir)
		matches = re.match(r'(.+/)?debian/([^/]+).univention-l10n$', def_relative)
		if not matches:
			raise ValueError(def_relative)

		pdir, self.binary_package_name = matches.groups()
		self.package_dir = os.getcwd() if pdir is None else pdir.rstrip('/')  # type: str

		self.source_dir = source_dir
		if hasattr(self, 'po_path'):
			self.new_po_path = self.po_path.format(lang=target_language)
		else:
			self.po_subdir = self.po_subdir.format(lang=target_language)  # type: str
			self.new_po_path = os.path.join(self.po_subdir, '{}.po'.format(target_language))

		self.destination = self.destination.format(lang=target_language)  # type: str
		self.path_to_definition = path_to_definition

	def _get_files_matching_patterns(self):
		# type: () -> List[str]
		try:
			src_pkg_path = os.path.join(self.source_dir, self.package_dir)
		except AttributeError:
			src_pkg_path = os.path.join(os.getcwd())

		matched = []  # type: List[str]
		regexs = []  # type: List[Pattern[str]]
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
		# type: () -> List[sourcefileprocessing.SourceFileSet]
		files_by_mime = {}  # type: Dict[str, List[str]]
		with MIMEChecker() as mime:
			for file_path in self._get_files_matching_patterns():
				files_by_mime.setdefault(mime.get(file_path), []).append(file_path)

		source_file_sets = []  # type: List[sourcefileprocessing.SourceFileSet]
		for mime_type, file_set in files_by_mime.iteritems():
			try:
				source_file_sets.append(sourcefileprocessing.from_mimetype(os.path.join(self.source_dir, self.package_dir), self.binary_package_name, mime_type, file_set))
			except sourcefileprocessing.UnsupportedSourceType:
				continue

		return source_file_sets

	def create_po_template(self, output_path=os.path.curdir):
		# type: (str) -> str
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
		# type: () -> None
		self._ms = magic.open(magic.MIME_TYPE)
		self._ms.load()

	def __enter__(self):
		# type: () -> MIMEChecker
		return self

	def __exit__(self, exc_type, exc_value, traceback):
		# type: (Optional[Type[BaseException]], Optional[BaseException], Optional[TracebackType]) -> None
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
	# type: (UMCModuleTranslation, str) -> None
	print("Creating directories and PO files for {module_name} in translation source package".format(**module))
	start_dir = os.getcwd()
	try:
		os.chdir(module['abs_path_to_src_pkg'])
		if not module.get('core'):

			def _create_po_files(po_files, src_files, language):
				# type: (Iterable[str], Iterable[str], str) -> None
				for po_file in po_files:
					po_path = os.path.join(output_dir, module['relative_path_src_pkg'], po_file)
					make_parent_dir(po_path)
					try:
						umc.create_po_file(po_path, module['module_name'], src_files, language)
					except umc.Error as exc:
						print(exc)

			# build python po files
			_create_po_files(module.python_po_files, module.python_files, 'Python')
			_create_po_files(module.js_po_files, module.js_files, 'JavaScript')

		# xml always has to be present
		for lang, po_file in module.xml_po_files:
			po_path = os.path.join(output_dir, module['relative_path_src_pkg'], po_file)
			make_parent_dir(po_path)
			try:
				umc.module_xml2po(module, po_path, lang)
			except umc.Error as exc:
				print(exc)

	except OSError as exc:
		print(traceback.format_exc())
		print("error in update_package_translation_files: %s" % (exc,))
	finally:
		os.chdir(start_dir)


def write_makefile(all_modules, special_cases, new_package_dir, target_language):
	# type: (List[UMCModuleTranslation], List[SpecialCase], str, str) -> None
	mo_targets_list = []  # type: List[str]
	target_prerequisite = []  # type: List[str]

	def _append_to_target_lists(mo_destination, po_file):
		# type: (str, str) -> None
		mo_targets_list.append('$(DESTDIR)/{}'.format(mo_destination))
		target_prerequisite.append('$(DESTDIR)/{}: {}'.format(mo_destination, po_file))

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
	# type: (SpecialCase, str, str) -> None
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
	# type: (str, str, str) -> Iterator[SpecialCase]
	with open(definition_path) as fd:
		try:
			sc_definitions = json.load(fd)
		except ValueError:
			sys.exit('Error: Invalid syntax in {}. File must be valid JSON.'.format(definition_path))
		for scdef in sc_definitions:
			yield SpecialCase(scdef, source_tree_path, definition_path, target_language)


def get_special_cases_from_srcpkg(source_tree_path, target_language):
	# type: (str, str) -> List[SpecialCase]
	special_case_files = glob('debian/*.univention-l10n')
	special_cases = []  # type: List[SpecialCase]
	for sc_definitions in special_case_files:
		for sc in read_special_case_definition(sc_definitions, os.getcwd(), target_language):
			special_cases.append(sc)
	return special_cases


def get_special_cases_from_checkout(source_tree_path, target_language):
	# type: (str, str) -> List[SpecialCase]
	"""
	Process *.univention-l10n files in the whole branch. Currently they
	lay 3 (UCS@school) or 4(UCS) directory levels deep in the repository.
	"""
	special_cases = []  # type: List[SpecialCase]
	sc_files = glob(os.path.join(source_tree_path, '*/*/debian/*.univention-l10n')) or glob(os.path.join(source_tree_path, '*/debian/*.univention-l10n'))
	if not sc_files:
		raise NoSpecialCaseDefintionsFound()
	for definition_path in sc_files:
		special_cases.extend([sc for sc in read_special_case_definition(definition_path, source_tree_path, target_language)])

	return special_cases


def find_base_translation_modules(startdir, source_dir, module_basefile_name):
	# type: (str, str, str) -> List[BaseModule]
	print('looking in %s' % source_dir)
	print('looking for files matching %s' % module_basefile_name)
	os.chdir(source_dir)
	matches = []  # type: List[str]
	for root, dirnames, filenames in os.walk('.'):
		dirnames[:] = [d for d in dirnames if os.path.join(root, d) not in DIR_BLACKLIST]
		matches.extend(os.path.abspath(os.path.join(root, fn)) for fn in filenames if fn.endswith(module_basefile_name))

	base_translation_modules = []  # type: List[BaseModule]

	regex = re.compile(r".*/(.*)/debian/.*%s$" % re.escape(module_basefile_name))
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
			module = {
				'module_name': modulename,
				'binary_package_name': packagename,
				'abs_path_to_src_pkg': os.path.abspath(package_dir),
				'relative_path_src_pkg': os.path.relpath(package_dir),
			}  # type: BaseModule
			base_translation_modules.append(module)
		else:
			print("could not obtain packagename from directory %s" % match)

	os.chdir(startdir)
	return base_translation_modules


def write_debian_rules(debian_dir_path):
	# type: (str) -> None
	with open(os.path.join(debian_dir_path, 'rules'), 'w') as f:
		f.write("""#!/usr/bin/make -f
#
# Copyright 2016-{year} Univention GmbH
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

override_dh_auto_test:
	ucslint -m 0008
	dh_auto_test

%:
	dh $@""".format(year=date.today().year))


def create_new_package(new_package_dir, target_language, target_locale, language_name, startdir):
	# type: (str, str, str, str, str) -> None
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
 <https://www.gnu.org/licenses/>.""".format(years=date.today().year))  # noqa: E101

	with open(os.path.join(new_package_dir_debian, 'changelog'), 'w') as f:
		f.write("""%s (1.0.0-1) unstable; urgency=low

  * Initial release

 -- %s <%s@%s>  %s""" % (translation_package_name, translation_creator, translation_creator, translation_host, formatdate()))  # noqa: E101

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
 refer to: https://www.univention.de/""" % (translation_package_name, translation_creator, translation_creator, socket.getfqdn(), translation_package_name))  # noqa: E101
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
