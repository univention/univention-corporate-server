#!/usr/bin/make -f
#
# python-notifier
#  Makefile for building/installing the package
#
# Copyright 2015-2019 Univention GmbH
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

.PHONY: build

GIT_PARAMS=--git-dir python-notifier/.git

build: usr/share/doc/python-notifier usr/share/doc/python3-notifier

usr/share/doc/python-notifier:
	mkdir -p usr/share/doc/python-notifier
	gzip -c python-notifier/ChangeLog > usr/share/doc/python-notifier/changelog.gz

usr/share/doc/python3-notifier:
	mkdir -p usr/share/doc/python3-notifier
	gzip -c python-notifier/ChangeLog > usr/share/doc/python3-notifier/changelog.gz

repack:
	git $(GIT_PARAMS) repack -d

update:
	git $(GIT_PARAMS) pull --rebase
	git $(GIT_PARAMS) repack -d

.PHONY: clean
clean:
	$(RM) -r usr
