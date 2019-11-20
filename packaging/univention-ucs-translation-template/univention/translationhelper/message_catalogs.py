#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""This module collects utilities for installing and building message catalogs
while applying Univention specific options.

Currently this is mostly a wrapper for gettext. In the future it might be
useful to merge parts of dh_umc into it as the UMC uses a custom JSON based
catalog format.
"""
#
# Copyright 2016-2019 Univention GmbH
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
import polib
import os
import subprocess

from . import umc
from .helper import make_parent_dir
try:
	from typing import Any, List, Union  # noqa F401
except ImportError:
	pass


class GettextError(Exception):
	pass


def _clean_header(po_path):
	# type: (str) -> None
	pof = polib.pofile(po_path)
	pof.header = ""
	pof.metadata.update({
		u'Content-Type': u'text/plain; charset=utf-8',
	})
	pof.metadata_is_fuzzy = None
	pof.save(po_path)


def concatenate_po(src_po_path, dest_po_path):
	# type: (str, str) -> None
	_call_gettext(
		'msgcat',
		'--unique',
		src_po_path,
		dest_po_path,
		'-o', dest_po_path)
	backup_file = '{}~'.format(dest_po_path)
	if os.path.isfile(backup_file):
		os.unlink(backup_file)
	_clean_header(dest_po_path)


def create_empty_po(binary_pkg_name, new_po_path):
	# type: (str, str) -> None
	make_parent_dir(new_po_path)
	_call_gettext(
		'xgettext',
		'--force-po',
		'--add-comments=i18n',
		'--from-code=UTF-8',
		'--sort-output',
		'--package-name={}'.format(binary_pkg_name),
		'--msgid-bugs-address=packages@univention.de',
		'--copyright-holder=Univention GmbH',
		# Suppress warning about /dev/null being an unknown source type
		'--language', 'C',
		'-o', new_po_path,
		'/dev/null')
	_clean_header(new_po_path)


def compile_mo(path_to_po, mo_output_path):
	# type: (str, str) -> None
	make_parent_dir(mo_output_path)
	_call_gettext('msgfmt', '--check', '--output={}'.format(mo_output_path), path_to_po)


def merge_po(source_po_path, dest_po_path):
	# type: (str, str) -> None
	_call_gettext(
		'msgmerge',
		'--update',
		'--sort-output',
		dest_po_path,
		source_po_path)
	backup_file = '{}~'.format(dest_po_path)
	if os.path.isfile(backup_file):
		os.unlink(backup_file)


def join_existing(language, output_file, input_files, cwd=os.getcwd()):
	# type: (str, str, Union[str, List[str]], str) -> None
	if not os.path.isfile(output_file):
		raise GettextError("Can't join input files into {}. File does not exist.".format(output_file))
	if not isinstance(input_files, list):
		input_files = [input_files]
	# make input_files relative so the location lines in the resulting po
	# will be relative to cwd
	input_files = [os.path.relpath(p, start=cwd) for p in input_files]
	_call_gettext(
		'xgettext',
		'--from-code=UTF-8',
		'--join-existing',
		'--omit-header',
		'--language', language,
		'-o', output_file,
		*input_files,
		cwd=cwd)


def po_to_json(po_path, json_output_path):
	# type: (str, str) -> None
	umc.create_json_file(po_path)
	make_parent_dir(json_output_path)
	os.rename(po_path.replace('.po', '.json'), json_output_path)


def _call_gettext(*args, **kwargs):
	# type: (*str, **Any) -> None
	try:
		subprocess.check_call(args, **kwargs)
	except subprocess.CalledProcessError as exc:
		raise GettextError("Error: A gettext tool exited unsuccessfully. Attempted command:\n{}".format(exc.cmd))
	except AttributeError as exc:
		raise GettextError("Operating System error during call to a gettext tool:\n{}".format(exc))


def univention_location_lines(pot_path, abs_path_source_pkg):
	# type: (str, str) -> None
	po_file = polib.pofile(pot_path)
	for entry in po_file:
		modified_occ = []
		for path, linenum in entry.occurrences:
			modified_occ.append((os.path.relpath(path, start=abs_path_source_pkg), linenum))
		entry.occurrences = modified_occ
	po_file.save(pot_path)
