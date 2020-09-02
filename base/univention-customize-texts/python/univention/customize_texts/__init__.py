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

L10N_FOLDER = Path("/usr/share/univention-customize-texts/l10n-files")
OVERWRITES_FOLDER = Path("/usr/share/univention-customize-texts/overwrites")


class Texts(object):
	def __init__(self, pkg, locale, orig_fname, diff_fname):
		self.pkg = pkg
		self.locale = locale
		self.orig_fname = orig_fname
		self.diff_fname = diff_fname


def get_customized_texts(l10n_info):
	base_dir = OVERWRITES_FOLDER
	if l10n_info.suffix:
		base_dir = base_dir / '{}:{}'.format(l10n_info.pkg, l10n_info.suffix)
	else:
		base_dir = base_dir / l10n_info.pkg

	orig_path = base_dir / l10n_info.orig_fname()
	diff_path = base_dir / 'diff.json'

	for localedir in base_dir.glob('*'):
		if not localedir.is_dir():
			continue
		locale = localedir.name
		orig_path = localedir / 'orig.json'
		if orig_path.exists():
			orig_fname = orig_path
		else:
			orig_fname = None
		diff_path = localedir / 'diff.json'
		if diff_path.exists():
			diff_fname = diff_path
		else:
			diff_fname = None
		yield Texts(l10n_info.pkg, locale, orig_fname, diff_fname)


class Merger:
	def __init__(self, original_data, diff):
		self.original_data
		self.diff

	def merge(self):
		raise NotImplementedError()


class JsonMerger(Merger):
	def merge(self):
		original = json.loads(self.original_data)
		original.update(self.diff)
		return json.dumps(original)


def find_merger(target_type):
	if target_type == 'json':
		return JsonMerger
	raise TypeError("{} not supported".format(target_type))


class L10NInfo:
	def __init__(self, pkg, suffix, target_type, destination):
		self.pkg = pkg
		self.suffix = suffix
		self.target_type = target_type
		self.destination = destination

	def get_merger(self):
		return find_merger(self.target_type)

	def orig_fname(self):
		return 'orig.{}'.format(self.target_type)


def get_l10n_infos():
	for l10n_file in L10N_FOLDER.glob('*.univention-l10n'):
		with l10n_file.open() as fd:
			content = json.load(fd)
			for entry in content:
				pkg = l10n_file.stem
				suffix = entry.get('key')
				target_type = entry['target_type']
				destination = entry['destination']
				yield L10NInfo(pkg, suffix, target_type, destination)
