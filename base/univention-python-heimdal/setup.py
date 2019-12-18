#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Python Heimdal
#  setup description for the python distutils
#
# Copyright 2003-2019 Univention GmbH
#
# https://www.univention.de/
#
# All rights reserved.
#
# The source code of this program is made available
# under the terms of the GNU Affero General Public License version 3
# (GNU AGPL V3) as published by the Free Software Foundation.
#
# Binary versions of this program provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention and not subject to the GNU AGPL V3.
#
# In the case you use this program under the terms of the GNU AGPL V3,
# the program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <https://www.gnu.org/licenses/>.

import io
from setuptools import setup, Extension
import pkgconfig
from debian.changelog import Changelog
from debian.deb822 import Deb822
from email.utils import parseaddr

d = pkgconfig.parse('heimdal-krb5')
dch = Changelog(io.open('debian/changelog', 'r', encoding='utf-8'))
dsc = Deb822(io.open('debian/control', 'r', encoding='utf-8'))
realname, email_address = parseaddr(dsc['Maintainer'])

setup(
	name=dch.package,
	version=dch.version.full_version,
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
		)
	],

	test_suite='test',
)
