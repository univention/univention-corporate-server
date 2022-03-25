#!/usr/bin/python3
#
# Copyright 2014-2022 Univention GmbH
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

"""
Generate `city_data.json`
"""

from __future__ import print_function

import json
from argparse import ArgumentParser, FileType

import _util

if __name__ == '__main__':
	parser = ArgumentParser(description=__doc__)
	parser.add_argument("outfile", type=FileType("w"))
	parser.add_argument("locales", nargs="+")
	opt = parser.parse_args()

	print('generating city data...')
	city_data = _util.get_city_data()
	city_geonameids = set(city_data.keys())
	for iid, icity in city_data.items():
		icity['id'] = iid

	for ilocale in opt.locales + ['']:
		print('loading data for locale %s' % ilocale)
		city_names = _util.get_localized_names(city_geonameids, ilocale)
		for iid, ilabel in city_names.items():
			city_data[iid].setdefault('label', {})[ilocale] = ilabel

	json.dump(list(city_data.values()), opt.outfile, indent=2)

	print('... done :)')
