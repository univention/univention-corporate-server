# -*- coding: utf-8 -*-
#
# Univention Client Boot PXE
#  baseconfig/listener module: update nameserver for PXE clients
#
# Copyright (C) 2004, 2005, 2006 Univention GmbH
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
		print line
	else:
		print line

def handler(baseConfig, changes):
	nameserver = baseConfig.get(var)
	if nameserver:
		for line in input(glob(pattern), inplace = True):
			update_nameserver(line, nameserver)
