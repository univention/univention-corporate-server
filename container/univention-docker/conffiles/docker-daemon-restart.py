#!/usr/bin/python3
#
# SPDX-FileCopyrightText: 2022-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import subprocess


def postinst(configRegistry, changes):
    subprocess.call(['systemctl', 'daemon-reload'])
    subprocess.call(['systemctl', 'restart', 'docker'])
