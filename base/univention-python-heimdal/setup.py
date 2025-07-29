#!/usr/bin/python3
#
# Python Heimdal
#  setup description for the Python build
#
# SPDX-FileCopyrightText: 2003-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from email.utils import parseaddr

import pkgconfig
from debian.changelog import Changelog
from debian.deb822 import Deb822
from setuptools import Extension, setup


d = pkgconfig.parse('heimdal-krb5')
dch = Changelog(open('debian/changelog', encoding='utf-8'))
dsc = Deb822(open('debian/control', encoding='utf-8'))
realname, email_address = parseaddr(dsc['Maintainer'])

setup(
    name=dch.package,
    version=dch.version.full_version.split('A~')[0],
    description='Heimdal Kerberos Python bindings',
    maintainer=realname,
    maintainer_email=email_address,
    url='https://www.univention.de/',

    ext_modules=[
        Extension(
                'heimdal',
                ['module.c', 'error.c', 'context.c', 'principal.c',
                 'creds.c', 'ticket.c', 'keytab.c', 'ccache.c',
                 'salt.c', 'enctype.c', 'keyblock.c', 'asn1.c'],
                libraries=['krb5', 'hdb', 'asn1'],
                library_dirs=d['library_dirs'],
                include_dirs=d['include_dirs'],
        ),
    ],

    test_suite='test',
)
