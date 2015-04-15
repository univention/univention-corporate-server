#!/usr/bin/make -f
#
# Univention Management Console Frontend Theme Package
#  Makefile for building/installing the UMC theme
#
# Copyright 2014 Univention GmbH
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

.PHONY: build build-common update repack clean

REPO=dijit-claro-stylus
TMP_THEME_DIR=tmp/dijit/themes/$(REPO)
TMP_THEME_CSS=$(TMP_THEME_DIR)/umc.css
GIT_PARAMS=--git-dir $(REPO)/.git
BOOSTRAP_FILE=$(TMP_THEME_DIR)/bootstrap.css
INSTALL_DIR=/usr/share/univention-management-console-frontend/js/dijit/themes/umc
ICON_FILES=icons.svg icons-small.svg icons-white.svg icons-small-white.svg
ICON_FILES_PNG=$(addprefix $(TMP_THEME_DIR)/images/,$(ICON_FILES:.svg=.png))

.PRECIOUS: $(REPO) Makefile

all: build

$(REPO):
	git clone https://github.com/kfranqueiro/$(REPO)
	git $(GIT_PARAMS) gc

tmp: $(REPO)
	# copy dijit-claro-stylus, dojo, and dijit files into tmp dir
	mkdir tmp
	cp -r /usr/share/univention-dojo/dojo /usr/share/univention-dojo/dijit /usr/share/univention-dojo/dojox tmp
	cp -r $(PWD)/$(REPO) tmp/dijit/themes
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

css/umc.css: tmp css $(BOOSTRAP_FILE) $(ICON_FILES_PNG)
	# compile all stylus files
	stylus $(TMP_THEME_DIR) $(TMP_THEME_DIR)/form $(TMP_THEME_DIR)/layout $(TMP_THEME_DIR)/site
	# Workaround: mark several commands as comments (/*TMP ... */) 
	# to avoid parse errors with stylus
	sed -i 's/.*\(^\s\+#\|filter: alpha\|filter:\|top: expression\).*/\/\*TMP\0\*\//; /\/\*TMP/ { s|/\*[^*]*\*/\*/|*/| }' $$(find tmp/dojo tmp/dijit -name "*.css")
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

build: css/umc.css css/fonts

build-dev: tmp css $(BOOSTRAP_FILE) css/fonts $(ICON_FILES_PNG)
	cp -r $(TMP_THEME_DIR)/* css
	cd css; stylus -m .
	cd css/form; stylus -m .
	cd css/layout; stylus -m .
	cd css/site; stylus -m .
	cp -frsn /usr/share/univention-management-console-frontend/js/dijit/themes/umc/icons css

install: build
	cd css; find ./ -type d -exec install -m0755 -d $(DESTDIR)$(INSTALL_DIR)/{} \;
	cd css; find ./ -type f -exec install -m0644 {} $(DESTDIR)$(INSTALL_DIR)/{} \;
	install -m0755 -d $(DESTDIR)$(INSTALL_DIR)/icons/scalable
	install -m0755 -d $(DESTDIR)$(INSTALL_DIR)/icons/50x50
	install -m0755 -d $(DESTDIR)$(INSTALL_DIR)/icons/16x16

repack:
	git $(GIT_PARAMS) repack -d

update:
	git $(GIT_PARAMS) fetch
	# make sure that all new object files are packed into one package
	# this should make the SVN commit easier
	git $(GIT_PARAMS) repack -d

clean:
	rm -rf tmp css

