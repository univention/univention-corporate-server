#!/usr/bin/python3
#
# Univention Management Console
#  module: ipchange
#
# SPDX-FileCopyrightText: 2012-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import ipaddress
from urllib.parse import urlparse

from ldap.filter import filter_format

import univention.admin.modules
import univention.admin.uldap
import univention.config_registry
from univention.management.console.base import Base
from univention.management.console.config import ucr
from univention.management.console.error import BadRequest
from univention.management.console.log import MODULE
from univention.management.console.modules.decorators import simple_response


univention.admin.modules.update()


class Instance(Base):

    @simple_response
    def change(self, role: str, ip: str, netmask: str, oldip: str | None = None) -> dict:
        """
        Return a dict with all necessary values for ipchange read from the current
        status of the system.
        """
        # ignore link local addresses (no DHCP address received)
        network = ipaddress.IPv4Network(f'{ip}/{netmask}', False)
        if network.is_link_local:
            MODULE.error('Ignore link local address change.')
            return

        lo, position = univention.admin.uldap.getAdminConnection()
        hmodule = univention.admin.modules.get('dns/host_record')
        cmodule = univention.admin.modules.get(f'computers/{role}')

        # check if already used
        res = univention.admin.modules.lookup(hmodule, None, lo, scope='sub', filter=filter_format('aRecord=%s', (ip,)))
        used_by = [entry['name'] for entry in res if 'name' in entry]
        if used_by:
            raise BadRequest(f'The IP address is already in use by host record(s) for: {", ".join(used_by)}')

        # do we have a forward zone for this IP address?
        if oldip and oldip != ip:
            fmodule = univention.admin.modules.get('dns/forward_zone')
            for forwardobject in univention.admin.modules.lookup(fmodule, None, lo, scope='sub', superordinate=None, filter=filter_format('(aRecord=%s)', (oldip,))):
                forwardobject.open()
                forwardobject['a'].remove(oldip)
                forwardobject['a'].append(ip)
                forwardobject.modify()

        # remove old DNS reverse entries with old IP
        server = cmodule.object(None, lo, position, self.user_dn)
        server.open()
        current_ips = server['ip']
        for entry in server['dnsEntryZoneReverse']:
            if entry[1] in current_ips:
                server['dnsEntryZoneReverse'].remove(entry)

        # change IP
        server['ip'] = ip
        MODULE.info("Change IP to %s", ip)
        server.modify()

        # do we have a new reverse zone for this IP address?
        rmodule = univention.admin.modules.get('dns/reverse_zone')
        parts = network.network_address.exploded.split('.')
        while parts[-1] == '0':
            parts.pop()

        while parts:
            subnet = '.'.join(parts)
            parts.pop()
            filter = filter_format('(subnet=%s)', (subnet,))
            reverseobject = univention.admin.modules.lookup(rmodule, None, lo, scope='sub', superordinate=None, filter=filter)
            if reverseobject:
                server = cmodule.object(None, lo, position, self.user_dn)
                server.open()
                server['dnsEntryZoneReverse'].append([reverseobject[0].dn, ip])
                server.modify()
                break

        # Change ucs-sso entry
        # FIXME: this should be done for UCS-in-AD domains as well!
        ucr.load()
        sso_uri = ucr.get('ucs/server/sso/uri').lower()
        sso_fqdn = urlparse(sso_uri).netloc
        if ucr.is_true('keycloak/server/sso/autoregistraton', True) and sso_fqdn:
            fmodule = univention.admin.modules.get('dns/forward_zone')
            forwardobjects = univention.admin.modules.lookup(fmodule, None, lo, scope='sub', superordinate=None, filter=None)
            for forwardobject in forwardobjects:
                zone = forwardobject.get('zone')
                # check case insenstive. Mostly necessary for keycloak
                if not sso_fqdn.endswith(zone.lower()):
                    continue
                sso_name = sso_fqdn[:-(len(zone) + 1)]
                for current_ip in current_ips:
                    records = univention.admin.modules.lookup(hmodule, None, lo, scope='sub', superordinate=forwardobject, filter=filter_format('(&(relativeDomainName=%s)(aRecord=%s))', (sso_name, current_ip)))
                    for record in records:
                        record.open()
                        if oldip in record['a']:
                            record['a'].remove(oldip)
                        record['a'].append(ip)
                        record.modify()
