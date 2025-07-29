#!/usr/bin/python3
#
# Univention System Setup
# cleanup script called after the appliance wizard setup
#
# SPDX-FileCopyrightText: 2011-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import os.path
import shutil
import sys
from tempfile import mkdtemp

from univention.management.console.modules.setup import util


PATH_CLEANUP_PRE_SCRIPTS = '/usr/lib/univention-system-setup/cleanup-pre.d/'
PATH_CLEANUP_POST_SCRIPTS = '/usr/lib/univention-system-setup/cleanup-post.d/'


def cleanup() -> None:
    temp_dir = mkdtemp()

    pre_dir = os.path.join(temp_dir, 'pre')
    post_dir = os.path.join(temp_dir, 'post')

    shutil.copytree(PATH_CLEANUP_PRE_SCRIPTS, pre_dir)
    shutil.copytree(PATH_CLEANUP_POST_SCRIPTS, post_dir)

    # Run cleanup-pre scripts
    util.run_scripts_in_path(pre_dir, sys.stdout, "cleanup-pre")

    # Run cleanup-post scripts
    util.run_scripts_in_path(post_dir, sys.stdout, "cleanup-post")

    shutil.rmtree(temp_dir)

    sys.exit(0)


if __name__ == "__main__":
    cleanup()
