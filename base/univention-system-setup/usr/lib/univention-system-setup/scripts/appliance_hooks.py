#!/usr/bin/python3
#
# Univention System Setup
# appliance hook script called at the end of appliance wizard setup
#
# SPDX-FileCopyrightText: 2016-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import os.path
import shutil
import sys
from tempfile import mkdtemp

from univention.management.console.modules.setup import util


PATH_APPLIANCE_HOOKS = '/usr/lib/univention-system-setup/appliance-hooks.d/'


def appliance_hooks() -> None:
    temp_dir = os.path.join(mkdtemp(), 'pre')
    shutil.copytree(PATH_APPLIANCE_HOOKS, temp_dir)
    util.run_scripts_in_path(temp_dir, sys.stdout, "appliance hook")
    shutil.rmtree(temp_dir)
    sys.exit(0)


if __name__ == "__main__":
    appliance_hooks()
