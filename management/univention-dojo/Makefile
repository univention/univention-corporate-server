#!/usr/bin/make -f
#
# Univention Dojo Package
#  Makefile for building/installing the package
#
# Copyright 2008-2019 Univention GmbH
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

#version := $(shell dpkg-parsechangelog | sed -ne 's/^Version: //p')
#copyrightyear := $(shell date +%Y)
PKGNAME=univention-dojo
INSTDIR=/usr/share/${PKGNAME}
LIBDIR:=$(CURDIR)/libs

# all JS packages
LIBS=dojo libs/dgrid libs/dstore libs/put-selector libs/xstyle libs/dompurify

.PHONY: clean all install

build: $(LIBS)

all: install

clean:
	rm -rf dojo $(LIBDIR)
	rm -rf univention-dojo-api-viewer
	rm -rf dojo-*.tar.gz

dojo: dojo-release-1.12.4-src.tar.gz
dojo-release-1.12.4-src.tar.gz:
	wget "https://updates.software-univention.de/download/large-build-files/dojo/$@"
	echo "02f0cc882b41003bcbc9e16d372cadd4b19abc1bcb4b1fb99eb8f0868df78fa7520f2cde85cde0f1e6756002efa26f52899e8a901d2725419158ca7f53eb5200  $@" | sha512sum -c

# treat dojo JS package different
dojo:
	tar -xzf $<
	[ ! -d $@ ] && mv $@*/ $@ || true
	cd dojo; \
	patch -p1 < ../fix_bashism.patch && \
	patch -p1 < ../fix_grid_focus.patch && \
	patch -p1 < ../fix_standbyOpacity.patch && \
	patch -p1 < ../fix_dojo_iframe_textarea.patch && \
	patch -p1 < ../fix_Dialog_autofocus.patch && \
	patch -p1 < ../fix_Dialog_resize_handling.patch && \
	patch -p1 < ../fix_dojox_widget_Standby_scrollbar_offset.patch && \
	patch -p1 < ../fix_dojox_widget_Standby_cntrIndicatorTop.patch && \
	patch -p1 < ../fix_dijit_ProgressBar_additional_css_classes.patch

# all other JS packages
libs/%: %-*.tar.gz
	mkdir -p libs
	tar -C libs --no-same-owner -xzf $<
	if [ ! -d $@ ]; then mv $@*/ $@; fi
