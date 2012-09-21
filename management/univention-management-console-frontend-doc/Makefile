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

dojo_tmp_dir:=$(CURDIR)/univention-dojo
rel_root_path:=$(shell echo '$(dojo_tmp_dir)/util/docscripts' | sed -e 's,/[^/]*,../,g')

build: umc.xml

umc.xml:
	@# generate umc.xml for univention-dojo-api-viewer
	cp -r /usr/share/univention-dojo/ '$(dojo_tmp_dir)'
	echo 'location = $(rel_root_path)$(CURDIR)/umc/' > '$(dojo_tmp_dir)/util/docscripts/modules/umc.module.properties'
	cd '$(dojo_tmp_dir)/util/docscripts/'; \
	php generate.php umc dojo dijit dojox --serialize=xml --clean --outfile=$(rel_root_path)../usr/share/univention-management-console-frontend-src/umc
	rm -rf $(dojo_tmp_dir)

install: build
	@# move umc.xml
	mkdir -p '$(DESTDIR)/usr/share/univention-dojo-api-viewer'
	cp umc.xml '$(DESTDIR)/usr/share/univention-dojo-api-viewer'

clean:
	rm -rf umc.xml
