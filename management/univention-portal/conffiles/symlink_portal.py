#!/usr/bin/python3
#
# Univention Portal
#
# SPDX-FileCopyrightText: 2021-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import os
import os.path
from errno import EEXIST


portal_path = "/usr/share/univention-portal"


def handler(config_registry, changes):
    old, new = changes['portal/paths']
    old = [o.strip() for o in old.split(",")] if old else []
    new = [n.strip() for n in new.split(",")] if new else []
    for path in old:
        if path in new:
            continue
        path = os.path.normpath("/var/www" + path)
        if not os.path.islink(path) or os.path.realpath(path) != portal_path:
            print(f"{path} does not link to the portal contents. Skipping...")
        else:
            print(f"Removing portal link to {path}...")
            os.unlink(path)
    for path in new:
        if path in old:
            continue
        path = os.path.normpath("/var/www" + path)
        if os.path.islink(path):
            link_target = os.path.realpath(path)
            print(f"{path} already links (to {link_target}). Skipping...")
        else:
            print(f"Linking {path} to portal content...")
            try:
                dirname = os.path.dirname(path)
                try:
                    os.makedirs(dirname)
                except OSError as exc:
                    if exc.errno != EEXIST:
                        raise
            except OSError as exc:
                print(f"Error creating {dirname}: {exc}!")
            else:
                try:
                    os.symlink(portal_path, path)
                except OSError as exc:
                    print(f"Error creating a link from {path} to {portal_path}: {exc}!")
