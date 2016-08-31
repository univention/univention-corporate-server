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

pkgDir:=/usr/share/univention-web/js/
timestamp:=$$$(shell date +'%Y%d%m%H%M%S')$$
dojoDir:=/usr/share/univention-dojo
version:=$(shell dpkg-parsechangelog | sed -ne 's/^Version: //p')
buildDir:=$(CURDIR)/build
tmpDir:=$(CURDIR)/tmp
testsDir:=$(CURDIR)/tests
jsFiles:=$(shell find umc -name "*.js")

THEME_TMP:=$(CURDIR)/tmp2
THEME_REPO=dijit-claro-stylus
THEME_GIT_PARAMS=--git-dir $(THEME_REPO)/.git
TMP_THEME_DIR=$(THEME_TMP)/dijit/themes/$(THEME_REPO)
TMP_THEME_CSS=$(TMP_THEME_DIR)/umc.css
BOOSTRAP_FILE=$(TMP_THEME_DIR)/bootstrap.css
THEME_INSTALL_DIR=/usr/share/univention-web/js/dijit/themes/umc
ICON_FILES=icons.svg icons-small.svg icons-white.svg icons-small-white.svg
ICON_FILES_PNG=$(addprefix $(TMP_THEME_DIR)/images/,$(ICON_FILES:.svg=.png))

.PHONY: build build-dev build-common install repack clean jslint i18n umc/package.json

build: build-common $(buildDir)/js/dojo/dojo.js.uncompressed.js css/umc.css css/fonts

$(THEME_REPO):
	git clone https://github.com/kfranqueiro/$(THEME_REPO)
	git $(GIT_PARAMS) gc

$(THEME_TMP): $(THEME_REPO)
	# copy dijit-claro-stylus, dojo, and dijit files into tmp dir
	mkdir -p $@
	cp -r /usr/share/univention-dojo/dojo /usr/share/univention-dojo/dijit /usr/share/univention-dojo/dojox $@
	cp -r $(PWD)/$(THEME_REPO) $@/dijit/themes
	# remove .git dir
	rm -rf $(TMP_THEME_DIR)/.git
	# mv claro.css to umc.css
	mv $(TMP_THEME_DIR)/claro.css $(TMP_THEME_CSS)
	# replace '.claro' selector with '.umc'
	sed -i 's/\.claro\>/.umc/g;' $$(find $(TMP_THEME_DIR) -name '*.styl' -o -name '*.css')
	for isvg in icons icons-small; do \
		sed 's/\#282828/\#ffffff/g' $(TMP_THEME_DIR)/images/$$isvg.svg > $(TMP_THEME_DIR)/images/$$isvg-white.svg; \
	done

%.png: %.svg
	convert -background transparent "$<" "$@"

css:
	mkdir css

css/fonts:
	mkdir -p $@
	unzip -o -j clearsans-1.00.zip "*.woff" -d $@

css/umc.css: $(THEME_TMP) css $(BOOSTRAP_FILE) $(ICON_FILES_PNG)
	# compile all stylus files
	stylus $(TMP_THEME_DIR) $(TMP_THEME_DIR)/form $(TMP_THEME_DIR)/layout $(TMP_THEME_DIR)/site
	# Workaround: mark several commands as comments (/*TMP ... */)
	# to avoid parse errors with stylus
	sed -i 's/.*\(^\s\+#\|filter: alpha\|filter:\|top: expression\).*/\/\*TMP\0\*\//; /\/\*TMP/ { s|/\*[^*]*\*/\*/|*/| }' $$(find $(THEME_TMP)/dojo $(THEME_TMP)/dijit -name "*.css")
	# compile all .css files into one big file
	stylus --resolve-url --include-css $(TMP_THEME_CSS)
	# Workaround: remove the temporarily commented lines
	sed -i 's|/\*TMP\(.*\)\*/|\1|' $(TMP_THEME_CSS)
	# copy the main CSS file and images
	cp $(TMP_THEME_CSS) $@
	for idir in ./images ./form/images ./layout/images; do \
		mkdir -p css/$${idir%/*}; \
		[ -e css/$$idir ] || cp -r $(TMP_THEME_DIR)/$$idir css/$$idir; \
	done
	touch $@

$(BOOSTRAP_FILE): bootstrap.zip
	unzip -o -j $< "*bootstrap.css" -d $(TMP_THEME_DIR)
	sed -i '/font-size: 10px/d' $@;

repack:
	git $(GIT_PARAMS) repack -d

update:
	git $(GIT_PARAMS) fetch
	# make sure that all new object files are packed into one package
	# this should make the SVN commit easier
	git $(GIT_PARAMS) repack -d

# the automatically generated module umc/widgets contains a require to all umc widgets
umc/widgets.js:
	deplist=""; \
	for imod in umc/widgets/*.js; do \
		deplist="$${deplist}\"$${imod%.js}\", "; \
	done; \
	echo "define([$${deplist%, }], function() { })" > $@

umc/package.json:
	sed 's/%VERSION%/$(version)/' package.json > $@

$(tmpDir):
	mkdir -p $@
	cp -rfs $(dojoDir)/* $@
	# remove dojo util directory
	rm -rf $@/util
	cp -rfs "$(CURDIR)/umc" $@

# convert .po to .json files
i18n:
	/usr/bin/dh-umc-translate -p univention-web-js -l en -l de -o umc $(jsFiles)

$(buildDir):
	mkdir -p $@

# rule for the main dojo build process
$(buildDir)/js/dojo/dojo.js.uncompressed.js: $(jsFiles) $(buildDir)
	/usr/share/univention-dojo/util/buildscripts/build.sh profile=build_profile.js version="$(version)"

build-dev: build-common
	# symlink javascript code
	[ -e $(buildDir)/js ] || ln -s $(tmpDir) $(buildDir)/js
	# symlink test directory
	[ -e $(buildDir)/tests ] || ln -s $(testsDir) $(buildDir)/tests
	# symlinks for installed modules
	mkdir -p $(tmpDir)/umc/modules
	cp -frsn /usr/share/univention-web/js/umc/modules/* $(tmpDir)/umc/modules
	
	cp -r $(TMP_THEME_DIR)/* css
	cd css; stylus -m .
	cd css/form; stylus -m .
	cd css/layout; stylus -m .
	cd css/site; stylus -m .
	cp -frsn /usr/share/univention-web/js/dijit/themes/umc/icons css
	rm -rf $(tmpDir)/dijit/themes/umc; \
	ln -s css $(tmpDir)/dijit/themes/umc; \

build-common: i18n umc/widgets.js umc/package.json $(tmpDir) $(buildDir)
	# symlink to javascript dir with timestamp
	rm -f "$(buildDir)/js_"*
	ln -s "js" "$(buildDir)/js_"'$(timestamp)'
	# install JSON translation file for framework
	for i in "$(CURDIR)/umc/"*.json; do \
		lang=$${i##*/}; \
		lang=$${lang%.*}; \
		mkdir -p "$(tmpDir)/umc/i18n/$$lang"; \
		cp $$i "$(tmpDir)/umc/i18n/$$lang/app.json"; \
	done
	# create empty branding localisation files to not cause 404 errors
	touch "$(tmpDir)/umc/i18n/en/branding.json" "$(tmpDir)/umc/i18n/de/branding.json"

install: build
	# copy all files from the build directory .. exclude file of the tmp directory
	mkdir -p "$(DESTDIR)$(pkgDir)"
	rsync -rpl --exclude ".svn" "$(buildDir)/" "$(DESTDIR)$(pkgDir)"
	
	cd css; find ./ -type d -exec install -m0755 -d $(DESTDIR)$(THEME_INSTALL_DIR)/{} \;
	cd css; find ./ -type f -exec install -m0644 {} $(DESTDIR)$(THEME_INSTALL_DIR)/{} \;
	install -m0755 -d $(DESTDIR)$(THEME_INSTALL_DIR)/icons/scalable
	install -m0755 -d $(DESTDIR)$(THEME_INSTALL_DIR)/icons/50x50
	install -m0755 -d $(DESTDIR)$(THEME_INSTALL_DIR)/icons/16x16

clean:
	rm -rf css $(THEME_TMP) $(tmpDir) $(buildDir) umc.xml umc/widgets.js umc/{en,de}.json umc/package.json
