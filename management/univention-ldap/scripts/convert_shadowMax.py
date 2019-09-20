#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention LDAP
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

import univention.uldap
from univention.config_registry import ConfigRegistry


lo = univention.uldap.getAdminConnection()

baseConfig = ConfigRegistry()
baseConfig.load()

searchResult = lo.search(base=baseConfig['ldap/base'], filter='(&(objectClass=shadowAccount)(shadowLastChange=*)(shadowMax=*))', attr=['shadowLastChange', 'shadowMax'])

for dn, attributes in searchResult:
	ml = []
	if 'shadowLastChange' in attributes and 'shadowMax' in attributes:
		try:
			lastChange = int(attributes['shadowLastChange'][0])
			max = int(attributes['shadowMax'][0])
			if max >= lastChange:
				new_max = max - lastChange
				if new_max == 0:
					ml.append(('shadowMax', attributes['shadowMax'], []))
				else:
					ml.append(('shadowMax', attributes['shadowMax'], [str(new_max)]))
				lo.modify(dn, ml)
		except:
			pass
