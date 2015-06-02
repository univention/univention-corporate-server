#!/usr/bin/make -f
#
# Copyright 2012-2015 Univention GmbH
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

dojoDir:=/usr/share/univention-dojo
timestamp:=$$$(shell date +'%Y%d%m%H%M%S')$$
version:=$(shell dpkg-parsechangelog | sed -ne 's/^Version: //p')
buildDir:=$(CURDIR)/build
buildJsDir:=$(buildDir)/www/ucs-overview/js
buildCssDir:=$(buildDir)/www/ucs-overview/css
buildBootstrap:=$(buildCssDir)/bootstrap.css
jsFiles:=$(shell find umc -name "*.js")

.PHONY: build build-dev

build: l10n $(buildDir) i18n $(buildDir)/www/ucs-overview/css/fonts

build-dev: l10n $(buildCssDir) $(buildBootstrap) i18n $(buildDir)/www/ucs-overview/css/fonts
	mkdir -p build $(buildJsDir)
	cp -r www build
	# symlink UCS javascript code
	[ -e $(buildJsDir)/ucs ] || cp -frsn $(CURDIR)/js/ucs $(buildJsDir)/ucs
	# symlinks for dojo packages
	for idir in dojo dijit dojox; do \
		[ -e $(buildJsDir)/$$idir ] || ln -s /usr/share/univention-dojo/$$idir $(buildJsDir); \
	done
	# symlinks for entries.json and languages.json
	for ijson in entries languages; do \
		ln -s /var/www/ucs-overview/$$ijson.json $(buildDir)/www/ucs-overview; \
	done

%/fonts:
	mkdir -p $@
	unzip -o -j clearsans-1.00.zip "*.woff" -d $@

i18n:
	/usr/bin/dh-umc-translate -p univention-apache -l de -o js/ucs $(jsFiles)

l10n: js/ucs/de.json

%.json: %.po
	dh-umc-po2json "$<"

$(buildDir): $(buildJsDir) $(buildCssDir) $(buildBootstrap)
	mkdir -p $@
	cp -r www $@

# rule for the main dojo build process
$(buildJsDir): 
	/usr/share/univention-dojo/util/buildscripts/build.sh profile=build_profile.js version="$(version)"

# rule for converting stylus CSS files into one final CSS file
$(buildCssDir):
	mkdir -p $@
	stylus -o $@ css
	cp css/ucs.css $@
	cp -r css/images $@
	cp -r css/icons $@
	# Workaround: mark several commands as comments (/*TMP ... */)
	# to avoid parse errors with stylus
	sed -i 's/.*\(^\s\+#\|filter: alpha\|filter:\|top: expression\).*/\/\*TMP\0\*\//; /\/\*TMP/ { s|/\*[^*]*\*/\*/|*/| }' $$(find $@ -name "*.css")
	# compile all .css files into one big file
	stylus --resolve-url --include-css $@/ucs.css
	# Workaround: remove the temporarily commented lines
	sed -i 's|/\*TMP\(.*\)\*/|\1|' $@/ucs.css

$(buildBootstrap): bootstrap.zip
	unzip -o -j $< "*bootstrap.css" -d $(buildCssDir)
	sed -i '/font-size: 10px/d' $@;

install: build
	# copy all files from the build directory .. exclude file of the tmp directory
	mkdir -p "$(DESTDIR)$(pkgDir)"
	cp -r $(buildDir)/* "$(DESTDIR)$(pkgDir)/var"

clean:
	rm -rf $(buildDir)
	rm -f js/ucs/de.json

