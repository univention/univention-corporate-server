#!/usr/bin/env python3
#
# SPDX-FileCopyrightText: 2019-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from setuptools import setup


VER = open('debian/changelog').readline().split()[1][1:-1].split('A~')[0]

setup(
    package_dir={'': '.'},
    version=VER,
)
