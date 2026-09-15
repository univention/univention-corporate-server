#!/usr/bin/python3
#
# Univention Portal
#
# SPDX-FileCopyrightText: 2021-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import os
import os.path


portal_path = "/usr/share/univention-portal"


def handler(config_registry, changes):
    """
    Remove the old document root links under /var/www.

    The portal is served by containers behind apache proxy rules. A real
    directory under /var/www takes precedence over those rules, so apache
    would answer with a 403 autoindex error instead of proxying.
    """
    old, new = changes['portal/paths']
    paths = {path.strip() for value in (old, new) for path in (value or "").split(",") if path.strip()}
    for path in paths:
        path = os.path.normpath("/var/www" + path)
        if os.path.islink(path) and os.path.realpath(path) == portal_path:
            print(f"Removing portal link {path}...")
            os.unlink(path)
