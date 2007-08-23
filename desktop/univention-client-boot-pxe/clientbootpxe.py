#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Client Boot PXE
#  Univention Listener Module
#
# Copyright (C) 2001, 2002, 2003, 2004, 2005, 2006 Univention GmbH
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA	 02110-1301	 USA

name='clientbootpxe'
description='PXE configuration for thin clients'
filter='(objectClass=univentionThinClient)'
attributes=['objectClass', 'aRecord', 'cn']

import listener
import os, re, ldap, string, univention.debug

pxebase = '/var/lib/univention-client-boot/pxelinux.cfg'
pxeconfig_file = '/etc/univention/client-boot-pxe/pxeconfig'

def ip_to_hex(ip):
	if ip.count('.') != 3:
		return ''
	o = ip.split('.')
	return '%02X%02X%02X%02X' % (int(o[0]), int(o[1]), int(o[2]), int(o[3]))

def handler(dn, new, old):

	# remove pxe host file
	if 'univentionThinClient' in old.get('objectClass',[]) and old.has_key('aRecord'):
		basename = ip_to_hex(old['aRecord'][0])
		if not basename:
			univention.debug.debug(univention.debug.LISTENER, univention.debug.ERROR, 'PXE: invalid IP address %s' % old['aRecord'][0])
			return
		filename = os.path.join(pxebase, basename)
		if os.path.exists(filename):
			listener.setuid(0)
			try:
				os.unlink(filename)
			finally:
				listener.unsetuid()

	# create pxe host file(s)
	if new and new.has_key('cn') and new.has_key('aRecord'):

		cn = new['cn'][0]
		univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, 'PXE: writing configuration for host %s' % cn)

		basename = ip_to_hex(new['aRecord'][0])
		if not basename:
			univention.debug.debug(univention.debug.LISTENER, univention.debug.ERROR, 'PXE: invalid IP address %s' % new['aRecord'][0])
			return
		filename = os.path.join(pxebase, basename)

		pxeconfig = open(pxeconfig_file).read()
		listener.setuid(0)
		try:
			f=open(filename, 'w')
			f.write(pxeconfig)
			f.close()
		finally:
			listener.unsetuid()
