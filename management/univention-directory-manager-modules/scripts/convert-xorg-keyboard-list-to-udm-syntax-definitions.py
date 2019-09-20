#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Script to generate syntax definitions for the XKeyboardLayout in Univention Directory
# Manager from the definitions shipped by X.org in /usr/share/X11/xkb/rules/xorg.lst
#
# Copyright 2011-2019 Univention GmbH
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

import sys

f = open(sys.argv[1])
lines = f.readlines()
lines_processed = 0

print "\t\t('', ''),"
for i in lines:
	elem = i.split()
	lines_processed = lines_processed + 1
	country = ""
	for j in elem[1:]:
		country = country + j + " "

	syntax = "\t\t('" + elem[0] + "', '" + country.strip() + "')"
	if lines_processed < len(lines):
		syntax = syntax + ","

	print syntax
