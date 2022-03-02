# -*- coding: utf-8 -*-
#
# Copyright (C) 2020-2022 Univention GmbH
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
"""
>>> RE_DEBIAN_PACKAGE_NAME.match("0").groups()
('0',)
>>> RE_DEBIAN_PACKAGE_VERSION.match("0").groups()
(None, '0', None)
>>> RE_DEBIAN_PACKAGE_VERSION.match("0-0").groups()
(None, '0', '0')
>>> RE_DEBIAN_PACKAGE_VERSION.match("0-0-0").groups()
(None, '0-0', '0')
>>> RE_DEBIAN_CHANGELOG.match("0 (0) unstable; urgency=low").groups()
('0', '0', ' unstable', ' urgency=low')
>>> RE_HASHBANG_SHELL.match('#!/bin/sh') is not None
True
>>> RE_HASHBANG_SHELL.match('#! /bin/bash') is not None
True
"""
import re

# /usr/share/perl5/Dpkg/Changelog/Entry/Debian.pm
WORD_CHARS = '[0-9a-z]'
NAME_CHARS = '[+.0-9a-z-]'
RE_DEBIAN_PACKAGE_NAME = re.compile(
	r'''^
	({wc}{nc}*)  # Package name
	$'''.format(wc=WORD_CHARS, nc=NAME_CHARS), re.VERBOSE)
RE_DEBIAN_PACKAGE_VERSION = re.compile(
	r'''^
	(?: (?P<epoch>[0-9]+) : )?
	(?P<upstream> [0-9][+.0-9a-z~-]*? )
	(?: - (?P<revision>[+.0-9a-z~]+) )?
	$''', re.VERBOSE)
RE_DEBIAN_CHANGELOG = re.compile(
	r'''^
	({wc}{nc}*)  # Package name
	[ ]
	\( ([^ ()]+) \)  # Package version
	( (?: \s+ {nc}+ )+ )  # Target distribution
	;
	(.*?)  # key=value options
	\s*$'''.format(wc=WORD_CHARS, nc=NAME_CHARS), re.MULTILINE | re.VERBOSE)
RE_HASHBANG_SHELL = re.compile(r'^#!\s*/bin/(?:a|ba|c|da|z)?sh\b')


if __name__ == '__main__':
	import doctest
	doctest.testmod()
