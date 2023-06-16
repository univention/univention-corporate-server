#!/usr/bin/python3
# SPDX-FileCopyrightText: 2004-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from email.utils import parseaddr

from debian.changelog import Changelog
from debian.deb822 import Deb822
from setuptools import setup


dch = Changelog(open('debian/changelog', encoding='utf-8'))
dsc = Deb822(open('debian/control', encoding='utf-8'))
realname, email_address = parseaddr(dsc['Maintainer'])

setup(
    description='Univention Directory Listener',
    url='https://www.univention.de/',
    license='GNU Affero General Public License v3',

    packages=['', 'univention.listener'],
    package_dir={'': 'python'},

    name=dch.package,
    version=dch.version.full_version.split('A~')[0],
    maintainer=realname,
    maintainer_email=email_address,

    entry_points={
        "console_scripts": [
            "get_notifier_id.py = univention.listener.get_notifier_id:main",
            "resync-objects.py = univention.listener.resync:main",
            "univention-get-ldif-from-master = univention.listener.get_ldif:main",
        ],
    },
)
