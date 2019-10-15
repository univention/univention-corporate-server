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
	if len(args) != 2 or '--help' in args or '-h' in args:
		print('usage: create_localized_country_labels.py <languageCode> <outfile.json>', file=sys.stderr)
		sys.exit(1)

	print('generating country label data...')
	countries = _util.get_country_code_to_geonameid_map(3)
	country_ids = set(countries.values())
	labels = _util.get_localized_names(country_ids, args[0])
	final_lables = dict([(icountry, labels.get(igeonameid, '')) for icountry, igeonameid in countries.items()])
	with open(args[1], 'w') as outfile:
		json.dump(final_lables, outfile)
	print('... done :)')
