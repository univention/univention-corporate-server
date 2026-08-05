#!/usr/bin/python3
# SPDX-FileCopyrightText: 2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import subprocess
from pathlib import Path


def test_app_install_frontend():
    test_file = Path(__file__).parent / 'js' / 'test_app_install_frontend.js'
    subprocess.run(['node', str(test_file)], check=True, timeout=30)
