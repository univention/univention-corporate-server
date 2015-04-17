#!/usr/bin/make -f
#
# Univention Management Console Frontend Package
#  Makefile for building/installing the package
#
# Copyright 2011-2015 Univention GmbH
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
testsDir:=$(CURDIR)/tests
jsFiles:=$(shell find umc -name "*.js")

.PHONY: build build-dev build-common install clean jslint i18n umc/package.json $(buildDir)/login.html $(buildDir)/index.html $(buildDir)/debug.html

build: build-common $(buildDir)/js/dojo/dojo.js.uncompressed.js

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
	# remove dojo util directory
	rm -rf $@/util
	cp -rfs "$(CURDIR)/umc" $@

# convert .po to .json files
i18n:
	/usr/bin/dh-umc-translate -p univention-management-console-frontend -l en -l de -o umc $(jsFiles) index.html

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
$(buildDir)/login.html: login.html
	mkdir -p $(dir $@)
	cp $< $(buildDir)
	cp blank.html $(dir $@)/blank.html

build-dev: build-common
	# symlink javascript code
	[ -e $(buildDir)/js ] || ln -s $(tmpDir) $(buildDir)/js
	# symlink test directory
	[ -e $(buildDir)/tests ] || ln -s $(testsDir) $(buildDir)/tests
	# symlinks for installed modules
	mkdir -p $(tmpDir)/umc/modules
	cp -frsn /usr/share/univention-management-console-frontend/js/umc/modules/* $(tmpDir)/umc/modules
	# if the umc theme package exists, as well, call "make build-dev"
	# there, as well, and link its sources in
	if [ -d ../univention-management-console-frontend-theme ]; then \
		oldPath=$$PWD; \
		cd ../univention-management-console-frontend-theme; \
		make build-dev; \
		cd $$oldPath; \
		rm -rf $(tmpDir)/dijit/themes/umc; \
		ln -s $$oldPath/../univention-management-console-frontend-theme/css $(tmpDir)/dijit/themes/umc; \
	fi


build-common: i18n umc/widgets.js umc/package.json $(tmpDir) $(cssFiles) $(buildDir)/login.html $(buildDir) $(buildDir)/index.html $(buildDir)/debug.html
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

clean:
	rm -rf $(tmpDir) $(buildDir) umc.xml umc/widgets.js umc/{en,de}.json umc/package.json
	# if the umc theme package exists, as well, call "make clean" there, as well
	if [ -d ../univention-management-console-frontend-theme ]; then \
		cd ../univention-management-console-frontend-theme; \
		make clean; \
	fi

