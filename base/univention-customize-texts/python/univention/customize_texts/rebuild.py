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


from univention.customize_texts import get_l10n_infos, get_customized_texts


def rebuild():
	for l10n_info in get_l10n_infos():
		Merger = l10n_info.get_merger()
		for customized_texts in get_customized_texts(l10n_info):
			destination = l10n_info.get_dest_fname(customized_texts.locale)
			print('Customizing {}'.format(destination))
			destination = l10n_info.get_dest_fname(customized_texts.locale)
			if not customized_texts.orig_fname:
				print("Missing {}. Skipping...".format(customized_texts.orig_fname))
				continue
			if not customized_texts.diff_fname:
				print("No customized texts for {}. Skipping...".format(customized_texts.orig_fname))
				continue
			merger = Merger(customized_texts.orig_fname, customized_texts.diff_fname)
			merger.merge(destination)
			print('Successfully rewritten {}'.format(destination))

