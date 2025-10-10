#!/usr/bin/python3
# SPDX-FileCopyrightText: 2011-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""This tool changes the priority from some SRV records from 0 to 100"""

import univention.admin.modules
import univention.admin.uldap
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


def main() -> None:
    univention.admin.modules.update()

    configRegistry = univention.config_registry.ConfigRegistry()
    configRegistry.load()

    lo, _position = univention.admin.uldap.getAdminConnection()
    forward_module = univention.admin.modules._get('dns/forward_zone')
    forward_zones = univention.admin.modules.lookup(forward_module, None, lo, scope='sub', superordinate=None, base=configRegistry.get('ldap_base'))

    srv_module = univention.admin.modules._get('dns/srv_record')
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
