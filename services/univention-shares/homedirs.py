# -*- coding: utf-8 -*-
#
# Univention Shares
#  listener script for shares
#
# Copyright (C) 2004-2009 Univention GmbH
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

name='homedirs'
description='create home directories'
filter='(&(objectClass=posixAccount)(objectClass=automount)(automountInformation=*))'
attributes=[]

import listener
import os, re

def handler(dn, new, old):

	# remove empty home directories
	if old.has_key('automountInformation') and (old.get('automountInformation', [''])[0] != new.get('automountInformation', [''])[0]):
		unc = ''
		try:
			flags, unc = re.split(' *', old['automountInformation'][0])
		except ValueError:
			pass
		except KeyError:
			pass
		if unc.count(':') != 1:
			return
		host, path = unc.split(':')

		if host != listener.baseConfig['hostname']+'.'+listener.baseConfig['domainname']:
			return

		listener.setuid(0)
		try:
			try:
				os.rmdir(path)
			except OSError:
				pass
		finally:
			listener.unsetuid()
	
	if new.has_key('automountInformation') and (old.get('automountInformation', [''])[0] != new.get('automountInformation', [''])[0]):
		unc = ''
		try:
			flags, unc = re.split(' *', new['automountInformation'][0])
		except ValueError:
			pass
		except KeyError:
			pass
		if unc.count(':') != 1:
			return
		host, path = unc.split(':')

		if host != listener.baseConfig['hostname']+'.'+listener.baseConfig['domainname']:
			return

		if not os.path.exists(path):
			listener.setuid(0)
			try:
				os.mkdir(path)
				os.chown(path, int(new['uidNumber'][0]), int(new['gidNumber'][0]))
			finally:
				listener.unsetuid()
