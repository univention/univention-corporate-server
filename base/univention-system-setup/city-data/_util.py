#!/usr/bin/python2.7
#
# Copyright 2012-2019 Univention GmbH
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

import os
import sys
import json


def _get_path(filename):
	for ipath in (
		os.path.join(os.path.dirname(sys.argv[0]), filename),
		filename,
	):
		if os.path.exists(ipath):
			return ipath
	raise RuntimeError('Cannot find data file %s' % filename)


def get_country_codes(countryCodeKeyType=2):
	if countryCodeKeyType == 2:
		idx1 = 0
		idx2 = 1
	elif countryCodeKeyType == 3:
		idx1 = 1
		idx2 = 0
	else:
		raise ValueError('Unknown countryCodeKeyType (=%s), only 2 or 3 allowed' % countryCodeKeyType)

	with open(_get_path('countryInfo.txt')) as infile:
		pairs = {}
		for line in infile:
			if line.startswith('#'):
				continue
			parts = line.split('\t')
			pairs[parts[idx1]] = parts[idx2]
		return pairs


def get_country_code_to_geonameid_map(countryCodeType=2):
	countries = {}
	if countryCodeType == 2:
		countryCodeIndex = 0
	elif countryCodeType == 3:
		countryCodeIndex = 1
	else:
		raise ValueError('Unknown countryCodeType (=%s), only 2 or 3 allowed' % countryCodeType)

	with open(_get_path('countryInfo.txt')) as infile:
		for line in infile:
			if line.startswith('#'):
				continue
			parts = line.split('\t')
			countries[parts[countryCodeIndex]] = parts[16].strip()
	return countries


def get_country_default_language(countryCodeType=2):
	if countryCodeType == 2:
		countryCodeIndex = 0
	elif countryCodeType == 3:
		countryCodeIndex = 1
	else:
		raise ValueError('Unknown countryCodeType (=%s), only 2 or 3 allowed' % countryCodeType)

	with open(_get_path('countryInfo.txt')) as infile:
		locales = {}
		for line in infile:
			if line.startswith('#'):
				continue

			parts = line.split('\t')
			languages = parts[15]
			if not languages.strip():
				continue

			default_lang = languages.split(',')[0]
			default_lang = default_lang.split('-')[0]
			country_code = parts[countryCodeIndex]
			locales[country_code] = default_lang

	return locales


def get_city_geonameid_to_country_code_map():
	cities = {}
	with open(_get_path('cities15000.txt')) as infile:
		for line in infile:
			parts = line.split('\t')
			cities[parts[0]] = parts[8].strip()
	return cities


def get_city_data():
	cities = {}
	with open(_get_path('cities15000.txt')) as infile:
		for line in infile:
			parts = line.split('\t')
			cities[parts[0]] = dict(
				country=parts[8].strip(),
				timezone=parts[17].strip(),
				population=int(parts[14]),
			)
	return cities


def get_localized_names(geonameids, lang):
	labels = {}
	label_score = {}
	with open(_get_path('alternateNames.txt')) as infile:
		for line in infile:
			parts = line.split('\t')
			iid = parts[1]
			ilang = parts[2]
			ilabel = parts[3]
			isprefered = bool(parts[4])
			isshort = bool(parts[5])

			if ilang == lang and iid in geonameids:
				iscore = isshort + 2 * isprefered
				if iscore >= label_score.get(iid, 0):
					labels[iid] = ilabel
					label_score[iid] = iscore
	return labels


def get_alternate_names(geonameids, *locales):
	labels = []
	with open(_get_path('alternateNames.txt')) as infile:
		for line in infile:
			parts = line.split('\t')
			iid = parts[1]
			ilabel = parts[3]
			ilang = parts[2]

			if iid in geonameids and (not ilang or ilang in locales):
				labels.append((iid, ilabel))
	return labels


def get_timezones():
	with open(_get_path('timeZones.txt')) as infile:
		countries = {}
		for line in infile:
			parts = line.split('\t')
			countries[parts[0]] = dict(id=parts[1], offset=parts[4])
		return countries


def get_country_code_to_nameserver_map():
	with open(_get_path('nameservers.json')) as infile:
		data = json.load(infile)
		mapping = {}
		for ientry in data:
			country = ientry['country_id']
			if not country:
				continue

			imapEntry = mapping.setdefault(country, dict(ipv4=[], ipv4_erroneous=[], ipv6=[], ipv6_erroneous=[]))
			ip = ientry['ip']
			has_error = ientry['error']
			idx = ''
			if ':' in ip:
				idx = 'ipv6'
				if has_error:
					idx = 'ipv6_erroneous'
			else:
				idx = 'ipv4'
				if has_error:
					idx = 'ipv4_erroneous'

			imapEntry[idx].append(ientry['ip'])

	return mapping
