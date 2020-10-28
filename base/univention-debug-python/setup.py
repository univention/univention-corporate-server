#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention Debug
#  setup.py
#
# Copyright 2004-2020 Univention GmbH
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

#
# If you get "fatal error: univention/debug.h: No such file or directory", the
# "libunivention-debug-dev" package is not installed. Build and install it:
# cd ../univention-debug
# dpkg-buildpackage -us -uc -b
# dpkg -i ../*.deb
# cd -
#

import os
from distutils.core import setup, Extension
from univention.python_packaging.debian_package import DebianPackage

dp = DebianPackage(os.path.dirname(__file__))

setup(
	package_dir={'': 'modules'},
	py_modules=['univention.debug', 'univention.debug2'],
	ext_modules=[Extension(
		'univention._debug', ['modules/univention/py_debug.c'],
		libraries=['univentiondebug'])],
	**dp.as_setuptools_setup_kwargs()
)
