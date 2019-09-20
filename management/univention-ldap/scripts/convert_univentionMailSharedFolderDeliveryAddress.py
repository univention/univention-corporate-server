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

import sys
import optparse
import univention.uldap
import univention.config_registry


def run():
	lo = univention.uldap.getAdminConnection()

	ucr = univention.config_registry.ConfigRegistry()
	ucr.load()

	searchResult = lo.search(base=ucr.get('ldap/base'), filter='(&(objectClass=univentionMailSharedFolder)(univentionMailSharedFolderDeliveryAddress=*))', attr=['univentionMailSharedFolderDeliveryAddress'])

	for dn, attr in searchResult:
		ml = []
		oldval = attr['univentionMailSharedFolderDeliveryAddress']
		newval = [x.lower() for x in oldval]
		if oldval != newval:
			ml.append(('univentionMailSharedFolderDeliveryAddress', oldval, newval))
			try:
				print 'Updating %s' % dn
				lo.modify(dn, ml)
			except Exception:
				print >> sys.stderr, 'E: Failed to modify %s' % dn

	print 'done'


usage = '''convert_univentionMailSharedFolderDeliveryAddress.py

This script converts LDAP attribute univentionMailSharedFolderDeliveryAddress of
all shared folder LDAP objects to lower case. This script should be called on
UCS domain controller master only.'''

parser = optparse.OptionParser(usage=usage)
(options, args) = parser.parse_args()
run()
