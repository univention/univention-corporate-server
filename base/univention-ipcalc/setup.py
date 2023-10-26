#!/usr/bin/python3
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# SPDX-License-Identifier: AGPL-3.0-only
# Copyright 2021-2024 Univention GmbH
import os

from setuptools import setup


package_version = open("debian/changelog").readline().split()[1][1:-1]
override_version = os.environ.get('PYTHON_PACKAGE_VERSION')

setup(
    version=override_version or package_version,
)
