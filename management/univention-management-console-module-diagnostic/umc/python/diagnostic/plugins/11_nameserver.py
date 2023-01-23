#!/usr/bin/python3
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2016-2023 Univention GmbH
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

import dns.resolver
from dns.exception import DNSException, Timeout

from univention.config_registry import ucr_live as ucr
from univention.lib.i18n import Translation
from univention.management.console.modules.diagnostic import MODULE, Instance, Warning


_ = Translation('univention-management-console-module-diagnostic').translate

title = _('Nameserver(s) are not responsive')
description = '\n'.join([
    _('%d of the configured nameservers are not responding to DNS queries.'),
    _('Please make sure the DNS settings in the {setup:network} are correctly set up.'),
    _('If the problem persists make sure the nameserver is connected to the network and the forwarders are able to reach the internet (www.univention.de).'),

])
umc_modules = [{
    'module': 'setup',
    'flavor': 'network',
}]
run_descr = ['Checks if all nameservers are responsive']


def run(_umc_instance: Instance) -> None:
    failed = []
    fqdn = "%(hostname)s.%(domainname)s" % ucr
    hostnames = {
        'www.univention.de': ('dns/forwarder1', 'dns/forwarder2', 'dns/forwarder3'),
        fqdn: ('nameserver1', 'nameserver2', 'nameserver3'),
    }
    for hostname, nameservers in hostnames.items():
        for nameserver in nameservers:
            if not ucr.get(nameserver):
                continue

            MODULE.process("Trying %s to resolve %s" % (ucr[nameserver], hostname))
            MODULE.process("Similar to running: dig +short %s @%s" % (hostname, ucr[nameserver]))
            try:
                query_dns_server(ucr[nameserver], hostname)
            except DNSException as exc:
                msgs = ['\n', _('The nameserver %(nameserver)s (UCR variable %(var)r) is not responsive:') % {'nameserver': ucr[nameserver], 'var': nameserver}]

                if isinstance(exc, Timeout):
                    msgs.append(_('A timeout occurred while reaching the nameserver (is it online?).'))
                else:
                    msgs.append('%s' % (exc,))
                failed.append('\n'.join(msgs))

    if failed:
        MODULE.error('%s%s' % (description % (len(failed),), '\n'.join(failed)))
        raise Warning('%s%s' % (description % (len(failed),), '\n'.join(failed)))


def query_dns_server(nameserver: str, hostname: str) -> None:
    resolver = dns.resolver.Resolver()
    resolver.lifetime = 10
    resolver.nameservers = [nameserver]

    # perform a reverse lookup
    try:
        resolver.query(hostname)
    except dns.resolver.NXDOMAIN:
        # it's not a problem
        pass


if __name__ == '__main__':
    from univention.management.console.modules.diagnostic import main
    main()
