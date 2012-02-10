#!/usr/bin/make -f
#
# Univention Management Console Frontend Package
#  Makefile for building/installing the package
#
# Copyright 2011 Univention GmbH
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

jsFiles:=$(shell find umc -name "*.js")
pkgDir:=/usr/share/univention-management-console-frontend/
timestamp:=$$$(shell date +'%Y%d%m%H%M%S')$$
version:=$(shell dpkg-parsechangelog | sed -ne 's/^Version: //p')
buildDir:=$(CURDIR)/build
tmpDir:=$(buildDir)/_tmp$(timestamp)

.PHONY: build build-dev build-common install clean jslint

build: build-common
	@# create a temp directory
	mkdir -p '$(tmpDir)'
	@# create the module umc.widgets containing a require for all umc widgets
	@# include all translation files
	( \
		echo '/*global dojo */'; \
		echo 'dojo.provide("_tmp$(timestamp).widgets");'; \
		find umc/widgets/ -name "*.js" | sed 's|/|.|g; s|^\(.*\).js$$|dojo.require("\1");|'; \
		for i in "$(CURDIR)/umc/"*.json; do \
			lang=$${i##*/}; \
			lang=$${lang%.*}; \
			echo 'dojo.cache("umc", "i18n/'$$lang'/app.json")'; \
		done; \
	) > '$(tmpDir)/include.js'
	@# dojo build
	sed 's|%CURDIR%|$(CURDIR)|g; s|%TIMESTAMP%|$(timestamp)|g' "$(CURDIR)/build_profile.js" > '$(tmpDir)/build_profile.js'
	cd /usr/share/univention-dojo/util/buildscripts; \
	./build.sh profileFile='$(tmpDir)/build_profile.js' releaseDir="$(CURDIR)/build/js" version="$(version)"
	@# index page .. replace the HASH with a timestamp
	sed 's/%HASH%/_$(timestamp)/; s/%JSSUFFIX%//;' index.html > "$(buildDir)/index.html"
	sed 's/%HASH%/_$(timestamp)/; s/%JSSUFFIX%/.uncompressed.js/;' index.html > "$(buildDir)/debug.html"
	@# copy css style sheets and images
	rsync -rp --exclude ".svn" --exclude "*.xcf" --exclude "*.sh" css images $(buildDir) 
	@# static login pages
	for i in login blank; do \
		sed 's/%HASH%/_$(timestamp)/; s/%JSSUFFIX%//;' umc/$$i.html > "$(buildDir)/js/umc/$$i.html"; \
	done;

build-dev: build-common
	mkdir -p "$(buildDir)/js"
	@# create the module umc.widgets containing a require for all umc widgets
	@# symlinks to dojo source code
	for i in dojo dijit dojox; do \
		ln -fs /usr/share/univention-dojo/$$i "$(buildDir)/js"; \
	done
	@# index page .. replace the HASH with a timestamp
	sed 's/%HASH%/_$(timestamp)/; s/%JSSUFFIX%//; /<script.*umc\/build.js.*<\/script>/d;' index.html > "$(buildDir)/index.html"
	@# symlinks for css style sheets and images
	cp -rfs "$(CURDIR)/css" "$(CURDIR)/images" "$(buildDir)"
	@# symlinks for UMC code
	cp -rfs "$(CURDIR)/umc" "$(buildDir)/js"
	@# symlinks for installed modules/icons
	cp -frs /usr/share/univention-management-console-frontend/js/umc/modules/* $(buildDir)/js/umc/modules
	cp -frs /usr/share/univention-management-console-frontend/images/icons/* $(buildDir)/images/icons/
	@# static login pages
	for i in login blank; do \
		rm "$(buildDir)/js/umc/$$i.html"; \
		sed 's/%HASH%/_$(timestamp)/; s/%JSSUFFIX%//;' umc/$$i.html > "$(buildDir)/js/umc/$$i.html"; \
	done;

build-common: i18n
	@# scale all icons
	for s in 16x16 50x50; do \
		mkdir -p "$(buildDir)/images/icons/$$s"; \
		for i in icons/*.png; do \
			dest="$(buildDir)/images/icons/$$s/$${i##*/}"; \
			if [ ! -e "$$dest" ]; then \
				convert "$$i" -resize $$s "$$dest"; \
			fi; \
		done; \
	done
	@# symlinks as temporary directories with timestamp
	for i in js css; do \
		rm -f "$(buildDir)/$${i}_"*; \
		ln -s "$$i" "$(buildDir)/$${i}_"'$(timestamp)'; \
	done;
	@# install JSON translation file for framework
	for i in "$(CURDIR)/umc/"*.json; do \
		lang=$${i##*/}; \
		lang=$${lang%.*}; \
		mkdir -p "$(CURDIR)/umc/i18n/$$lang"; \
		cp $$i "$(CURDIR)/umc/i18n/$$lang/app.json"; \
	done

i18n:
	/usr/bin/dh-umc-translate -p univention-management-console-frontend -o umc $(jsFiles)

install: build
	@# copy all files from the build directory .. exclude file of the tmp directory
	mkdir -p "$(DESTDIR)$(pkgDir)"
	rsync -rpl --exclude ".svn" --exclude "_tmp"'$(timestamp)' "$(buildDir)/" "$(DESTDIR)$(pkgDir)"

clean:
	rm -rf build

jslint:
	jslint $(jsFiles) | grep -v "\['require'\] is better written in dot notation" || true

