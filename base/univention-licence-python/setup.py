#!/usr/bin/python3
#
# Univention Debug
#  setup.py
#
# SPDX-FileCopyrightText: 2004-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from email.utils import parseaddr

from debian.changelog import Changelog
from debian.deb822 import Deb822
from setuptools import Extension, setup


dch = Changelog(open('debian/changelog', encoding='utf-8'))
dsc = Deb822(open('debian/control', encoding='utf-8'))
realname, email_address = parseaddr(dsc['Maintainer'])

setup(
    package_dir={'': 'python'},
    description='Univention license validation library',

    ext_modules=[Extension(
        'univention.license', ['python/univention/py_license.c'],
                libraries=['univentionlicense'])],

    url='https://www.univention.de/',
    license='GNU Affero General Public License v3',

    name=dch.package,
    version=dch.version.full_version.split('A~')[0],
    maintainer=realname,
    maintainer_email=email_address,

    test_suite='test',
)
