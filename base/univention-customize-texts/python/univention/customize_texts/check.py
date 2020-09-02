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


import os
import json
import polib

from univention.customize_texts import OVERWRITES_FOLDER


def mo2json(mofile):
	# type: polib.MOFile
	return {moentry.msgid: moentry.msgstr for moentry in mofile}


def get_orig(path):
	orig_mo_path = os.path.join(path, 'orig.mo')
	if os.path.exists(orig_mo_path):
		mofile = polib.mofile(orig_mo_path)
		orig = mo2json(mofile)
	else:
		orig_json_path = os.path.join(path, 'orig.json')
		with open(orig_json_path, 'r') as fd:
			orig = json.load(fd)
	return orig


def get_diff(path):
	with open(os.path.join(path, 'diff.json'), 'r') as fd:
		diff = json.load(fd)
	return diff


def check():
	res = []
	path = str(OVERWRITES_FOLDER)
	for package in os.listdir(path):
		package_path = os.path.join(path, package)
		for locale in os.listdir(package_path):
			locale_path = os.path.join(package_path, locale)
			orig = get_orig(locale_path)
			diff = get_diff(locale_path)
			for k in diff.keys():
				if k not in orig:
					res.append("* {} {} {}".format(package, locale, k))
	if res:
		print('The following keys do not match')
		for line in res:
			print(line)
