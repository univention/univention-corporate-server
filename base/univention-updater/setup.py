#!/usr/bin/python3
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# SPDX-FileCopyrightText: 2024 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import os
import sys

from setuptools import setup


package_version = open("debian/changelog").readline().split()[1][1:-1]
override_version = os.environ.get('PYTHON_PACKAGE_VERSION')

packages = ['univention', 'univention.updater']
if sys.version_info >= (3,):
    packages += ['univention.updater.scripts']

setup(
    packages=packages,
    package_dir={'': 'modules'},
    version=override_version or package_version,
)
