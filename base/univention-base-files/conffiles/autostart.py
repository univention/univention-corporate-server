# SPDX-FileCopyrightText: 2017-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""UCR module for autostart handling."""

from logging import getLogger
from subprocess import PIPE, Popen

from univention.service_info import ServiceInfo


def ctl(cmd, service):
    log = getLogger(__name__).getChild('cmd')

    cmd = ('systemctl', cmd, service)
    log.debug('Calling %r...', cmd)
    proc = Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE)
    out, err = proc.communicate()
    rv = proc.wait()
    if rv:
        log.error('Failed %d (%s)[%s]', rv, out.decode('UTF-8', 'replace'), err.decode('UTF-8', 'replace'))


def handler(configRegistry, changes):
    log = getLogger(__name__)

    log.debug('Loading service information...')
    si = ServiceInfo()
    for name in si.get_services():
        service = si.get_service(name)
        if not service:
            log.debug('Service not found: %s', name)
            continue

        try:
            var = service['start_type']
            unit = service.get('systemd', '%s.service' % (name,))
        except KeyError:
            log.debug('Incomplete service information: %s', service)
            continue

        if var not in changes:
            log.debug('Not changed: %s', name)
            continue

        if configRegistry.is_false(var, False):
            log.info('Disabling %s...', unit)
            ctl('disable', unit)
            ctl('mask', unit)
        elif configRegistry.get(var, '').lower() == 'manually':
            log.info('Manual %s...', unit)
            ctl('unmask', unit)
            ctl('disable', unit)
        else:
            log.info('Enabling %s...', unit)
            ctl('unmask', unit)
            ctl('enable', unit)
