#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention LDAP
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

import univention.uldap
import univention_baseconfig


lo = univention.uldap.getAdminConnection()

baseConfig = univention_baseconfig.baseConfig()
baseConfig.load()

searchResult = lo.search( base = baseConfig['ldap/base'], filter = '(&(objectClass=shadowAccount)(shadowLastChange=*)(shadowMax=*))', attr = ['shadowLastChange', 'shadowMax'] )

for dn,attributes in searchResult:
	ml = []
	if attributes.has_key('shadowLastChange') and attributes.has_key('shadowMax'):
		try:
			lastChange = int(attributes['shadowLastChange'][0])
			max = int(attributes['shadowMax'][0])
			if max >= lastChange:
				new_max = max - lastChange
				if new_max == 0:
					ml.append( ('shadowMax', attributes['shadowMax'], []) )
				else:
					ml.append( ('shadowMax', attributes['shadowMax'], [str(new_max)]) )
				lo.modify( dn, ml )
		except:
			pass
			
