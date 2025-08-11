# SPDX-FileCopyrightText: 2009-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""UCR module to trigger udev on changes in /etc/default/keyboard."""

import shutil
import subprocess


def handler(configRegistry, changes):
    subprocess.call(['udevadm', 'trigger', '--subsystem-match=input', '--action=change'])
    if shutil.which('setupcon'):
        subprocess.call(['setupcon', '--force', '--save'])
