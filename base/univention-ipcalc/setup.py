#!/usr/bin/python3
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# SPDX-License-Identifier: AGPL-3.0
# Copyright 2021-2023 Univention GmbH

from setuptools import setup

from debian.changelog import Changelog


dch = Changelog(open('debian/changelog'))

setup(
    version=dch.version.full_version.split('A~')[0],
)
