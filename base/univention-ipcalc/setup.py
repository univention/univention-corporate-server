#!/usr/bin/python3
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# SPDX-License-Identifier: AGPL-3.0-only
# Copyright 2021-2024 Univention GmbH

from setuptools import setup


version = open("debian/changelog").readline().split()[1][1:-1]

setup(
    version=version,
)
