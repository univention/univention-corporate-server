#!/usr/bin/make -f
#
# Univention Dojo Package
#  Makefile for building/installing the package
#
# SPDX-FileCopyrightText: 2008-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

.PHONY: build dojo dojox dijit dijit-themes util patches download-libs download clean

PKGNAME := univention-dojo
INSTDIR := /usr/share/${PKGNAME}
LIBDIR := $(CURDIR)/libs
DOJO := 1.17.3
DGRID := 1.3.3
DSTORE := 1.2.1
DOMPURIFY := 2.5.8
# DOMPURIFY := 3.3.0
PUTSELECTOR := 0.3.6
XSTYLE := 0.3.3

# all JS packages
LIBS := dojo dojox dijit dijit-themes util libs/dgrid libs/dstore libs/put-selector libs/xstyle libs/dompurify

build: download-libs $(LIBS) patches

clean:
	$(RM) -r dojo $(LIBDIR)
	$(RM) *.tar.gz

download-libs: dgrid-$(DGRID).tar.gz dstore-${DSTORE}.tar.gz xstyle-${XSTYLE}.tar.gz dompurify-${DOMPURIFY}.tar.gz put-selector-${PUTSELECTOR}.tar.gz
	echo

dojo-release-$(DOJO)-src.tar.gz:
	wget -N "https://updates.software-univention.de/download/large-build-files/dojo/$@"
	echo "0d4780eace9f23c02e579b11087df79201259db4d7ff48517ad24372a807a1755ea30a34341155fb876b6d16d512a29ca1b86c3dbf02b91c8dce7c3c344ef2ac $@" | sha512sum -c

dojox-release-$(DOJO)-src.tar.gz:
	wget -N "https://updates.software-univention.de/download/large-build-files/dojo/$@"
	echo "e821e5f3e88edcf5bdd17babc2a8e0800448a15f8808635610ba0858202729cd41f88ff6eaba65f441266b2827cf81f29c5eeb315027f75df56c0d757887e00b $@" | sha512sum -c

dijit-release-$(DOJO)-src.tar.gz:
	wget -N "https://updates.software-univention.de/download/large-build-files/dojo/$@"
	echo "ffa22456f74ba4f59067be92c8259b767e530831f792ce0da824e03dcd22191d72fb1d3a5f8b510f86d8d3927ba7768e7598b47546ea050fe9d8477f8e28deee $@" | sha512sum -c

dijit-themes-release-$(DOJO)-src.tar.gz:
	wget -N "https://updates.software-univention.de/download/large-build-files/dojo/$@"
	echo "f0a4cdcdb0cb0e1b605fe0fda0606552d8df8a3c28f8ed78f3106df5d84859ed9e317758501d8b4d7a8025a21d6e7c54b4732159fc5f780dffa5512c721c19c3 $@" | sha512sum -c

util-release-$(DOJO)-src.tar.gz:
	wget -N "https://updates.software-univention.de/download/large-build-files/dojo/$@"
	echo "061f063a1fd84207b7431882d03a07b2d18929957a783f71fd1a85f487bac9b413694da0f0179c9159f131680677dc3312962abc8cb8083c23f80b1f0d091c1a $@" | sha512sum -c

dstore-$(DSTORE).tar.gz:
	wget -N "https://updates.software-univention.de/download/large-build-files/dojo/$@"
	echo "98c71110859ded349d030db7d2a295fa1c567cfc701d281ede6836af4c76fd7ea507dcac2ca62b76530de595641f789a6f35b2a77086017094fc9d3787417013 $@" | sha512sum -c

dgrid-$(DGRID).tar.gz:
	wget -N "https://updates.software-univention.de/download/large-build-files/dojo/$@"
	echo "291a8696d28978d76799d8658c2a110157cdb99fd897303e4e2c7e30bad9d661cffafc851054fba33bbb6cd922f16638818d0d2f790bb40894d13da211fb267e $@" | sha512sum -c

xstyle-$(XSTYLE).tar.gz:
	wget -N "https://updates.software-univention.de/download/large-build-files/dojo/$@"
	echo "3828517c0112cddfa06ff2870dbefe63be8d14c348849a8ef505801c49aeaddfc7dba413f120b4f8250408418ce29cb41d918e0f5b94d04b58fd099460089a65 $@" | sha512sum -c

dompurify-$(DOMPURIFY).tar.gz:
	wget -N "https://updates.software-univention.de/download/large-build-files/dojo/$@"
	echo "23f02a867b94352bd9f104783951f29467a00b2e6fce05314d7992ec5fa8c73289470818ec2ce711272976735f058be238fe7051680949e90bd5ebb01a39c20a $@" | sha512sum -c
	# echo "19636687f62e1e8b2ce1b8dc0db9413b5651feeed85c8eb927201a11c60ee5eb6294ef7dd573ef2a4f3f5197a7bc02d3263a6558af3225e8b455614e8c573c2d $@" | sha512sum -c

put-selector-$(PUTSELECTOR).tar.gz:
	wget -N "https://updates.software-univention.de/download/large-build-files/dojo/$@"
	echo "b1a9b9586412a8b7f0234cbf94b87b40ec12d3562d5383b7ba2a537e0c833388ec815330ecd456b7341da4371446d1d85d8fe63a581ccc3319a385bd644f29ec $@" | sha512sum -c

# treat dojo JS package different
dojo: dojo-release-$(DOJO)-src.tar.gz
	$(RM) -r $@.tmp
	tar xf $< --transform="s|^[^/]*|$@.tmp/$@|"

dojox: dojox-release-$(DOJO)-src.tar.gz
	tar xf $< --transform="s|^[^/]*|dojo.tmp/$@|"

dijit: dijit-release-$(DOJO)-src.tar.gz
	tar xf $< --transform="s|^[^/]*|dojo.tmp/$@|"

dijit-themes: dijit-themes-release-$(DOJO)-src.tar.gz
	tar xf $< --transform="s|^[^/]*|dojo.tmp/$@|"

util: util-release-$(DOJO)-src.tar.gz
	tar xf $< --transform="s|^[^/]*|dojo.tmp/$@|"

patches: dojo dojox dijit dijit-themes util
	patch -d dojo.tmp -p1 -i ../fix_bashism.patch
	patch -d dojo.tmp -p1 -i ../fix_grid_focus.patch
	patch -d dojo.tmp -p1 -i ../fix_standbyOpacity.patch
	patch -d dojo.tmp -p1 -i ../fix_dojo_iframe_textarea.patch
	patch -d dojo.tmp -p1 -i ../fix_Dialog_autofocus.patch
	patch -d dojo.tmp -p1 -i ../fix_Dialog_resize_handling.patch
	patch -d dojo.tmp -p1 -i ../fix_dojox_widget_Standby_scrollbar_offset.patch
	patch -d dojo.tmp -p1 -i ../fix_dojox_widget_Standby_cntrIndicatorTop.patch
	patch -d dojo.tmp -p1 -i ../fix_dijit_ProgressBar_additional_css_classes.patch
	patch -d dojo.tmp -p0 -i ../fix_dijit_MenuItem.patch
	patch -d dojo.tmp -p0 -i ../fix_dijit_PopupMenuItem.patch
	patch -d dojo.tmp -p0 -i ../fix_dojox_enhancedgrid_selection_icon.patch
	mv dojo.tmp dojo

libs/dgrid: dgrid-$(DGRID).tar.gz
	mkdir -p libs
	$(RM) -r $@.tmp
	tar -C libs --no-same-owner -xf $< --transform="s|^[^/]*|$(@F).tmp|"
	patch -d $@.tmp -p0 -i ../../fix_dgrid_Grid_sortIcon.patch
	patch -d $@.tmp -p0 -i ../../fix_dgrid_Tree_reload.patch
	mv $@.tmp $@

libs/dstore: dstore-${DSTORE}.tar.gz
	mkdir -p libs
	tar -C libs --no-same-owner -xf $< --transform="s|^[^/]*|$(@F)|"

libs/put-selector: put-selector-${PUTSELECTOR}.tar.gz
	mkdir -p libs
	tar -C libs --no-same-owner -xf $< --transform="s|^[^/]*|$(@F)|"

libs/xstyle: xstyle-${XSTYLE}.tar.gz
	mkdir -p libs
	tar -C libs --no-same-owner -xf $< --transform="s|^[^/]*|$(@F)|"

libs/dompurify: dompurify-${DOMPURIFY}.tar.gz
	mkdir -p libs
	$(RM) -r $@.tmp
	tar -C libs --no-same-owner -xf $< --transform="s|^[^/]*|$(@F).tmp|"
	mv $@.tmp/dist $@
	$(RM) -r $@.tmp
	$(RM) $@/*.cjs.* $@/*.es.*
	cp dompurify.js libs/dompurify/package.js

# doesn't work since the files are downloaded
# # all other JS packages
# libs/%: %-*.tar.gz
# 	mkdir -p libs
# 	$(RM) -r $@.tmp
# 	tar -C libs --no-same-owner -xf $< --transform="s|^[^/]*|$*.tmp|"
# 	mv $@.tmp $@

download:
	wget -O dojo-release-${DOJO}-src.tar.gz https://github.com/dojo/dojo/archive/refs/tags/${DOJO}.tar.gz
	wget -O dojox-release-${DOJO}-src.tar.gz https://github.com/dojo/dojox/archive/refs/tags/${DOJO}.tar.gz
	wget -O dijit-release-${DOJO}-src.tar.gz https://github.com/dojo/dijit/archive/refs/tags/${DOJO}.tar.gz
	wget -O dijit-themes-release-${DOJO}-src.tar.gz https://github.com/dojo/dijit-themes/archive/refs/tags/${DOJO}.tar.gz
	wget -O util-release-${DOJO}-src.tar.gz https://github.com/dojo/util/archive/refs/tags/${DOJO}.tar.gz
	wget -O dstore-${DSTORE}.tar.gz https://github.com/dojo/dojo1-dstore/archive/refs/tags/v${DSTORE}.tar.gz
	wget -O dgrid-${DGRID}.tar.gz https://github.com/dojo/dojo1-dgrid/archive/refs/tags/v${DGRID}.tar.gz
	wget -O xstyle-${XSTYLE}.tar.gz https://github.com/kriszyp/xstyle/archive/refs/tags/v${XSTYLE}.tar.gz
	wget -O dompurify-${DOMPURIFY}.tar.gz https://github.com/cure53/DOMPurify/archive/refs/tags/${DOMPURIFY}.tar.gz
	wget -O put-selector-${PUTSELECTOR}.tar.gz https://github.com/kriszyp/put-selector/archive/refs/tags/v${PUTSELECTOR}.tar.gz
