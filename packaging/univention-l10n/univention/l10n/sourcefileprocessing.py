#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Generate gettext Portable Objects and message catalogs (gettext MO and a
Univention specific JSON-based format) from multiple source files by file type.
"""
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
from __future__ import absolute_import
from lxml import etree
import os
from . import message_catalogs
import polib

from . import umc
try:
	from typing import Iterable, List  # noqa: F401
except ImportError:
	pass


class UnsupportedSourceType(Exception):
	pass


class SourceFileSet(object):

	def __init__(self, src_pkg_path, binary_pkg_name, files):
		# type: (str, str, Iterable[str]) -> None
		self.files = files
		self.src_pkg_path = src_pkg_path
		self.binary_pkg_name = binary_pkg_name

	def process_po(self, pot_path):
		# type: (str) -> None
		self._create_po_template(pot_path)

	def process_target(self, po_path, output_path):
		# type: (str, str) -> None
		if os.path.isabs(output_path):
			output_path = os.path.relpath(output_path, '/')
		output_path = os.path.join(os.getcwd(), 'debian', self.binary_pkg_name, output_path)
		self._compile(po_path, output_path)

	def _create_po_template(self, pot_path):
		# type: (str) -> None
		raise NotImplementedError()

	def _compile(self, po_path, output_path):
		# type: (str, str) -> None
		raise NotImplementedError()


class SourceFilesXgettext(SourceFileSet):

	def _create_po_file(self, gettext_lang, pot_path):
		# type: (str, str) -> None
		umc.create_po_file(pot_path, self.binary_pkg_name, self.files, language=gettext_lang)

	def _compile(self, po_path, mo_output_path):
		# type: (str, str) -> None
		umc.create_mo_file(po_path, mo_output_path)


class SourceFilesShell(SourceFilesXgettext):

	def _create_po_template(self, pot_path):
		# type: (str) -> None
		super(SourceFilesShell, self)._create_po_file('Shell', pot_path)


class SourceFilesPython(SourceFilesXgettext):

	def _create_po_template(self, pot_path):
		# type: (str) -> None
		super(SourceFilesPython, self)._create_po_file('Python', pot_path)


class SourceFilesJavaScript(SourceFilesXgettext):

	def _create_po_template(self, pot_path):
		# type: (str) -> None
		super(SourceFilesJavaScript, self)._create_po_file('JavaScript', pot_path)

	def _compile(self, po_path, json_output_path):
		# type: (str, str) -> None
		"""With UMC and univention-web based applications a custom, JSON-based
		message format is used."""
		umc.po_to_json(po_path, json_output_path)


class SourceFilesHTML(SourceFileSet):

	def _create_po_template(self, pot_path):
		# type: (str) -> None
		po_template = polib.POFile()
		html_parser = etree.HTMLParser()
		js_paths = []  # type: List[str]
		for html_path in self.files:
			with open(html_path, 'rb') as html_file:
				tree = etree.parse(html_file, html_parser)

			for element in tree.xpath('//*[@data-i18n]'):
				msgid = element.get('data-i18n')
				loc = (os.path.basename(html_path), element.sourceline)
				entry = po_template.find(msgid)
				if entry:
					if loc not in entry.occurrences:
						entry.occurrences.append(loc)
				else:
					new_entry = polib.POEntry(msgid=msgid, occurrences=[loc])
					po_template.append(new_entry)

			if tree.xpath('//script'):
				js_paths.append(html_path)

		po_template.save(pot_path)

		# Inline JavaScript may use underscorce function, e.g. univention/management/index.html
		if js_paths:
			message_catalogs.join_existing('JavaScript', pot_path, js_paths)

	def _compile(self, po_path, json_output_path):
		# type: (str, str) -> None
		umc.po_to_json(po_path, json_output_path)


class SourceFileSetCreator(object):

	process_by_type = {
		'text/x-shellscript': SourceFilesShell,
		'text/x-python': SourceFilesPython,
		'text/html': SourceFilesHTML,
		'application/javascript': SourceFilesJavaScript}

	@classmethod
	def from_mimetype(cls, src_pkg_path, binary_pkg_name, mimetype, files):
		# type: (str, str, str, Iterable[str]) -> SourceFileSet
		try:
			obj = cls.process_by_type[mimetype](src_pkg_path, binary_pkg_name, files)
		except KeyError:
			raise UnsupportedSourceType(files)
		else:
			return obj


def from_mimetype(src_pkg_path, binary_pkg_name, mimetype, files):
	# type: (str, str, str, Iterable[str]) -> SourceFileSet
	return SourceFileSetCreator.from_mimetype(src_pkg_path, binary_pkg_name, mimetype, files)
