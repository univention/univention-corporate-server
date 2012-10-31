#!/usr/bin/make -f
#
# Univention Management Console Frontend Package
#  Makefile for building/installing the package
#
# Copyright 2011-2012 Univention GmbH
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

.PHONY: build build-dev build-common install clean jslint i18n umc/package.json $(tmpDir)/umc/login.html $(buildDir)/index.html $(buildDir)/debug.html

build: build-common $(tmpDir) $(buildDir)/js/dojo/dojo.js.uncompressed.js $(themesDir)/umc

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
$(tmpDir)/umc/login.html: login.html
	mkdir -p $(dir $@)
	sed 's/%HASH%/_$(timestamp)/;' login.html > $@
	cp $@ $(dir $@)/blank.html

# copy css and image data into umc themes directory
$(themesDir)/umc: $(tmpDir)
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
	@# compile all less files and replace ".claro" with ".umc"
	for i in $$(find $@ -name "*.less"); do \
		echo ./lessc $$i $${i%.*}.css; \
		./lessc $$i $${i%.*}.css; \
		sed -i 's/\.claro\>/.umc/g; s/"""/"/g;' $${i%.*}.css; \
	done

$(themesDir)/umc/icons: $(themesDir)/umc
	@# scale all icons
	for s in 16x16 24x24 50x50; do \
		mkdir -p "$@/$$s"; \
		for i in icons/*.png; do \
			dest="$@/$$s/$${i##*/}"; \
			if [ ! -e "$$dest" ]; then \
				convert "$$i" -resize $$s "$$dest"; \
			fi; \
		done; \
	done

build-dev: build-common
	@# symlink javascript code
	[ -e $(buildDir)/js ] || ln -s $(tmpDir) $(buildDir)/js
	@# symlinks for installed modules/icons
	mkdir -p $(tmpDir)/umc/modules
	cp -frs /usr/share/univention-management-console-frontend/js/umc/modules/* $(tmpDir)/umc/modules
	cp -frs /usr/share/univention-management-console-frontend/js/dijit/themes/umc/icons/* $(themesDir)/umc/icons/

build-common: i18n umc/widgets.js umc/package.json $(themesDir)/umc $(themesDir)/umc/icons $(tmpDir)/umc/login.html $(buildDir) $(buildDir)/index.html $(buildDir)/debug.html
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

