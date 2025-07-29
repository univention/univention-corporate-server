#!/usr/bin/python3
#
# SPDX-FileCopyrightText: 2020-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from setuptools import setup


setup(
    py_modules=[
        'univention.debhelper',
    ],
    description='Univention helper programs for debian/rules',

    url='https://www.univention.de/',
    license='GNU Affero General Public License v3',

    name='univention-debhelper',
    version='1.0.0',
    maintainer='Univention GmbH',
    maintainer_email='packages@univention.de',
)
