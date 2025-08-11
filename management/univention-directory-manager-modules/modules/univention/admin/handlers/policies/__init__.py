#!/usr/bin/python3
# SPDX-FileCopyrightText: 2004-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""import all policy modules"""

import importlib
import os.path


__path__ = __import__('pkgutil').extend_path(__path__, __name__)  # type: ignore

policies = []


def __walk(root, dir, files):
    for file_ in files:
        if file_.endswith('.py') and not file_.startswith('__') and file_ not in ('policy.py', 'base.py'):
            policies.append(importlib.import_module('univention.admin.handlers.policies.%s' % (file_[:-3],)))


path = os.path.abspath(os.path.dirname(__file__))
for w_root, _w_dirs, w_files in os.walk(path):
    __walk(w_root, w_root, w_files)
