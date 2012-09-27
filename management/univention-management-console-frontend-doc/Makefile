#!/usr/bin/make -f
#
# Univention Management Console Frontend Package
#  Makefile for building/installing the package
#
# Copyright 2011-2012 Univention GmbH
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

build: umc.xml

# FIXME: Remove?
js-doc-parse:
	git clone --recursive https://github.com/wkeese/js-doc-parse.git

umc.xml: js-doc-parse univention-dojo univention-dojo/umc
	cd $<; \
		git apply < ../api_generator.patch && \
		./parse.sh ../univention-dojo/umc ../univention-dojo/dojo ../univention-dojo/dijit ../univention-dojo/dojox

univention-dojo: /usr/share/univention-dojo
	cp -r $< $@
univention-dojo/umc: /usr/share/univention-management-console-frontend-src/umc
	cp -r $< $@

install: build
	install -d '$(DESTDIR)/usr/share/univention-dojo-api-viewer'
	install -m644 umc.xml '$(DESTDIR)/usr/share/univention-dojo-api-viewer'

clean:
	$(RM) umc.xml
	$(RM) -r univention-dojo
	$(RM) -r js-doc-parse
