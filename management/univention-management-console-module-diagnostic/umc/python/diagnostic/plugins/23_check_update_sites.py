#!/usr/bin/python3
# SPDX-FileCopyrightText: 2016-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import socket
from collections.abc import Iterator
from urllib.parse import urlsplit

from univention.config_registry import ucr_live as configRegistry
from univention.lib.i18n import Translation
from univention.management.console.modules.diagnostic import MODULE, Instance, Warning  # noqa: A004


_ = Translation('univention-management-console-module-diagnostic').translate

title = _('Check resolving repository servers')
description = _('No problems were found while resolving update repositories.')
links = [{
    'name': 'sdb',
    'href': _('http://sdb.univention.de/1298'),
    'label': _('Univention Support Database - DNS Server on Directory Node does not resolve external names'),
}]
run_descr = ['Checks resolving repository servers']


def repositories() -> Iterator[str]:
    if configRegistry.is_true('repository/online', True):
        yield configRegistry.get('repository/online/server', 'updates.software-univention.de/')
        yield configRegistry.get('repository/app_center/server', 'appcenter.software-univention.de')


def test_resolve(url: str) -> bool:
    parsed = urlsplit(url if '//' in url else '//' + url)
    MODULE.process("Trying to resolve address of repository server %s" % (parsed.hostname))
    MODULE.process("Similar to running: host %s" % (parsed.hostname))

    try:
        socket.getaddrinfo(parsed.hostname, parsed.scheme)
    except socket.gaierror:
        return False
    return True


def unresolvable_repositories() -> Iterator[str]:
    for repository in repositories():
        if not test_resolve(repository):
            yield repository


def run(_umc_instance: Instance) -> None:
    error_descriptions = [_('The following FQDNs were not resolvable:')]
    unresolvable = list(unresolvable_repositories())
    if unresolvable:
        error_descriptions.extend(unresolvable)
        error_descriptions.append(_('Please see {sdb} for troubleshooting DNS problems.'))
        MODULE.error('\n'.join(error_descriptions))
        raise Warning(description='\n'.join(error_descriptions))


if __name__ == '__main__':
    from univention.management.console.modules.diagnostic import main
    main()
