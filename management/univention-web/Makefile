#!/usr/bin/make -f
#
# Univention Management Console Frontend Package
#  Makefile for building/installing the package
#
# Copyright 2011-2017 Univention GmbH
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

DOJO_DIR:=/usr/share/univention-dojo
VERSION:=$(shell dpkg-parsechangelog | sed -ne 's/^Version: //p')
BUILD_DIR:=$(CURDIR)/build
TESTS_DIR:=$(CURDIR)/tests
JS_FILES:=$(shell find js -name "*.js")
I18N_FILES= $(addprefix js/, de.json en.json de.po en.po)
TMP_I18N_FILES= $(addprefix $(TMP_DIR)/umc/i18n/, en/app.json de/app.json)

TMP_DIR:=$(CURDIR)/tmp
TMP_JS_FILES:=$(patsubst js/%, $(TMP_DIR)/umc/%, $(TMP_DIR))
THEME_REPO=css
TMP_THEME_DIR=$(TMP_DIR)/dijit/themes/umc
STYL_FILES:=$(shell find $(THEME_REPO) -name "*.styl")
TMP_STYL_FILES:=$(STYL_FILES:$(THEME_REPO):$(TMP_THEME_DIR))
TMP_CSS_FILES:=$(TMP_STYL_FILES:.styl:.css)
BUILD_THEME_DIR=$(BUILD_DIR)/dijit/themes/umc
BUILD_IMAGE_DIRS=$(addprefix $(BUILD_THEME_DIR)/, images form/images layout/images)
TMP_THEME_CSS=$(TMP_THEME_DIR)/$(CSS_FILE_NAME)
CSS_FILE_NAME=umc.css
ICONS_DIR=/usr/share/univention-management-console-frontend/js/dijit/themes/umc/icons

JS_INSTALL_DIR:=usr/share/univention-web/js
THEME_INSTALL_DIR=$(JS_INSTALL_DIR)/dijit/themes/umc

.PHONY: build-dev install clean

build: $(BUILD_DIR)/dojo/dojo.js build-css

build-dev: $(TMP_DIR) $(TMP_JS_FILES) $(TMP_DIR)/umc/_all.js $(TMP_I18N_FILES) $(TMP_DIR)/umc/i18n/en/branding.json build-css $(TMP_DIR)/dijit/themes/umc/icons

build-css: $(BUILD_THEME_DIR)/umc.css $(BUILD_THEME_DIR)/fonts $(BUILD_IMAGE_DIRS)

# shortcut rule
i18n: js/de.po js/en.po

tmp-css: $(TMP_THEME_DIR) $(TMP_THEME_DIR)/bootstrap.css $(addprefix $(TMP_THEME_DIR)/images/,icons-white.svg icons-small-white.svg icons.png icons-small.png icons-white.png icons-small-white.png univention-white.svg home-white.svg) $(TMP_THEME_DIR)/fonts


$(TMP_DIR):
	# copy dojo and dijit files into tmp dir; remove util dir
	mkdir -p $@
	cp -rf $(DOJO_DIR)/* $@
	rm -rf $@/util
	# copy univention JS files into the tmp dir
	cp -rfs "$(CURDIR)/js" $@/umc

$(TMP_THEME_DIR): $(TMP_DIR)
	# link theme files into the tmp dir
	cp -fsr $(PWD)/$(THEME_REPO) $@

# automatically create SVG files with white icons
%-white.svg: %.svg
	sed 's/\#282828/\#ffffff/g' $< > $@

%.png: %.svg
	convert -background transparent "$<" "$@"

$(BUILD_THEME_DIR)/fonts $(TMP_THEME_DIR)/fonts: roboto.zip
	mkdir -p $@
	unzip -o $< -d $@

%/bootstrap.css: bootstrap.zip
	unzip -o -j $< "*bootstrap.css" -d $(TMP_THEME_DIR)
	sed -i '/font-size: 10px/d' $@;

$(BUILD_IMAGE_DIRS)::
	mkdir -p $(@D)
	src=$@; \
	src=$(TMP_THEME_DIR)$${src#$(BUILD_THEME_DIR)}; \
	cp -rL $$src $@

$(BUILD_THEME_DIR)/umc.css: tmp-css
	# generate source maps
	for idir in . form layout site; do \
		cd $(TMP_THEME_DIR)/$$idir; \
		stylus --sourcemap . ; \
	done
	# Workaround: mark several commands as comments (/*TMP ... */)
	# to avoid parse errors with stylus
	sed -i 's/.*\(^\s\+#\|filter: alpha\|filter:\|top: expression\).*/\/\*TMP\0\*\//; /\/\*TMP/ { s|/\*[^*]*\*/\*/|*/| }' $$(find $(TMP_DIR)/dojo $(TMP_DIR)/dijit -name "*.css")
	# compile all .css files into one big file
	mkdir -p $(@D)
	stylus --resolve-url --include-css -o $(@D) $(TMP_THEME_CSS)
	# Workaround: remove the temporarily commented lines
	sed -i 's|/\*TMP\(.*\)\*/|\1|' $@

$(TMP_DIR)/umc/_all.js:
	# generate a pseudo module which contains references to all other JS modules
	deps=$$(find js/ -name "*.js" -a -not -name "*.*.js" | sort | sed 's/\.js//; s/^js/umc/; s/i18n$$/i18n!/; s/.*/"\0",/; $$ s/,$$//'); \
	echo "define([$$deps], function() { })" > $@

$(TMP_DIR)/dijit/themes/umc/icons:
	cp -rfs $(ICONS_DIR) $@

$(TMP_DIR)/umc/package.json: debian/changelog
	mkdir -p $(@D)
	sed 's/%VERSION%/$(VERSION)/' package.json > $@

# manually define dependencies between JSON translation files
# and add a more generic rule for copying JSON translation file
$(TMP_DIR)/umc/i18n/de/app.json: js/de.json
$(TMP_DIR)/umc/i18n/en/app.json: js/en.json
$(TMP_DIR)/umc/i18n/%/app.json:
	# install JSON translation at correct position
	mkdir -p $(@D)
	cp $< $@

$(I18N_FILES):: $(JS_FILES)
	# update .po files and convert .po to .json files (in one go)
	lang=$(@F); \
	lang=$${lang%.*}; \
	/usr/bin/dh-umc-translate -p univention-web-js -l $$lang -o $(@D) $^

$(BUILD_DIR)/dojo/dojo.js: build_profile.js $(TMP_JS_FILES) $(TMP_DIR) $(TMP_I18N_FILES) $(TMP_DIR)/umc/_all.js $(TMP_DIR)/umc/i18n/en/branding.json $(TMP_DIR)/umc/package.json
	# main dojo build process
	mkdir -p $(BUILD_DIR)
	/usr/share/univention-dojo/util/buildscripts/build.sh profile=build_profile.js version="$(VERSION)"

$(TMP_DIR)/umc/i18n/en/branding.json:
	# create empty branding localisation files to not cause 404 errors
	mkdir -p $(@D)
	touch "$@"

install: build
	# copy all files for univention-web-js
	cd $(BUILD_DIR); find . -type d -exec install -m0755 -d $(CURDIR)/debian/univention-web-js/$(JS_INSTALL_DIR)/{} \;
	cd $(BUILD_DIR); find . -type f -exec install -m0644 {} $(CURDIR)/debian/univention-web-js/$(JS_INSTALL_DIR)/{} \;
	rm -rf $(CURDIR)/debian/univention-web-js/$(JS_INSTALL_DIR)/dijit/themes/umc
	# copy all files for univention-web-style
	cd $(BUILD_DIR); find dijit/themes/umc -type d -exec install -m0755 -d $(CURDIR)/debian/univention-web-style/$(JS_INSTALL_DIR)/{} \;
	cd $(BUILD_DIR); find dijit/themes/umc -type f -exec install -m0644 {} $(CURDIR)/debian/univention-web-style/$(JS_INSTALL_DIR)/{} \;

clean:
	rm -rf $(TMP_DIR) $(BUILD_DIR) js/de.json js/en.json
