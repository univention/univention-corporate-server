#!/usr/bin/make -f
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

.PHONY: build install clean

# extend the list LANGUAGES to support l10n for other languages
LANGUAGES := de en
JSON_FILES := city-data/country_data.json city-data/city_data.json
INITIALSETUP_DE_JSON := var/www/ucs-overview/js/initialsetup/de.json

build: $(JSON_FILES) $(INITIALSETUP_DE_JSON)

clean:
	rm -f city-data/alternateNames.txt city-data/cities15000.txt $(JSON_FILES)
	rm -f $(INITIALSETUP_DE_JSON)

install: build
	@echo "Nothing to install"

%.txt: %.zip
	unzip -u -d "$(*D)" $<

%.json: %.po
	dh-umc-po2json "$<"

%/country_data.json: city-data/countryInfo.txt city-data/alternateNames.txt
	city-data/create_country_data.py "$@" $(LANGUAGES)

%/city_data.json: city-data/cities15000.txt city-data/alternateNames.txt
	city-data/create_city_data.py "$@" $(LANGUAGES)

