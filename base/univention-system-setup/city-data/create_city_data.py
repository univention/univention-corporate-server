#!/usr/bin/python2.7
#
# Copyright 2014-2019 Univention GmbH
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
import sys
import json
import _util

if __name__ == '__main__':
	# check argument (action)
	args = sys.argv[1:]
	if not len(args) or '--help' in args or '-h' in args:
		print('options: <outfile.json> <locale1> [<locale2>...]', file=sys.stderr)
		sys.exit(1)

	locales = args[1:]

	print('generating city data...')
	city_data = _util.get_city_data()
	city_geonameids = set(city_data.keys())
	for iid, icity in city_data.items():
		icity['id'] = iid

	for ilocale in locales + ['']:
		print('loading data for locale %s' % ilocale)
		city_names = _util.get_localized_names(city_geonameids, ilocale)
		for iid, ilabel in city_names.items():
			city_data[iid].setdefault('label', dict())[ilocale] = ilabel

	with open(args[0], 'wb') as outfile:
		json.dump(list(city_data.values()), outfile, indent=2)

	print('... done :)')
