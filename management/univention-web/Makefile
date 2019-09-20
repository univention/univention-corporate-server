#!/usr/bin/make -f
#
# Univention Management Console Frontend Package
#  Makefile for building/installing the package
#
# Copyright 2011-2019 Univention GmbH
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


### META FILES AND DIRECTORIES ###

DOJO_DIR := /usr/share/univention-dojo
VERSION := $(shell dpkg-parsechangelog | sed -ne 's/^Version: //p')
WWW_JS_DIR := /var/www/univention/js

TMP_DIR := $(CURDIR)/tmp
TMP_THEME_DIR := $(TMP_DIR)/dijit/themes/umc
TMP_I18N_DIR := $(TMP_DIR)/umc/i18n

BUILD_DIR := $(CURDIR)/build
BUILD_THEME_DIR=$(BUILD_DIR)/dijit/themes/umc


### MAIN RULES ###

.PHONY: build install clean tmp-build tmp-umc-icons build-dev build-live i18n

build: $(BUILD_DIR)/dojo/dojo.js $(BUILD_THEME_DIR)/umc.css $(BUILD_DIR)/config.js

$(BUILD_DIR)/dojo/dojo.js $(BUILD_THEME_DIR)/umc.css: build_profile.js tmp-build
	# main dojo build process
	mkdir -p $(BUILD_DIR)
	/usr/share/univention-dojo/util/buildscripts/build.sh profile=build_profile.js version="$(VERSION)"

JS_INSTALL_DIR := usr/share/univention-web/js
THEME_INSTALL_DIR=$(JS_INSTALL_DIR)/dijit/themes/umc

install:
	# copy all files for univention-web-js
	cd $(BUILD_DIR); find . -type d -exec install -m0755 -d $(CURDIR)/debian/univention-web-js/$(JS_INSTALL_DIR)/{} \;
	cd $(BUILD_DIR); find . -type f -exec install -m0644 {} $(CURDIR)/debian/univention-web-js/$(JS_INSTALL_DIR)/{} \;
	rm -rf $(CURDIR)/debian/univention-web-js/$(JS_INSTALL_DIR)/dijit/themes/umc
	rm -f $(CURDIR)/debian/univention-web-js/$(JS_INSTALL_DIR)/build-report.txt
	# copy all files for univention-web-style
	cd $(BUILD_DIR); find dijit/themes/umc -type d -exec install -m0755 -d $(CURDIR)/debian/univention-web-style/$(JS_INSTALL_DIR)/{} \;
	cd $(BUILD_DIR); find dijit/themes/umc -type f -exec install -m0644 {} $(CURDIR)/debian/univention-web-style/$(JS_INSTALL_DIR)/{} \;


### DEVELOPMENT RULES ###

UMC_ICONS_DIR := /usr/share/univention-management-console-frontend/js/dijit/themes/umc/icons
UMC_ICON_FILES := $(shell find $(UMC_ICONS_DIR) -type f)
TMP_UMC_ICON_FILES := $(UMC_ICON_FILES:$(UMC_ICONS_DIR)/%=$(TMP_THEME_DIR)/icons/%)
I18N_FILES := js/de.po js/en.po

i18n: $(I18N_FILES)

build-dev: tmp-build $(TMP_UMC_ICON_FILES)
	# divert original js symlink and create symlink to temporary build dir "tmp"
	if [ -L $(WWW_JS_DIR) -a "$$(readlink -f $(WWW_JS_DIR))" = "/usr/share/univention-web/js" ]; then \
		dpkg-divert --package univention-web-make-build-dev --add --rename --divert $(WWW_JS_DIR).real $(WWW_JS_DIR) ;\
		ln -s $(TMP_DIR) $(WWW_JS_DIR) ;\
		ln -s /usr/share/univention-web/js/umc/hooks.json $(TMP_DIR)/umc ;\
		ln -s /usr/share/univention-web/js/umc/hooks/*.js $(TMP_DIR)/umc/hooks ;\
		ucr set umc/web/hooks/univention-web-js?default_menu_entries ;\
	fi

$(TMP_UMC_ICON_FILES): $(TMP_THEME_DIR)/icons/%: $(UMC_ICONS_DIR)/%
	mkdir -p $(@D)
	ln -fs $< $@


### INTERMEDIATE LEVEL BUILD RULES ###

# javascript files
JS_FILES := $(shell find js -name "*.js")
TMP_JS_FILES := $(JS_FILES:js/%=$(TMP_DIR)/umc/%)
DOJO_PACKAGES := $(filter-out $(DOJO_DIR)/util, $(wildcard $(DOJO_DIR)/*))
TMP_DOJO_PACKAGES := $(DOJO_PACKAGES:$(DOJO_DIR)/%=$(TMP_DIR)/%)
TMP_I18N_FILES := $(addprefix $(TMP_I18N_DIR)/, en/app.json de/app.json en/branding.json de/branding.json)

# font files
FONT_FILES := $(shell unzip -l roboto.zip | sed -n 's/^.*\s*\(Roboto.*\.woff\).*$$/\1/p')
TMP_FONT_FILES := $(addprefix $(TMP_THEME_DIR)/fonts/, $(FONT_FILES))

# image files
IMG_FILES := $(shell find css -name "*.svg" -o -name "*.png" -o -name "*.gif")
WHITE_IMG_FILES := $(addprefix css/images/,icons-white.svg icons-small-white.svg univention-white.svg univention_u-white.svg home-white.svg)
SVG_IMG_FILES := $(shell find css -name "*.svg")
PNG_IMG_FILES := $(filter-out css/images/login_logo.png,$(SVG_IMG_FILES:.svg=.png))
ALL_IMG_FILES := $(IMG_FILES) $(WHITE_IMG_FILES) $(PNG_IMG_FILES)
TMP_IMG_FILES := $(patsubst css/%,$(TMP_THEME_DIR)/%,$(ALL_IMG_FILES))

tmp-build: $(TMP_JS_FILES) $(TMP_DOJO_PACKAGES) $(TMP_I18N_FILES) $(TMP_DIR)/umc/package.json $(TMP_DIR)/umc/_all.js $(TMP_DIR)/login/main.js $(TMP_DIR)/config.js $(TMP_THEME_DIR)/umc.css $(TMP_THEME_DIR)/bootstrap.css $(TMP_FONT_FILES) $(TMP_IMG_FILES)

$(TMP_JS_FILES):
	@# create symlinks for all JavaScript files
	mkdir -p $(@D)
	ln -fs $(patsubst $(TMP_DIR)/umc/%,$(CURDIR)/js/%,$@) $@

$(TMP_DOJO_PACKAGES): $(TMP_DIR)/%: $(DOJO_DIR)/%
	@# copy dojo and dijit files into tmp dir; remove util dir
	mkdir -p $(TMP_DIR)
	cp -rfs $< $@

$(TMP_I18N_DIR)/%/branding.json:
	@# create empty branding localisation files to not cause 404 errors
	mkdir -p $(@D)
	echo '{}' > "$@"

$(TMP_I18N_DIR)/%/app.json: js/%.po
	@# create empty branding localisation files to not cause 404 errors
	mkdir -p $(@D)
	dh-umc-po2json $<
	mv $(<D)/$*.json $@

js/%.po: $(JS_FILES)
	xgettext --force-po --add-comments=i18n --from-code=UTF-8 --sort-output --language JavaScript -o $@.temp $^
	msgmerge $@ $@.temp > $@.new
	mv $@.new $@
	rm -f $@.temp

$(TMP_DIR)/umc/package.json: debian/changelog
	mkdir -p $(@D)
	sed 's/%VERSION%/$(VERSION)/' package.json > $@

$(TMP_DIR)/umc/_all.js:
	# generate a pseudo module which contains references to all other JS modules
	deps=$$(find js/ -name "*.js" -a -not -name "*.*.js" -a -not -wholename 'js/hooks/*' | sort | sed 's/\.js//; s/^js/umc/; s/i18n$$/i18n!/; s/.*/"\0",/; $$ s/,$$//'); \
	echo "define([$$deps], function() { })" > $@

$(TMP_DIR)/login/main.js:
	# generate empty pseudo modules
	mkdir -p $(@D)
	echo "define([], function() { })" > $@

%/config.js: config.js
	# copy the config.js to its appropriate directory
	mkdir -p $(@D)
	sed 's/%VERSION%/$(VERSION)/' $< > $@

$(TMP_THEME_DIR)/umc.css: css/umc.css
	mkdir -p $(@D)
	ln -fs $(CURDIR)/css/umc.css* $(@D)

STYL_FILES := $(shell find css -name "*.styl")

css/umc.css: css/umc.styl $(STYL_FILES) $(ALL_IMG_FILES)
	cd $(@D); stylus --sourcemap --resolve-url --hoist-atrules $(<F)

$(TMP_THEME_DIR): $(TMP_DIR)
	# link theme files into the tmp dir
	cp -fsr $(CURDIR)/css $@

$(TMP_IMG_FILES): $(TMP_THEME_DIR)/%: css/%
	@# create symlinks for all image files
	mkdir -p $(@D)
	cp $< $@

%/bootstrap.css: bootstrap.zip
	unzip -o -j $< "*bootstrap.css" -d $(TMP_THEME_DIR)
	sed -i '/font-size: 10px/d' $@

$(TMP_FONT_FILES): roboto.zip
	mkdir -p $(@D)
	unzip -o $< $(@F) -d $(@D)
	touch $@

# automatically create SVG files with white icons
%-white.svg: %.svg
	sed 's/\#282828/\#ffffff/g' $< > $@

%.png: %.svg
	convert -background transparent "$<" "$@"


### CLEAN RULE ###

CREATED_IMG_FILES := $(WHITE_IMG_FILES) $(PNG_IMG_FILES)

.INTERMEDIATE: $(CREATED_IMG_FILES)

clean:
	rm -rf $(TMP_DIR) $(BUILD_DIR) css/umc.css{,.map} $(CREATED_IMG_FILES)
	# remove link to temporary build dir "tmp" and undivert original js directory
	if [ -L $(WWW_JS_DIR) -a "$$(readlink -f $(WWW_JS_DIR))" = "$(TMP_DIR)" ]; then \
		rm $(WWW_JS_DIR) ;\
		dpkg-divert --package univention-web-make-build-dev --remove --rename "$(WWW_JS_DIR)" ;\
	fi

