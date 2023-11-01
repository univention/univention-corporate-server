#!/usr/bin/python3
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# SPDX-FileCopyrightText: 2024 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from setuptools import setup


version = open("debian/changelog").readline().split()[1][1:-1].split('A~')[0]

packages = ['univention', 'univention.updater', 'univention.updater.scripts']

setup(
    packages=packages,
    package_dir={'': 'modules'},
    version=version,
)
