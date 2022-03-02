#!/usr/bin/python3
# SPDX-License-Identifier: AGPL-3.0
# Copyright 2021-2022 Univention GmbH

from setuptools import setup

version = open("debian/changelog", "r").readline().split()[1][1:-1]

setup(
    version=version,
)
