#!/usr/bin/make -f
#
# Univention Dojo Package
#  Makefile for building/installing the package
#
# Copyright 2008-2011 Univention GmbH
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

#version := $(shell dpkg-parsechangelog | sed -ne 's/^Version: //p')
#copyrightyear := $(shell date +%Y)
PKGNAME=univention-dojo
INSTDIR=/usr/share/${PKGNAME}

# get the most recent dojo version of all src-packages that can be found in the
# current directory 
DOJO_VERSION=$(shell find . -maxdepth 1 -name "dojo-release*-src.tar.gz" | sort -r | sed -n '1 s/^.*dojo-release-\(.*\)-src.tar.gz$$/\1/ p')
DOJO_DIR=dojo-release-$(DOJO_VERSION)-src

.PHONY: clean all install

build: $(DOJO_DIR)

$(DOJO_DIR):
	tar xzf $@.tar.gz
	patch -p0 < fix_bashism.patch
	patch -p0 < fix_grid_focus.patch
	patch -p0 < fix_normalizeLocale.patch
	patch -p0 < fix_standbyOpacity.patch
	patch -p0 < fix_dijit_findWidgets.patch
	patch -p0 < fix_dojo_style.patch
	patch -p0 < fix_dojo_position.patch
	patch -p0 < fix_dojox_form_Uploader.patch
	patch -p0 < fix_dojoStoreMemory.patch

all: install

clean:
	rm -rf $(DOJO_DIR)

install: build
	@# main directory
	install -m 0755 -d "$(DESTDIR)$(INSTDIR)"
	@# directories
	find $(DOJO_DIR) -mindepth 1 -type d | sed 's|$(DOJO_DIR)/||' | while read i; do \
		install -m 0755 -d "$(DESTDIR)$(INSTDIR)/$$i"; \
	done
	@# files .. set execute bit for scripts
	find $(DOJO_DIR) -type f | sed 's|$(DOJO_DIR)/||' | while read i; do  \
		mod=0644; \
		[ "$${i%.sh}" != "$$i" ] && mod=0755; \
		install -m $$mod "$(DOJO_DIR)/$$i" "$(DESTDIR)$(INSTDIR)/$$i"; \
	done

