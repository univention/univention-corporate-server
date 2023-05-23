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
        # ignore link local addresses (no DHCP address received)
        network = ipaddress.IPv4Network(f'{ip}/{netmask}', False)
        if network.is_link_local:
            MODULE.error('Ignore link local address change.')
            return

        ucr.load()
        sso_uri = ucr.get('ucs/server/sso/uri').lower()
        sso_fqdn = urlparse(sso_uri).netloc

        lo, position = univention.admin.uldap.getAdminConnection()
        host_mod = univention.admin.modules.get('dns/host_record')
        comp_mod = univention.admin.modules.get(f'computers/{role}')
        fwd_mod = univention.admin.modules.get('dns/forward_zone')
        rev_mod = univention.admin.modules.get('dns/reverse_zone')

        # check if already used
        host_recs = univention.admin.modules.lookup(host_mod, None, lo, scope='sub', filter=filter_format('aRecord=%s', (ip,)))
        used_by = {
            f"{host_rec['name']}.{host_rec.superordinate['zone']}"
            for host_rec in host_recs
            if 'name' in host_rec
        } - {sso_fqdn, "%(hostname)s.%(domainname)s" % ucr}
        if used_by:
            raise BadRequest(f'The IP address is already in use by host record(s) for: {", ".join(used_by)}')

        # do we have a forward zone for this IP address?
        if oldip and oldip != ip:
            for fwd_zone in univention.admin.modules.lookup(fwd_mod, None, lo, scope='sub', superordinate=None, filter=filter_format('(aRecord=%s)', (oldip,))):
                fwd_zone.open()
                fwd_zone['a'].remove(oldip)
                fwd_zone['a'].append(ip)
                fwd_zone.modify()

        # remove old DNS reverse entries with old IP
        server = comp_mod.object(None, lo, position, self.user_dn)
        server.open()
        current_ips = server['ip']
        for zone_ip in server['dnsEntryZoneReverse']:
            if zone_ip[1] in current_ips:
                server['dnsEntryZoneReverse'].remove(zone_ip)

        # change IP
        server['ip'] = ip
        MODULE.info("Change IP to %s", ip)
        server.modify()

        # do we have a new reverse zone for this IP address?
        parts = network.network_address.exploded.split('.')
        while parts[-1] == '0':
            parts.pop()

        while parts:
            subnet = '.'.join(parts)
            parts.pop()
            filterstr = filter_format('(subnet=%s)', (subnet,))
            rev_recs = univention.admin.modules.lookup(rev_mod, None, lo, scope='sub', superordinate=None, filter=filterstr)
            if rev_recs:
                server = comp_mod.object(None, lo, position, self.user_dn)
                server.open()
                server['dnsEntryZoneReverse'].append([rev_recs[0].dn, ip])
                server.modify()
                break

        # Change ucs-sso entry
        # FIXME: this should be done for UCS-in-AD domains as well!
        if ucr.is_true('keycloak/server/sso/autoregistraton', True) and sso_fqdn:
            for fwd_zone in univention.admin.modules.lookup(fwd_mod, None, lo, scope='sub', superordinate=None, filter=None):
                zone = fwd_zone.get('zone')
                # check case insenstive. Mostly necessary for keycloak
                if not sso_fqdn.endswith(zone.lower()):
                    continue
                sso_name = sso_fqdn[:-(len(zone) + 1)]
                for current_ip in current_ips:
                    for host_rec in univention.admin.modules.lookup(host_mod, None, lo, scope='sub', superordinate=fwd_zone, filter=filter_format('(&(relativeDomainName=%s)(aRecord=%s))', (sso_name, current_ip))):
                        host_rec.open()
                        if oldip in host_rec['a']:
                            host_rec['a'].remove(oldip)
                        host_rec['a'].append(ip)
                        host_rec.modify()
