#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Univention App Center
#  Setup file for packaging
#
# Copyright 2020 Univention GmbH
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
#


import json
from pathlib import Path

from univention.customize_texts.merger import find_merger

L10N_FOLDER = Path("/usr/share/univention-customize-texts/l10n-files")
OVERWRITES_FOLDER = Path("/usr/share/univention-customize-texts/overwrites")


class Texts(object):
	def __init__(self, pkg, locale, orig_fname, diff_fname):
		self.pkg = pkg
		self.locale = locale
		self.orig_fname = orig_fname
		self.diff_fname = diff_fname

def get_customized_texts_for_locale(l10n_info, locale):
	orig_fname = l10n_info.orig_fname(locale)
	diff_fname = l10n_info.diff_fname(locale)
	return Texts(l10n_info.pkg, locale, orig_fname, diff_fname)


def get_customized_texts(l10n_info):
	base_dir = OVERWRITES_FOLDER
	if l10n_info.suffix:
		base_dir = base_dir / '{}:{}'.format(l10n_info.pkg, l10n_info.suffix)
	else:
		base_dir = base_dir / l10n_info.pkg

	for localedir in base_dir.glob('*'):
		locale = localedir.name
		texts = get_customized_texts_for_locale(l10n_info, locale)
		if texts:
			yield texts


class L10NInfo:
	def __init__(self, pkg, suffix, target_type, destination):
		self.pkg = pkg
		self.suffix = suffix
		self.target_type = target_type
		self.destination = destination

	def get_merger(self):
		return find_merger(self.target_type)

	def orig_fname(self, locale):
		return '{}.orig'.format(self.get_dest_fname(locale))

	def diff_fname(self, locale):
		if self.suffix:
			base_dir = OVERWRITES_FOLDER / '{}:{}'.format(self.pkg, self.suffix)
		else:
			base_dir = OVERWRITES_FOLDER / self.pkg
		return str(base_dir / locale / 'diff.json')

	def get_dest_fname(self, locale):
		return self.destination.format(lang=locale)


def get_l10n_infos():
	for l10n_file in L10N_FOLDER.glob('*.univention-l10n'):
		with l10n_file.open() as fd:
			content = json.load(fd)
			for entry in content:
				pkg = l10n_file.stem
				suffix = entry.get('key')
				target_type = entry['target_type']
				destination = '/' + entry['destination']
				yield L10NInfo(pkg, suffix, target_type, destination)
