#!/usr/bin/python3
#
# SPDX-FileCopyrightText: 2004-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import os

from setuptools import Extension, setup


# Type checkers install the Python modules on hosts without libunivention-debug.
ext_modules = [] if os.environ.get('UNIVENTION_SKIP_EXTENSIONS') else [
    Extension('univention._debug', ['python/univention/py_debug.c'], libraries=['univentiondebug']),
]

setup(
    package_dir={'': 'python'},
    py_modules=['univention.debug', 'univention.debug2', 'univention.logging'],
    ext_modules=ext_modules,
)
