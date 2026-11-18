#!/usr/bin/python3
# SPDX-FileCopyrightText: 2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""Print APT sources in the one-line format: DEB822 `*.sources` files are expanded, comments are kept."""

import io
from sys import argv

from univention.updater.sources import iter_entries


for fn in argv[1:]:
    try:
        with open(fn) as fd:
            text = fd.read()
    except FileNotFoundError:
        continue
    if not fn.endswith('.sources'):
        print(text, end='')
        continue
    for line in text.splitlines():
        if line.startswith('#'):
            print(line)
    for entry in iter_entries(io.StringIO(text)):
        for line in entry.lines():
            print(line)
