#!/usr/bin/python3
#
# SPDX-FileCopyrightText: 2004-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import os

from debian.changelog import Changelog
from setuptools import Extension, setup


dch = Changelog(open('debian/changelog', encoding='utf-8'))


def heimdal_extension():
    import pkgconfig

    d = pkgconfig.parse('heimdal-krb5')
    return Extension(
        'heimdal',
        ['module.c', 'error.c', 'context.c', 'principal.c',
         'creds.c', 'ticket.c', 'keytab.c', 'ccache.c',
         'salt.c', 'enctype.c', 'keyblock.c', 'asn1.c'],
        libraries=['krb5', 'hdb', 'asn1'],
        library_dirs=d['library_dirs'],
        include_dirs=d['include_dirs'],
    )


# Type checkers install the package on hosts without the Heimdal headers.
setup(
    ext_modules=[] if os.environ.get('UNIVENTION_SKIP_EXTENSIONS') else [heimdal_extension()],
    version=dch.version.full_version.split('A~')[0],
)
