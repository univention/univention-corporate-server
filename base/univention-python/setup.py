#!/usr/bin/python3
#
# SPDX-FileCopyrightText: 2004-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from debian.changelog import Changelog
from setuptools import setup


dch = Changelog(open('debian/changelog', encoding='utf-8'))

setup(version=dch.version.full_version.split('A~')[0])
