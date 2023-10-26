#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2022-2024 Univention GmbH
import os

from setuptools import setup


package_version = open("debian/changelog").readline().split()[1][1:-1]
override_version = os.environ.get('PYTHON_PACKAGE_VERSION')

setup(
    version=override_version or package_version,
)
