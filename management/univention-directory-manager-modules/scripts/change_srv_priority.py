#!/usr/bin/python2.7
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

'''
Univention Directory Manager Tools
This tool changes the priority from some SRV records from 0 to 100
'''

import univention.admin
import univention.admin.uldap
import univention.admin.modules
import univention.admin.handlers.dns.forward_zone
import univention.admin.handlers.dns.srv_record
import univention.config_registry

univention.admin.modules.update()

configRegistry = univention.config_registry.ConfigRegistry()
configRegistry.load()

PRIORITY_NEW = '100'
PRIORITY_OLD = '0'

SRV_RECORDS = [
	['ldap', 'tcp'],
	['kerberos', 'tcp'],
	['kerberos', 'udp'],
	['kerberos-adm', 'tcp'],
	['kpasswd', 'tcp'],
	['kpasswd', 'udp'],
]


lo, position = univention.admin.uldap.getAdminConnection()
co = None
forward_module = univention.admin.modules.get('dns/forward_zone')
forward_zones = univention.admin.modules.lookup(forward_module, co, lo, scope='sub', superordinate=None, base=configRegistry.get('ldap_base'), filter=None)

srv_module = univention.admin.modules.get('dns/srv_record')
for forward_zone in forward_zones:
	srv_records = univention.admin.modules.lookup(srv_module, co, lo, scope='sub', superordinate=forward_zone, base=configRegistry.get('ldap_base'), filter=None)

	for srv_record in srv_records:
		name = srv_record.get('name')
		modify = False
		if name in SRV_RECORDS:
			for i in range(len(srv_record['location'])):
				if len(srv_record['location'][i]) > 0 and srv_record['location'][i][1] == PRIORITY_OLD:
					srv_record['location'][i][1] = PRIORITY_NEW
					modify = True
			if modify:

				# make SRV records uniq
				location = []
				for i in range(len(srv_record['location'])):
					if srv_record['location'][i] not in location:
						location.append(srv_record['location'][i])

				srv_record['location'] = location

				# Change the objects
				print 'Modify: %s' % srv_record.dn
				srv_record.modify()
