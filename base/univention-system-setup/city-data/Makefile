#!/usr/bin/make -f
#
# SPDX-FileCopyrightText: 2014-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

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
