#!/usr/bin/make -f
#
# SPDX-FileCopyrightText: 2014-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

.PHONY: build install clean

#INITIALSETUP_DE_JSON := usr/share/univention-system-setup-boot/www/i18n/de/initialsetup.json
STYL_FILES := $(shell find usr/share -name '*.styl')
CSS_FILES := $(STYL_FILES:.styl=.css)

build: $(CSS_FILES)

clean:
	$(RM) -f $(CSS_FILES)
	$(RM) -f umc/js/*.json

install: build
	@echo "Nothing to install"

%.css: %.styl
	stylus "$<"

%.json: %.po
	dh-umc-po2json "$<"
