#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention Debug
#  setup.py
#
# Copyright 2004-2019 Univention GmbH
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
from distutils.core import setup, Extension
from email.utils import parseaddr
from debian.changelog import Changelog
from debian.deb822 import Deb822

dch = Changelog(io.open('debian/changelog', 'r', encoding='utf-8'))  # ³
dsc = Deb822(io.open('debian/control', 'r', encoding='utf-8'))
realname, email_address = parseaddr(dsc['Maintainer'])

setup(
	package_dir={'': 'python'},
	description='Univention debugging and logging library',

	py_modules=['univention.debug', 'univention.debug2'],
	ext_modules=[Extension(
		'univention._debug', ['python/univention/py_debug.c'],
		libraries=['univentiondebug'])],

	url='https://www.univention.de/',
	license='GNU Affero General Public License v3',

	name=dch.package,
	version=dch.version.full_version,
	maintainer=realname,
	maintainer_email=email_address,
)
