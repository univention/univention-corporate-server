#!/usr/bin/python2.7
#
# Copyright 2014-2015 Univention GmbH
#
# http://www.univention.de/
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
# <http://www.gnu.org/licenses/>.

import sys
import simplejson as json
import _util

if __name__ == '__main__':
	# check argument (action)
	args = sys.argv[1:]
	if not len(args) or '--help' in args or '-h' in args:
		print >>sys.stderr, 'options: <outfile.json> <locale1> [<locale2>...]'
		sys.exit(1)

	locales = args[1:]

	print 'generating country data...'
	country_data = {}

	country_default_lang = _util.get_country_default_language()
	for icountry, ilang in country_default_lang.iteritems():
		country_data.setdefault(icountry, {})['default_lang'] = ilang

	nameservers = _util.get_country_code_to_nameserver_map()
	for icountry, iservers in nameservers.iteritems():
		country_data.setdefault(icountry, {}).update(iservers)

	country_code_to_geonameid_map = _util.get_country_code_to_geonameid_map()
	country_geonameids = country_code_to_geonameid_map.values()
	for ilocale in locales + ['']:
		print 'loading data for locale %s' % ilocale
		country_names = _util.get_localized_names(country_geonameids, ilocale)
		for icode, iid in country_code_to_geonameid_map.iteritems():
			data_set = country_data.get(icode)
			if not data_set:
				print '  empty country code: %s' % icode
				continue
			ilabel = country_names.get(iid)
			if ilabel:
				data_set.setdefault('label', dict())[ilocale] = ilabel

	with open(args[0], 'wb') as outfile:
		json.dump(country_data, outfile, indent=2)

	print '... done :)'

