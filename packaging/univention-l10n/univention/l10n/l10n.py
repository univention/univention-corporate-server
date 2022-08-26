#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2013-2022 Univention GmbH
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

import getpass
import json
import mimetypes
import os
import re
import shutil
import socket
import sys
import traceback
from datetime import date
from email.utils import formatdate
from glob import glob

import magic
from debian.deb822 import Deb822

from . import message_catalogs, sourcefileprocessing, umc
from .helper import Error, make_parent_dir
try:
	from typing import Any, Dict, Iterable, Iterator, List, Optional, Pattern, Tuple, Type  # noqa: F401
	from types import TracebackType  # noqa: F401
	from mypy_extensions import TypedDict
	BaseModule = TypedDict('BaseModule', {'module_name': str, 'package': str, 'abs_path_to_src_pkg': str, 'relative_path_src_pkg': str})
except ImportError:
	pass


REFERENCE_LANG = 'de'
UMC_MODULES = '.umc-modules'
# Use this set to ignore whole sub trees of a given source tree
DIR_BLACKLIST = {
	'doc',
	'umc-module-templates',
	'test',
	'testframework',
}
# do not translate modules with these names, as they are examples and thus not worth the effort
MODULE_BLACKLIST = {
	'PACKAGENAME',
}


class NoSpecialCaseDefintionsFound(Error):
	pass


class NoMatchingFiles(Error):
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
		umc_module_definition_file = os.path.join(module['abs_path_to_src_pkg'], 'debian', '{}{}'.format(module['module_name'], UMC_MODULES))
		with open(umc_module_definition_file, 'r') as fd:
			def_file = fd.read()

		attributes = Deb822(def_file)
		attributes = dict((k, [v]) for k, v in attributes.items())  # simulate dh_ucs.parseRfc822 behaviour
		attributes.update(module)
		return attributes

	@classmethod
	def _get_core_module_from_source_package(cls, module, target_language):
		# type: (BaseModule, str) -> UMCModuleTranslation
		attrs = cls._read_module_attributes_from_source_package(module)
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

	RE_L10N = re.compile(r'(.+/)?debian/([^/]+).univention-l10n$')

	def __init__(self, special_case_definition, source_dir, path_to_definition, target_language):
		# type: (Dict[str, str], str, str, str) -> None
		# FIXME: this would circumvent custom getters and setter?
		self.__dict__.update(special_case_definition)
		def_relative = os.path.relpath(path_to_definition, start=source_dir)
		matches = self.RE_L10N.match(def_relative)
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

		regexs = []  # type: List[Pattern[str]]
		for pattern in [os.path.join(src_pkg_path, pattern) for pattern in self.input_files]:
			try:
				regexs.append(re.compile(r'{}$'.format(pattern)))
			except re.error:
				sys.exit("Invalid input_files statement in: {}. Value must be valid regular expression.".format(self.path_to_definition))

		matched = [
			path
			for parent, dirnames, fnames in os.walk(src_pkg_path)
			for path in (os.path.join(parent, fn) for fn in fnames)
			if any(rex.match(path) for rex in regexs)
		]
		if not matched:
			raise NoMatchingFiles()

		return matched

	def get_source_file_sets(self):
		# type: () -> List[sourcefileprocessing.SourceFileSet]
		files_by_mime = {}  # type: Dict[str, List[str]]
		with MIMEChecker() as mime:
			for file_path in self._get_files_matching_patterns():
				files_by_mime.setdefault(mime.get(file_path), []).append(file_path)

		source_file_sets = []  # type: List[sourcefileprocessing.SourceFileSet]
		for mime_type, file_set in files_by_mime.items():
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
		'.ts': 'application/javascript',
		'.vue': 'application/javascript',
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


def update_package_translation_files(module, output_dir, template=False):
	# type: (UMCModuleTranslation, str, bool) -> None
	print("Creating directories and PO files for {module_name} in translation source package".format(**module))
	start_dir = os.getcwd()
	output_dir = os.path.abspath(output_dir)
	try:
		os.chdir(module['abs_path_to_src_pkg'])
		if not module.get('core'):

			def _create_po_files(po_files, src_files, language):
				# type: (Iterable[str], Iterable[str], str) -> None
				for po_file in po_files:
					po_path = os.path.join(output_dir, module['relative_path_src_pkg'], po_file)
					make_parent_dir(po_path)
					umc.create_po_file(po_path, module['module_name'], src_files, language, template)

			# build Python po files
			_create_po_files(module.python_po_files, module.python_files, 'Python')
			_create_po_files(module.js_po_files, module.js_files, 'JavaScript')

		# xml always has to be present
		for lang, po_file in module.xml_po_files:
			po_path = os.path.join(output_dir, module['relative_path_src_pkg'], po_file)
			make_parent_dir(po_path)
			umc.module_xml2po(module, po_path, lang, template)

	except OSError as exc:
		print(traceback.format_exc())
		print("error in update_package_translation_files: %s" % (exc,))
		raise Error("update_package_translation_files() failed")
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
		fd.write('ALL_TARGETS := {}\n\n'.format(' \\\n\t'.join(sorted(mo_targets_list))))
		fd.write('\n'.join(sorted(target_prerequisite)))
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
	return [
		sc
		for sc_definitions in special_case_files
		for sc in read_special_case_definition(sc_definitions, os.getcwd(), target_language)
	]


def get_special_cases_from_checkout(source_tree_path, target_language):
	# type: (str, str) -> List[SpecialCase]
	"""
	Process \\*.univention-l10n files in the whole branch. Currently they
	lay 3 (UCS@school) or 4(UCS) directory levels deep in the repository.
	"""
	sc_files = glob(os.path.join(source_tree_path, '*/*/debian/*.univention-l10n')) or glob(os.path.join(source_tree_path, '*/debian/*.univention-l10n'))
	if not sc_files:
		raise NoSpecialCaseDefintionsFound()
	return [
		sc
		for definition_path in sc_files
		for sc in read_special_case_definition(definition_path, source_tree_path, target_language)
	]


def find_base_translation_modules(source_dir):
	# type: (str) -> List[BaseModule]
	base_translation_modules = []  # type: List[BaseModule]

	print('looking in %s' % source_dir)
	for root, dirnames, filenames in os.walk(os.path.abspath(source_dir)):
		dirnames[:] = [d for d in dirnames if d not in DIR_BLACKLIST]
		(package_dir, tail) = os.path.split(root)
		if tail != "debian":
			continue
		for fn in filenames:
			(modulename, tail) = os.path.splitext(fn)
			if tail != UMC_MODULES:
				continue
			if modulename in MODULE_BLACKLIST:
				print("Ignoring module %s: Module is blacklisted\n" % modulename)
				continue

			print("Found package: %s" % package_dir)
			module = {
				'module_name': modulename,
				'package': modulename,
				'abs_path_to_src_pkg': package_dir,
				'relative_path_src_pkg': os.path.relpath(package_dir, source_dir),
			}  # type: BaseModule
			base_translation_modules.append(module)

	return base_translation_modules


def template_file(dst, fn, values):
	# type: (str, str, Dict[str, str]) -> None
	"""
	Render file from template file by filling in values.

	:param dst: Destination path.
	:param fn: File name for destination file and source template with `.tmpl` suffix.
	:param values: A dictionary with the values.
	"""
	with open(os.path.join(os.path.dirname(__file__), fn + ".tmpl"), "r") as f:
		tmpl = f.read()

	with open(os.path.join(dst, fn), 'w') as f:
		f.write(tmpl.format(**values))


def create_new_package(new_package_dir, target_language, target_locale, language_name, startdir):
	# type: (str, str, str, str, str) -> None
	new_package_dir_debian = os.path.join(new_package_dir, 'debian')
	if not os.path.exists(new_package_dir_debian):
		print("creating directory: %s" % new_package_dir_debian)
		os.makedirs(new_package_dir_debian)

	translation = dict(
		name=language_name,
		package_name=os.path.basename(new_package_dir),
		creator=getpass.getuser(),
		host=socket.getfqdn(),
		date=formatdate(),
		years=date.today().year,
	)

	template_file(new_package_dir, "Makefile", translation)
	for fn in ("copyright", "changelog", "control", "compat", "rules"):
		template_file(new_package_dir_debian, fn, translation)

	with open(os.path.join(new_package_dir_debian, '%(package_name)s.postinst' % translation), 'w') as f:
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

	# Move source files and installed .mo files to new package dir
	if os.path.exists(os.path.join(new_package_dir, 'usr')):
		shutil.rmtree(os.path.join(new_package_dir, 'usr'))
	# shutil.copytree(os.path.join(startdir, 'usr'), os.path.join(new_package_dir, 'usr'))
	# shutil.rmtree(os.path.join(startdir, 'usr'))

	if os.path.exists(os.path.join(new_package_dir, target_language)):
		shutil.rmtree(os.path.join(new_package_dir, target_language))
	shutil.copytree(os.path.join(startdir, target_language), os.path.join(new_package_dir, target_language))
	shutil.rmtree(os.path.join(startdir, target_language))
