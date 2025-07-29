#!/usr/bin/make -f
#
# Univention Dojo Package
#  Makefile for building/installing the package
#
# SPDX-FileCopyrightText: 2008-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

PKGNAME := univention-dojo
INSTDIR := /usr/share/${PKGNAME}
LIBDIR := $(CURDIR)/libs
VER := 1.16.3

# all JS packages
LIBS := dojo libs/dgrid libs/dstore libs/put-selector libs/xstyle libs/dompurify

.PHONY: build
build: $(LIBS)

.PHONY: clean
clean:
	$(RM) -r dojo $(LIBDIR)
	$(RM) -r univention-dojo-api-viewer
	$(RM) dojo-*.tar.gz

dojo-release-$(VER)-src.tar.gz:
	wget -N "https://updates.software-univention.de/download/large-build-files/dojo/$@"
	echo "8086fc38a9af04fcee27b455e420b652a740c5492efe93ee84d9a9d9ca9d4a43f04fd7190471d845751aac9224fdce71699555932c6004a8e8e975ecc65f675e $@" | sha512sum -c

# treat dojo JS package different
dojo: dojo-release-$(VER)-src.tar.gz
	$(RM) -r $@.tmp
	tar xf $< --transform="s|^[^/]*|$@.tmp|"
	patch -d $@.tmp -p1 -i ../fix_bashism.patch
	patch -d $@.tmp -p1 -i ../fix_grid_focus.patch
	patch -d $@.tmp -p1 -i ../fix_standbyOpacity.patch
	patch -d $@.tmp -p1 -i ../fix_dojo_iframe_textarea.patch
	patch -d $@.tmp -p1 -i ../fix_Dialog_autofocus.patch
	patch -d $@.tmp -p1 -i ../fix_Dialog_resize_handling.patch
	patch -d $@.tmp -p1 -i ../fix_dojox_widget_Standby_scrollbar_offset.patch
	patch -d $@.tmp -p1 -i ../fix_dojox_widget_Standby_cntrIndicatorTop.patch
	patch -d $@.tmp -p1 -i ../fix_dijit_ProgressBar_additional_css_classes.patch
	patch -d $@.tmp -p0 -i ../fix_dijit_MenuItem.patch
	patch -d $@.tmp -p0 -i ../fix_dijit_PopupMenuItem.patch
	patch -d $@.tmp -p0 -i ../fix_dojox_enhancedgrid_selection_icon.patch
	mv $@.tmp $@

libs/dgrid: dgrid-1.1.0.tar.gz
	mkdir -p libs
	$(RM) -r $@.tmp
	tar -C libs --no-same-owner -xf $< --transform="s|^[^/]*|$(@F).tmp|"
	patch -d $@.tmp -p0 -i ../../fix_dgrid_Grid_sortIcon.patch
	mv $@.tmp $@

# all other JS packages
libs/%: %-*.tar.gz
	mkdir -p libs
	$(RM) -r $@.tmp
	tar -C libs --no-same-owner -xf $< --transform="s|^[^/]*|$*.tmp|"
	mv $@.tmp $@
