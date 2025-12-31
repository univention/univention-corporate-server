#!/usr/bin/python3
#
# Univention App Center
#  Setup file for packaging
#
# SPDX-FileCopyrightText: 2019-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
#

from packaging import setup


setup(
    name='univention-appcenter-docker',
    packages=[
        'univention.appcenter',
        'univention.appcenter.actions',
    ],
    package_dir={
        'univention.appcenter': 'python/appcenter-docker',
        'univention.appcenter.actions': 'python/appcenter-docker/actions',
    },
)
