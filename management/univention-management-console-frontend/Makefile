#!/usr/bin/make -f
#
# Univention Management Console Frontend Package
#  Makefile for building/installing the package
#
# Copyright 2011-2014 Univention GmbH
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

pkgDir:=/usr/share/univention-management-console-frontend/
timestamp:=$$$(shell date +'%Y%d%m%H%M%S')$$
dojoDir:=/usr/share/univention-dojo
version:=$(shell dpkg-parsechangelog | sed -ne 's/^Version: //p')
buildDir:=$(CURDIR)/build
tmpDir:=$(CURDIR)/tmp
themesDir:=$(tmpDir)/dijit/themes
jsFiles:=$(shell find umc -name "*.js")

# collect all less files...
# the UMC theme is based on claro with some additional .less files
claroLessFiles:=$(shell find $(dojoDir)/dijit/themes/claro -name "*.less" | sed 's|^.*themes/claro/|$(themesDir)/umc/|')
umcLessFiles:=$(shell find css -name "*.less" | sed 's|^css/|$(themesDir)/umc/|')
lessFiles:=$(claroLessFiles) $(umcLessFiles)
cssFiles:=$(lessFiles:%.less=%.css)

.PHONY: build build-dev build-common install clean jslint i18n umc/package.json $(tmpDir)/umc/app/login.html $(buildDir)/index.html $(buildDir)/debug.html

build: build-common $(buildDir)/js/dojo/dojo.js.uncompressed.js $(themesDir)/umc

# the automatically generated module umc/widgets contains a require to all umc widgets
umc/widgets.js:
	deplist=""; \
	for imod in umc/widgets/*.js; do \
		deplist="$${deplist}\"$${imod%.js}\", "; \
	done; \
	echo "define([$${deplist%, }], function() { })" > $@

umc/package.json:
	sed 's/%VERSION%/$(version)/' package.json > $@

# temp directory
$(tmpDir):
	mkdir -p $@
	cp -rfs $(dojoDir)/* $@
	@# remove dojo util directory
	rm -rf $@/util
	cp -rfs "$(CURDIR)/umc" $@

# convert .po to .json files
i18n:
	/usr/bin/dh-umc-translate -p univention-management-console-frontend -l en -l de -o umc $(jsFiles)

$(buildDir):
	mkdir -p $@

# rule for the main dojo build process
$(buildDir)/js/dojo/dojo.js.uncompressed.js: $(jsFiles) $(buildDir)
	/usr/share/univention-dojo/util/buildscripts/build.sh profile=build_profile.js version="$(version)"

# index page
$(buildDir)/index.html: $(buildDir) index.html
	sed 's/%HASH%/_$(timestamp)/; s/%JSSUFFIX%//; s/%VERSION%/$(version)/;' index.html > $@

# index page for debug mode
$(buildDir)/debug.html: $(buildDir) index.html
	sed 's/%HASH%/_$(timestamp)/; s/%JSSUFFIX%/.uncompressed.js/; s/%VERSION%/$(version)/;' index.html > $@

# login page
$(tmpDir)/umc/app/login.html: login.html
	mkdir -p $(dir $@)
	sed 's/%HASH%/_$(timestamp)/;' login.html > $@
	cp $@ $(dir $@)/blank.html

%.css: %.less
	@# compile less file
	./lessc $< $@
	@# replace .claro rules with .umc rule
	sed -i 's/\.claro\>/.umc/g; s/"""/"/g;' $@

# copy css and image data into umc themes directory
$(themesDir)/umc:
	@#rsync -rp --exclude ".svn" --exclude "*.xcf" --exclude "*.sh" css $@
	@# symlinks for css style sheets and images
	cp -rf $(dojoDir)/dijit/themes/claro $@
	@# remove claro.css and all .css files that have a .less source
	rm $@/claro.css
	for i in $$(find $@ -name "*.less"); do rm -f $${i%.less}.css; done
	cp -rsf $(CURDIR)/css/* $@
	@# merge claro variables and our variables (recursive include not possible with less)
	mv $@/variables.less $@/variables.orig.less
	cat $(themesDir)/claro/variables.less $@/variables.orig.less > $@/variables.less
	@# remove claro compile.js file
	rm $@/compile.js

$(themesDir)/umc/icons: $(themesDir)/umc
	@# scale all icons
	@# treat umc-menu* icons differently and create a version with different
	@# background for the hover effect
	for s in 16 24 50; do \
		path="$@/$${s}x$${s}"; \
		mkdir -p "$$path"; \
		for isrc in icons/*.svg*; do \
			name="$${isrc##*/}"; \
			name="$${name%.*}"; \
			dest="$$path/$${name}.png"; \
			echo "creating $$dest"; \
			convert -background none "$$isrc" -resize x$$s "$$dest"; \
		done; \
	done

build-dev: build-common
	@# symlink javascript code
	[ -e $(buildDir)/js ] || ln -s $(tmpDir) $(buildDir)/js
	@# symlinks for installed modules
	mkdir -p $(tmpDir)/umc/modules
	cp -frsn /usr/share/univention-management-console-frontend/js/umc/modules/* $(tmpDir)/umc/modules
	@# symlinks for installed icons
	mkdir -p $(themesDir)/umc/icons/
	cp -frsn /usr/share/univention-management-console-frontend/js/dijit/themes/umc/icons/* $(themesDir)/umc/icons/

build-common: i18n umc/widgets.js umc/package.json $(tmpDir) $(themesDir)/umc $(themesDir)/umc/icons $(cssFiles) $(tmpDir)/umc/app/login.html $(buildDir) $(buildDir)/index.html $(buildDir)/debug.html
	@# symlink to javascript dir with timestamp
	rm -f "$(buildDir)/js_"*
	ln -s "js" "$(buildDir)/js_"'$(timestamp)'
	@# install JSON translation file for framework
	for i in "$(CURDIR)/umc/"*.json; do \
		lang=$${i##*/}; \
		lang=$${lang%.*}; \
		mkdir -p "$(tmpDir)/umc/i18n/$$lang"; \
		cp $$i "$(tmpDir)/umc/i18n/$$lang/app.json"; \
	done
	@# create empty branding localisation files to not cause 404 errors
	touch "$(tmpDir)/umc/i18n/en/branding.json" "$(tmpDir)/umc/i18n/de/branding.json"

install: build
	@# copy all files from the build directory .. exclude file of the tmp directory
	mkdir -p "$(DESTDIR)$(pkgDir)"
	rsync -rpl --exclude ".svn" "$(buildDir)/" "$(DESTDIR)$(pkgDir)"

clean:
	rm -rf $(tmpDir) $(buildDir) umc.xml umc/widgets.js umc/{en,de}.json umc/package.json

