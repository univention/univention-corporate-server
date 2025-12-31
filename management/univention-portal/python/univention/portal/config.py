#!/usr/bin/python3
#
# Univention Portal
#
# SPDX-FileCopyrightText: 2020-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only


import json
from glob import glob


_CONF = "/usr/lib/univention-portal/config/*.json"
_DB = {}


def load():
    _DB.clear()
    try:
        for fname in sorted(glob(_CONF)):
            with open(fname) as fd:
                _DB.update(json.load(fd))
    except OSError:
        pass
    else:
        load.never_loaded = False


load.never_loaded = True


def fetch(key):
    if load.never_loaded:
        load()
    return _DB[key]
