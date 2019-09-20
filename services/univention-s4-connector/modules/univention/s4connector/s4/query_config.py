#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention S4 Connector
#  reads the internal configuration
#
# Copyright 2004-2019 Univention GmbH
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


from __future__ import print_function
import ConfigParser
import cPickle
import os


def fixup(s):
	# add proper padding to a base64 string
	n = len(s) & 3
	if n:
		s = s + "=" * (4 - n)
	return s


configfile = '/etc/univention/s4connector/s4internal.cfg'
if not os.path.exists(configfile):
	print("ERROR: Config-File not found, maybe connector was never started")
config = ConfigParser.ConfigParser()
config.readfp(open(configfile))

for section in config.sections():
	print("SECTION: %s" % section)
	for name, value in config.items(section):
		if section == "S4 GUID":
			print(" --%s: %s" % (name, value))
			print(" --%s: %s" % (fixup(name).decode('base64'), fixup(value).decode('base64')))
		else:
			print(" -- %50s : %s" % (name, value))
