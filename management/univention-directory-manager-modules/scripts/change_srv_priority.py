#!/usr/bin/python3
#
# Copyright 2011-2022 Univention GmbH
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
This tool changes the priority from some SRV records from 0 to 100
'''

import univention.admin
import univention.admin.uldap
import univention.admin.modules
import univention.admin.handlers.dns.forward_zone
import univention.admin.handlers.dns.srv_record
import univention.config_registry

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


def main():
	# type: () -> None
	univention.admin.modules.update()

	configRegistry = univention.config_registry.ConfigRegistry()
	configRegistry.load()

	lo, position = univention.admin.uldap.getAdminConnection()
	forward_module = univention.admin.modules.get('dns/forward_zone')
	forward_zones = univention.admin.modules.lookup(forward_module, None, lo, scope='sub', superordinate=None, base=configRegistry.get('ldap_base'))

	srv_module = univention.admin.modules.get('dns/srv_record')
	for forward_zone in forward_zones:
		srv_records = univention.admin.modules.lookup(srv_module, None, lo, scope='sub', superordinate=forward_zone, base=configRegistry.get('ldap_base'))

		for srv_record in srv_records:
			name = srv_record.get('name')
			modify = False
			if name in SRV_RECORDS:
				for location in srv_record['location']:
					if len(location) > 1 and location[1] == PRIORITY_OLD:
						location[1] = PRIORITY_NEW
						modify = True

				if modify:
					# make SRV records uniq
					srv_record['location'] = list(set(srv_record['location']))

					# Change the objects
					print('Modify: %s' % srv_record.dn)
					srv_record.modify()


if __name__ == "__main__":
	main()
