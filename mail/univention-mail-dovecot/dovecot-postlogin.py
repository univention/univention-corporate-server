#!/usr/bin/env python3

# Univention Mail Dovecot
# postlogin script to supply user groups information to dovecot
#
# SPDX-FileCopyrightText: 2015-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import grp
import os
import sys


if "SYSTEM_GROUPS_USER" in os.environ:
    user = os.environ["SYSTEM_GROUPS_USER"]
    groups = (g.gr_name for g in grp.getgrall() if user in g.gr_mem)

    os.environ["ACL_GROUPS"] = ",".join(groups)
    try:
        os.environ["USERDB_KEYS"] += " acl_groups"
    except KeyError:
        os.environ["USERDB_KEYS"] = "acl_groups"

os.execv(sys.argv[1], sys.argv[1:])  # noqa: S606
