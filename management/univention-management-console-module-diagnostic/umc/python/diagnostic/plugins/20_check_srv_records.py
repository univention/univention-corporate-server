#!/usr/bin/python3
# SPDX-FileCopyrightText: 2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from collections.abc import Iterator
from typing import Any

import dns.exception
import dns.resolver

import univention.admin.modules as udm_modules
import univention.admin.uldap
from univention.admin.handlers import simpleLdap
from univention.lib.i18n import Translation
from univention.management.console.log import MODULE
from univention.management.console.modules.diagnostic import Instance, Warning  # noqa: A004


_ = Translation('univention-management-console-module-diagnostic').translate

title = _('Check target entries in DNS SRV records')
description = [_('All checked SRV record entries are ok.')]
run_descr = [_('Checks target entries in DNS SRV records')]


class DNSReferenceChecker:
    def __init__(self) -> None:
        self.checked_hosts: dict[str, bool] = {}
        univention.admin.modules.update()
        (self.ldap_connection, self.position) = univention.admin.uldap.getMachineConnection()

    def lookup(self, module_name: str, filter_expression: str = '') -> Iterator[simpleLdap]:
        module = udm_modules.get(module_name)
        for instance in module.lookup(None, self.ldap_connection, filter_expression):
            instance.open()
            yield instance

    def find_all_srv_record_problems(self) -> Any:
        for record in self.lookup('dns/srv_record'):
            for prio, weight, port, target in record['location']:
                if target not in self.checked_hosts:
                    self.checked_hosts[target] = self.is_valid_target(target)
                if not self.checked_hosts[target]:
                    MODULE.process('SRV record %s does not contain a valid target (must be A/AAAA): %s', record.dn, target)
                    yield record.oldattr['relativeDomainName'][0].decode(), target, self.umc_link(record.dn)

    def is_valid_target(self, target: str) -> bool:
        """
        Checks if the given target ends with a dot and is a resolvable
        A or AAAA record. A CNAME is not allowed.
        """
        if not target.endswith('.'):
            return False
        target = target.strip(' .')
        try:
            dns.resolver.resolve(target, 'A')
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
            try:
                dns.resolver.resolve(target, 'AAAA')
            except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
                return False
        return True

    def umc_link(self, dn: str) -> tuple[str, dict[str, Any]]:
        text = 'udm:dns/dns'
        link = {
            'module': 'udm',
            'flavor': 'dns/dns',
            'props': {
                'openObject': {
                    'objectDN': dn,
                    'objectType': 'dns/srv_record',
                },
            },
        }
        return text, link


def run(_umc_instance: Instance) -> None:
    errortext = [
        ' '.join(
            [
                _('Found invalid target entries in the following SRV records.'),
                _('Please make sure that only A or AAAA records are present and the given FQDN has to end with a dot.'),
            ],
        ),
    ]
    modules = []
    text_tmpl = _('In SRV record {name} is an invalid target "{target}" (see {{{link}}}):')

    ref_checker = DNSReferenceChecker()
    for record_name, target, umc_link in ref_checker.find_all_srv_record_problems():
        (text, link) = umc_link
        errortext.append('')
        errortext.append(text_tmpl.format(name=record_name, target=target, link=text))
        modules.append(link)

    if modules:
        raise Warning(description='\n'.join(errortext), umc_modules=modules)


if __name__ == '__main__':
    run(None)
