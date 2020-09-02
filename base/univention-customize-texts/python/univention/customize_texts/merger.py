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

import polib

class Merger:
	def __init__(self, original_fname, diff_fname):
		self.original_fname = original_fname
		self.diff_fname = diff_fname

	def get_diff(self):
		with open(str(self.diff_fname)) as fd:
			return json.load(fd)

	def merge(self, destination):
		raise NotImplementedError()


class JsonMerger(Merger):
	def merge(self, destination):
		with open(self.original_fname) as fd:
			original = json.load(fd)
		diff = self.get_diff()
		original.update(diff)
		with open(destination, 'w') as fd:
			json.dump(original, fd)


class MoMerger(Merger):
	def merge(self, destination):
		mo = polib.mofile(self.original_fname)
		diff = self.get_diff()
		for entry in mo:
			key = entry.msgid
			if key in diff:
				entry.msgstr = diff.pop(key)
		mo.save(destination)


def find_merger(target_type):
	if target_type == 'json':
		return JsonMerger
	elif target_type == 'mo':
		return MoMerger
	raise TypeError("{} not supported".format(target_type))
