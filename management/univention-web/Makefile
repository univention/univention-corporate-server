#!/usr/bin/make -f
#
# Univention Management Console Frontend Package
#  Makefile for building/installing the package
#
# Copyright 2011-2016 Univention GmbH
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

PKG_DIR:=/usr/share/univention-web/js/
DOJO_DIR:=/usr/share/univention-dojo
VERSION:=$(shell dpkg-parsechangelog | sed -ne 's/^Version: //p')
BUILD_DIR:=$(CURDIR)/build
TESTS_DIR:=$(CURDIR)/tests
JS_FILES:=$(shell find umc -name "*.js")
TMP_JS_FILES:=$(shell find tmp -name "*.js")
I18N_FILES= $(addprefix umc/, de.json en.json de.po en.po)
TMP_I18N_FILES= $(addprefix $(TMP_DIR)/umc/i18n/, en/app.json de/app.json)

TMP_DIR:=$(CURDIR)/tmp
THEME_REPO=dijit-claro-stylus
TMP_THEME_DIR=$(TMP_DIR)/dijit/themes/umc
STYL_FILES:=$(shell find $(THEME_REPO) -name "*.styl")
TMP_STYL_FILES:=$(STYL_FILES:$(THEME_REPO):$(TMP_THEME_DIR))
TMP_CSS_FILES:=$(TMP_STYL_FILES:.styl:.css)
BUILD_THEME_DIR=$(BUILD_DIR)/dijit/themes/umc
BUILD_IMAGE_DIRS=$(addprefix $(BUILD_THEME_DIR)/, images form/images layout/images)
TMP_THEME_CSS=$(TMP_THEME_DIR)/umc.css
THEME_INSTALL_DIR=/usr/share/univention-web/js/dijit/themes/umc

.PHONY: build-dev install clean jslint

#.PRECIOUS: $(BUILD_DIR)

build: build-js build-css

build-js: $(BUILD_DIR)/dojo/dojo.js

build-common-js: $(TMP_DIR) $(BUILD_DIR) $(TMP_I18N_FILES) $(TMP_DIR)/umc/_all.js $(TMP_DIR)/umc/i18n/en/branding.json $(BUILD_DIR)/umc/package.json

build-css: $(BUILD_THEME_DIR)/umc.css $(BUILD_THEME_DIR)/fonts $(BUILD_IMAGE_DIRS)

tmp-css: $(TMP_THEME_DIR) $(TMP_THEME_DIR)/bootstrap.css $(addprefix $(TMP_THEME_DIR)/images/,icons-white.svg icons-small-white.svg icons.png icons-small.png icons-white.png icons-small-white.png)

$(BUILD_DIR):
	mkdir -p $@

$(TMP_DIR):
	# copy dojo and dijit files into tmp dir; remove util dir
	mkdir -p $@
	cp -rf $(DOJO_DIR)/* $@
	rm -rf $@/util
	# copy univention JS files into the tmp dir
	cp -rfs "$(CURDIR)/umc" $@

$(TMP_THEME_DIR): $(TMP_DIR)
	# copy theme files into the tmp dir
	cp -r $(PWD)/$(THEME_REPO) $@
	# mv claro.css to umc.css and replace '.claro' selector with '.umc'
	mv $(TMP_THEME_DIR)/claro.css $(TMP_THEME_CSS)

# automatically create SVG files with white icons
%-white.svg: %.svg
	sed 's/\#282828/\#ffffff/g' $< > $@

%.png: %.svg
	convert -background transparent "$<" "$@"

$(BUILD_THEME_DIR)/fonts: clearsans-1.00.zip
	mkdir -p $@
	unzip -o -j $< "*.woff" -d $@

%/bootstrap.css: bootstrap.zip
	unzip -o -j $< "*bootstrap.css" -d $(TMP_THEME_DIR)
	sed -i '/font-size: 10px/d' $@;

$(BUILD_IMAGE_DIRS)::
	mkdir -p $(@D)
	src=$@; \
	src=$(TMP_THEME_DIR)$${src#$(BUILD_THEME_DIR)}; \
	cp -r $$src $@

$(BUILD_THEME_DIR)/umc.css: tmp-css
	# compile all stylus files
	stylus $(TMP_THEME_DIR) $(TMP_THEME_DIR)/form $(TMP_THEME_DIR)/layout $(TMP_THEME_DIR)/site
	# generate source maps
	for idir in . form layout site; do \
		cd $(TMP_THEME_DIR)/$$idir; \
		stylus -m . ; \
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
	deps=$$(find umc/ -name "*.js" -a -not -name "*.*.js" | sort | sed 's/\.js//; s/i18n$$/i18n!/; s/.*/"\0",/; $$ s/,$$//'); \
	echo "define([$$deps], function() { })" > $@

$(BUILD_DIR)/umc/package.json: debian/changelog
	mkdir -p $(@D)
	sed 's/%VERSION%/$(VERSION)/' package.json > $@

# manually define dependencies between JSON translation files
# and add a more generic rule for copying JSON translation file
$(TMP_DIR)/umc/i18n/de/app.json: umc/de.json
$(TMP_DIR)/umc/i18n/en/app.json: umc/en.json
$(TMP_DIR)/umc/i18n/%/app.json:
	# install JSON translation at correct position
	mkdir -p $(@D)
	cp $< $@

$(I18N_FILES):: $(JS_FILES)
	# update .po files and convert .po to .json files (in one go)
	lang=$(@F); \
	lang=$${lang%.*}; \
	/usr/bin/dh-umc-translate -p univention-web-js -l $$lang -o $(@D) $^

$(BUILD_DIR)/dojo/dojo.js: $(TMP_DIR) $(TMP_JS_FILES) $(BUILD_DIR) build_profile.js build-common-js
	# main dojo build process
	/usr/share/univention-dojo/util/buildscripts/build.sh profile=build_profile.js version="$(VERSION)"

build-dev: build-common-js build-css
	# symlinks for installed modules
	mkdir -p $(TMP_DIR)/umc/modules
	cp -frsn /usr/share/univention-management-console-frontend/js/umc/modules/* $(TMP_DIR)/umc/modules
	#cp -frsn /usr/share/univention-management-console-frontend/js/dijit/themes/umc/icons css

$(TMP_DIR)/umc/i18n/en/branding.json:
	# create empty branding localisation files to not cause 404 errors
	mkdir -p $(@D)
	touch "$@"

install: build
	# copy all files from the build directory .. exclude file of the tmp directory
	mkdir -p "$(DESTDIR)$(PKG_DIR)"
	rsync -rpl --exclude ".svn" "$(BUILD_DIR)/" "$(DESTDIR)$(PKG_DIR)"
	
	cd $(BUILD_THEME_DIR); find ./ -type d -exec install -m0755 -d $(DESTDIR)$(THEME_INSTALL_DIR)/{} \;
	cd $(BUILD_THEME_DIR); find ./ -type f -exec install -m0644 {} $(DESTDIR)$(THEME_INSTALL_DIR)/{} \;
	install -m0755 -d $(DESTDIR)$(THEME_INSTALL_DIR)/icons/scalable
	install -m0755 -d $(DESTDIR)$(THEME_INSTALL_DIR)/icons/50x50
	install -m0755 -d $(DESTDIR)$(THEME_INSTALL_DIR)/icons/16x16

clean:
	rm -rf $(TMP_DIR) $(BUILD_DIR) umc/de.json um/en.json
