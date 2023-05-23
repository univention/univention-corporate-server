#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: ipchange
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2012-2023 Univention GmbH
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

import ipaddress
from typing import Optional

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
    def change(self, role: str, ip: str, netmask: str, oldip: Optional[str] = None) -> None:
        # ignore link local addresses (no DHCP address received)
        network = ipaddress.IPv4Network(f'{ip}/{netmask}', False)
        if network.is_link_local:
            MODULE.error('Ignore link local address change.')
            return

        ucr.load()
        sso_fqdn = ucr.get('ucs/server/sso/fqdn')

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
        MODULE.info(f'Change IP to {ip}')
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
        if ucr.is_true('ucs/server/sso/autoregistraton', True):
            for fwd_zone in univention.admin.modules.lookup(fwd_mod, None, lo, scope='sub', superordinate=None, filter=None):
                zone = fwd_zone.get('zone')
                if not sso_fqdn.endswith(zone):
                    continue
                sso_name = sso_fqdn[:-(len(zone) + 1)]
                for current_ip in current_ips:
                    for host_rec in univention.admin.modules.lookup(host_mod, None, lo, scope='sub', superordinate=fwd_zone, filter=filter_format('(&(relativeDomainName=%s)(aRecord=%s))', (sso_name, current_ip))):
                        host_rec.open()
                        if oldip in host_rec['a']:
                            host_rec['a'].remove(oldip)
                        host_rec['a'].append(ip)
                        host_rec.modify()
