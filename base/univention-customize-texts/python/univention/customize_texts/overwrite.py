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


import os.path
from subprocess import run, PIPE
import json

from univention.customize_texts import get_l10n_info
from univention.customize_texts.rebuild import rebuild

def overwrite(l10n_key, locale, english_text, custom_text):
	l10n_info = get_l10n_info(l10n_key)
	diff_fname = l10n_info.diff_fname(locale)
	try:
		with open(diff_fname) as fd:
			diff = json.load(fd)
	except EnvironmentError:
		diff = {}
	diff[english_text] = custom_text
	if not os.path.exists(os.path.dirname(diff_fname)):
		os.mkdirs(os.path.dirname(diff_fname))
	with open(diff_fname, 'w') as fd:
		json.dump(diff, fd)
	orig_fname = l10n_info.orig_fname(locale)
	dest_fname = l10n_info.get_dest_fname(locale)
	run(['dpkg-divert', '--local', '--rename', '--divert', orig_fname, '--add', dest_fname], stdout=PIPE)
	rebuild([l10n_info])
