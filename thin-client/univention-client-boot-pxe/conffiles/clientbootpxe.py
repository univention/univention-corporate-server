# -*- coding: utf-8 -*-
#
# Univention Client Boot PXE
#  baseconfig/listener module: update nameserver for PXE clients
#
# Copyright 2004-2010 Univention GmbH
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

import os
import re
from fileinput import *
from glob import glob

var = 'pxe/nameserver'
pattern = '/var/lib/univention-client-boot/pxelinux.cfg/*'

def update_nameserver(line, nameserver):
	line = line.strip('\n')
	if 'DNSSERVER=' in line:
		sp = line.split(' ')
		line = ''
		for element in sp:
			if element.startswith('DNSSERVER='):
				element = 'DNSSERVER=%s' % nameserver
			if line == '':
				line = element
			else:
				line = '%s %s' % (line, element)
		return line
	else:
		return line

def update_loglevel(line, loglevel):
	line = line.strip('\n')
	if 'APPEND root=' in line:
		line = re.sub(" loglevel=\d+", "", line)
		if loglevel:
			line = line + " loglevel=%s" % loglevel
	return line

def update_quiet(line, quiet):
	line = line.strip('\n')
	if 'APPEND root=' in line:
		if ' quiet' in line:
			if not quiet:
				line = line.replace(" quiet", "")
		if not ' quiet' in line:
			if quiet:
				line = line + " quiet"
	return line

def handler(baseConfig, changes):
	nameserver = baseConfig.get(var)
	quiet = False
	if baseConfig.get('pxe/quiet', "False").lower() in ['yes', 'true', '1']:
		quiet = True
	loglevel = baseConfig.get('pxe/loglevel', False)
	for line in input(glob(pattern), inplace = True):
		if nameserver:
			line = update_nameserver(line, nameserver)
		line = update_quiet(line, quiet)
		line = update_loglevel(line, loglevel)
		print line
