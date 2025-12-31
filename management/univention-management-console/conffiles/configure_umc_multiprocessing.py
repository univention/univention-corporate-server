#!/usr/bin/python3
#
# Univention Management Console
# Univention Configuration Registry Module to create systemd services for multiprocessing
#
# SPDX-FileCopyrightText: 2020-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import os
import subprocess


def handler(ucr, changes):
    processes = ucr.get_int('umc/http/processes', 1)
    if processes == 0:
        processes = os.cpu_count()

    start_port = 18200
    try:
        start_port = int(ucr.get('umc/http/processes/start-port', start_port))
    except ValueError:
        pass

    systemd_target_dir = '/etc/systemd/system/univention-management-console-server-multiprocessing.target.wants/'

    if os.path.isdir(systemd_target_dir):
        for service in os.listdir(systemd_target_dir):
            subprocess.call(['systemctl', 'disable', service])

    if processes > 1:
        for i in range(processes):
            subprocess.call(['systemctl', 'enable', f'univention-management-console-server@{i + start_port}'])
