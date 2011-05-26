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

jsFiles=$(shell find umc -name "*.js")
pkgDir=/usr/share/univention-management-console-frontend/
timestamp=$(shell date +'%Y%d%m%H%M%S')
version=$(shell dpkg-parsechangelog | sed -ne 's/^Version: //p')
buildDir=$(CURDIR)/build

.PHONY: all install build clean jslint

all: install

jslint: 
	jslint $(jsFiles)

clean:
	rm -rf build

build:
	mkdir -p "$(buildDir)/js/umc"
	@# create the module umc.widgets containing a require for all umc widgets
	( \
		echo '/*global dojo */'; \
		echo 'dojo.provide("umc.widgets");'; \
		find umc/widgets/ -name "*.js" | sed 's|/|.|g; s|^\(.*\).js$$|dojo.require("\1");|'; \
	) > $(buildDir)/js/umc/widgets.js
	@# dojo build
	sed 's|%CURDIR%|$(CURDIR)|' "$(CURDIR)/build_profile.js" > "$(buildDir)/.build_profile.js"
	cd /usr/share/univention-dojo/util/buildscripts; \
	./build.sh profileFile="$(buildDir)/.build_profile.js" releaseDir="$(CURDIR)/build/js" version="$(version)"
	@# index page .. replace the HASH with a timestamp
	sed 's/%HASH%/_$(timestamp)/' index.html > "$(CURDIR)/build/index.html"
	@# copy css style sheets and images
	rsync -rp --delete --exclude ".svn" --exclude "*.xcf" --exclude "*.sh" css images $(buildDir) 
	@# scale all icons
	for s in 16x16 24x24 32x32 64x64; do \
		mkdir -p $(buildDir)/images/icons/$$s; \
		for i in icons/*.png; do \
			convert "$$i" -resize $$s "$(buildDir)/images/icons/$$s/$${i##*/}"; \
		done; \
	done
	@# symlinks as temporary directories with timestamp
	@#TODO: this should be done with an Apache redirection
	for i in js css; do \
		rm -f "$(buildDir)/$${i}_"*; \
		ln -s "$$i" "$(buildDir)/$${i}_$(timestamp)"; \
	done;

install: build
	@# copy all files from the build directory .. exclude file of the pattern ".*"
	mkdir -p $(DESTDIR)$(pkgDir)
	rsync -rp --exclude ".svn" --exclude ".*" $(buildDir)/ $(DESTDIR)$(pkgDir)
	
