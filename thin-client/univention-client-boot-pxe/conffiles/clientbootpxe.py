# -*- coding: utf-8 -*-
#
# Univention Client Boot PXE
#  baseconfig/listener module: update nameserver for PXE clients
#
# Copyright (C) 2004, 2005, 2006, 2007 Univention GmbH
#
# http://www.univention.de/
#
# All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# Binary versions of this file provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

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
