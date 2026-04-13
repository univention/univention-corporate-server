#!/usr/bin/python3
#
# Univention Debug
#  setup.py
#
# SPDX-FileCopyrightText: 2004-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from setuptools import Extension, setup

setup(
    package_dir={'': 'python'},
    description='Univention debugging and logging library',

    py_modules=['univention.debug', 'univention.debug2', 'univention.logging'],
    ext_modules=[Extension(
        'univention._debug', ['python/univention/py_debug.c'],
        libraries=['univentiondebug'])],

    url='https://www.univention.de/',
    license='GNU Affero General Public License v3',

    name="univention-debug-python",
    version="14.5.0",
    # maintainer=realname,
    # maintainer_email=email_address,
)
