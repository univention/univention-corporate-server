#!/usr/bin/make -f
#
# Univention Management Console Frontend Package
#  Makefile for building/installing the package
#
# Copyright 2011-2013 Univention GmbH
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

build: univention-management-console-frontend-doc univention-dojo-api-viewer

js-doc-parse.tar.gz:
	git clone --recursive https://github.com/wkeese/js-doc-parse.git
	cd js-doc-parse && git checkout all-my-changes
	tar cvzf js-doc-parse.tar.gz js-doc-parse
#	cd js-doc-parse && git archive --format=tar js-doc-parse | gzip > js-doc-parse.tar.gz

api-viewer.tar.gz:
	git clone https://github.com/wkeese/api-viewer.git
	tar cvzf api-viewer.tar.gz api-viewer
#	cd api-viewer && git archive --format=tar api-viewer | gzip > api-viewer.tar.gz

js-doc-parse:
	tar xvzf js-doc-parse.tar.gz

api-viewer:
	tar xvzf api-viewer.tar.gz

univention-dojo: /usr/share/univention-dojo
	cp -r /usr/share/univention-dojo $@
	cp -r /usr/share/univention-management-console-frontend-src/umc $@
	# workarounds for referenced external modules
	for imodule in umc/modules/udm/LicenseImportDialog.js umc/modules/udm/LicenseDialog.js umc/modules/undefined.js https://www.piwik.univention.de/piwik.js.js; do \
		mkdir -p univention-dojo/$${imodule%/*}; \
		echo 'define([],function(){});' > univention-dojo/$${imodule}; \
	done
	# remove test directories
	rm -rf univention-dojo/dgrid/test univention-dojo/put-selector/test univention-dojo/xstyle/test

univention-management-console-frontend-doc: data

data: js-doc-parse univention-dojo
	#creating details.xml and tree.json
	install -m755 -d 'data/1.8'
	cd $< && \
		git apply < ../$<.patch && \
		./parse.sh ../univention-dojo/umc ../univention-dojo/dojo ../univention-dojo/dijit ../univention-dojo/dgrid # ../univention-dojo/dojox FIXME: dojox produces errors because "build" directory does not exists

univention-dojo-api-viewer: api-viewer
	cp -r $< $@
	cd $@ && \
		git apply < ../$<.patch;
	#@ remove unneeded things: security
	rm -rf $@/install $@/tests || true

install: build
	install -m0755 -d '$(DESTDIR)/usr/share'
	# univention-dojo-api-viewer
	install -m0755 -d '$(DESTDIR)/usr/share/univention-doc/src'
	install -m0755 -d '$(DESTDIR)/var/www/ucs-overview/images'
	rsync -rpl --exclude '.svn' --exclude '.git' univention-management-console-doc '$(DESTDIR)/usr/share/univention-doc/src/'
	rsync -rpl --exclude '.svn' --exclude '.git' univention-dojo-api-viewer '$(DESTDIR)/usr/share/'
	install -m0644 icon/dojo-api.png '$(DESTDIR)/var/www/ucs-overview/images/'
	# univention-management-console-frontend-doc
	rsync -rpl data '$(DESTDIR)/'

clean:
	$(RM) -r data
	$(RM) -r univention-dojo univention-dojo-api-viewer
	$(RM) -r js-doc-parse api-viewer
