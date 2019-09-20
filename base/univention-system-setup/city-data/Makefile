#!/usr/bin/make -f
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

.PHONY: build install clean

# NOTE:
#   In order to update json data files, run 'make clean; make'
#   In order to support l10n for other languages, extend the list LANGUAGES
LANGUAGES := de en
JSON_FILES := country_data.json city_data.json

build: $(JSON_FILES)

clean:
	rm -f alternateNames.txt cities15000.txt $(JSON_FILES)

install: build
	@echo "Nothing to install"

%.txt: %.zip
	unzip -u -d "$(*D)" $<

country_data.json: countryInfo.txt alternateNames.txt
	./create_country_data.py "$@" $(LANGUAGES)

city_data.json: cities15000.txt alternateNames.txt
	./create_city_data.py "$@" $(LANGUAGES)

alternateNames.zip:
	wget https://updates.software-univention.de/download/large-build-files/alternateNames.zip
	echo 'b2592ddda5484bb7a7b0724543ac7dbf5db9a3f5cb47dd1d4bc358e6afda324be55ed9a42355309e7a2ba20c710abd839daa4174cb97947c57abdbead132a1cf  alternateNames.zip' | sha512sum -c
