# SPDX-FileCopyrightText: 2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""UCR module: enable or disable the systemd unit of a Docker app when <app_id>/autostart changes."""

import os
import subprocess


SYSTEMD_UNIT_DIR = '/etc/systemd/system'
SUFFIX = '/autostart'


def handler(configRegistry, changes):
    for key in changes:
        if not key.endswith(SUFFIX):
            continue
        unit = 'docker-app-%s.service' % (key[:-len(SUFFIX)],)
        if not os.path.exists(os.path.join(SYSTEMD_UNIT_DIR, unit)):
            continue
        if configRegistry.is_false(key, False) or configRegistry.get(key, '').lower() == 'manually':
            action = 'disable'
        else:
            action = 'enable'
        subprocess.call(['systemctl', action, '--quiet', unit])
