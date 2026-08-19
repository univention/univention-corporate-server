#!/usr/bin/python3
#
# Univention Management Console
#  module: ipchange
#
# SPDX-FileCopyrightText: 2012-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import ipaddress
from urllib.parse import urlparse

from ldap.filter import filter_format

import univention.admin.modules
import univention.admin.uldap
from univention.management.console.base import Base
from univention.management.console.config import ucr
from univention.management.console.error import BadRequest
from univention.management.console.log import MODULE
from univention.management.console.modules.decorators import simple_response


univention.admin.modules.update()


class Instance(Base):

    @simple_response
    def change(self, role: str, ip: str, netmask: str, oldip: str | None = None) -> None:
        try:
            network = ipaddress.ip_network(f'{ip}/{netmask}', False)
            old_ip = ipaddress.ip_address(oldip) if oldip else None
            old_address = old_ip.exploded if old_ip else None

            new_ip = ipaddress.ip_address(ip)
            new_address = new_ip.exploded
        except ValueError as exc:
            raise BadRequest(f'The IP address is invalid: {exc}')

        if old_ip is not None and old_ip.version != new_ip.version:
            raise BadRequest('The old and new IP addresses use different address families.')

        # ignore link local or loopback addresses (no DHCP address received)
        if new_ip.is_link_local or new_ip.is_loopback:
            MODULE.error('Ignore link local or loopback address change.')
            return

        # set attribute aRecord(<split>.|<trim>0) or aAAARecord(<split>:|<trim>0000) for IP version 4 or 6
        if network.version == 4:
            attribute = 'aRecord'
            ip_delimiter = '.'
            ip_trim = '0'
        elif network.version == 6:
            attribute = 'aAAARecord'
            ip_delimiter = ':'
            ip_trim = '0000'

        lo, position = univention.admin.uldap.getAdminConnection()
        host_mod = univention.admin.modules.get('dns/host_record')
        comp_mod = univention.admin.modules.get(f'computers/{role}')
        fwd_mod = univention.admin.modules.get('dns/forward_zone')
        rev_mod = univention.admin.modules.get('dns/reverse_zone')

        server = comp_mod.object(None, lo, position, self.user_dn)
        server.open()

        current_ips = set(server['ip'])

        if new_address in current_ips and (not oldip or old_address == new_address):
            return

        # get the current server status filtered by IP version
        source_addresses = {
            entry for entry in server['ip']
            if ipaddress.ip_address(entry).version == network.version
        }
        if oldip:
            source_addresses |= {old_address, oldip}

        ucr.load()
        server_domain = server.get('domain', '').lower()
        fqdn = server.get('fqdn', '').lower()
        fqdns = {fqdn}

        sso_fqdn = urlparse(ucr.get('ucs/server/sso/uri', '').lower()).hostname
        if ucr.is_true('keycloak/server/sso/autoregistraton', True) and sso_fqdn:
            fqdns.add(sso_fqdn)

        if ucr.get('dns/backend') == 'samba4':
            # FIXED? Works, but it isn't stable!
            # (Sometimes the S4 connector resyncs old adresses. Do we have to wait for a replication?)
            fqdns |= {f'{host}.{server_domain}' for host in ['gc._msdcs', 'DomainDnsZones', 'ForestDnsZones']}

        fqdns.discard('')
        fqdns.discard(None)

        # check if already used by host record
        # FIXME: what about further A records for this server, which are just manually added by customers?
        # TODO: replace the check by a search for computers/computer ip={new_address} ?
        host_recs = univention.admin.modules.lookup(host_mod, None, lo, scope='sub', filter=filter_format('(|(%s=%s)(%s=%s))', (attribute, new_address, attribute, ip)))
        used_by = {
            f"{host_rec['name']}.{host_rec.superordinate['zone']}".lower()
            for host_rec in host_recs
            if 'name' in host_rec
        } - {managed_fqdn.lower() for managed_fqdn in fqdns}
        if used_by:
            raise BadRequest(f'The IP address is already in use by host record(s) for: {", ".join(used_by)}')

        # do we have a forward zone for the IP addresses?
        for address in source_addresses:
            for fwd_zone in univention.admin.modules.lookup(fwd_mod, None, lo, scope='sub', filter=filter_format('(%s=%s)', (attribute, address))):
                fwd_zone.open()
                if address in fwd_zone['a']:
                    fwd_zone['a'].remove(address)
                if new_address not in fwd_zone['a']:
                    fwd_zone['a'].append(new_address)
                fwd_zone.modify()

        # add the new A records for all known DNS names
        # this must be done before modifying the server, as that would cleanup the old IP addresses and we wouldn't find any records anymore
        # FIXME: this should be done for UCS-in-AD domains as well!
        for fwd_zone in univention.admin.modules.lookup(fwd_mod, None, lo, scope='sub'):
            zone = fwd_zone.get('zone')
            for host_fqdns in fqdns:
                # check case insensitive. Mostly necessary for Keycloak
                if not host_fqdns.lower().endswith('.' + zone.lower()):
                    continue
                name = host_fqdns[:-(len(zone) + 1)]
                for host_rec in univention.admin.modules.lookup(host_mod, None, lo, scope='sub', superordinate=fwd_zone, filter=filter_format('(&(relativeDomainName=%s))', (name,))):
                    host_rec.open()
                    if set(host_rec['a']) & current_ips:
                        host_rec['a'] = [
                            address
                            for address in host_rec['a']
                            if address not in source_addresses
                        ]
                        if new_address not in host_rec['a']:
                            host_rec['a'].append(new_address)
                        host_rec.modify()

        server = comp_mod.object(None, lo, position, self.user_dn)
        server.open()

        # change/append server address and cleanup any old ip addresses
        server['ip'] = list(current_ips - source_addresses | {new_address})
        # TODO: from security perspective we should only do:
        # server['ip'] = list(set(server['ip']) | {new_address})

        # remove old DNS reverse entries with current IP address(es)
        for zone_ip in server['dnsEntryZoneReverse']:
            if zone_ip[1] in source_addresses:
                server['dnsEntryZoneReverse'].remove(zone_ip)

        # do we have a new reverse zone for this IP address?
        parts = network.network_address.exploded.split(ip_delimiter)
        while parts[-1] == ip_trim:
            parts.pop()

        while parts:
            subnet = ip_delimiter.join(parts)
            rev_recs = univention.admin.modules.lookup(rev_mod, None, lo, scope='sub', filter=filter_format('(subnet=%s)', (subnet,)))
            if rev_recs:
                entry = [rev_recs[0].dn, new_address]
                if entry not in server['dnsEntryZoneReverse']:
                    server['dnsEntryZoneReverse'].append(entry)
                break
            parts.pop()

        # add IP address to new A record in forward zone
        parts = fqdn.split('.')
        while len(parts) > 1:
            zone_name = '.'.join(parts)
            zones = univention.admin.modules.lookup(fwd_mod, None, lo, scope='sub', filter=filter_format('(zone=%s)', (zone_name,)))
            if zones:
                entry = [zones[0].dn, new_address]
                if entry not in server['dnsEntryZoneForward']:
                    server['dnsEntryZoneForward'].append(entry)
                break
            parts.pop(0)

        MODULE.process('Change IP address %s for %s', ip, fqdn)
        server.modify()
