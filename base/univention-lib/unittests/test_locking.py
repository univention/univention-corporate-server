#!/usr/bin/python3
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2020-2022 Univention GmbH
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

import os
import sys
import pytest
import subprocess

from .conftest import import_lib_module

locking = import_lib_module('locking')


@pytest.mark.xfail()
@pytest.mark.parametrize('nonblocking', [True, False])
def test_locking(nonblocking):
	lock = locking.get_lock('foo', nonblocking)
	try:
		assert os.path.exists('/var/run/foo.pid')
		assert int(open('/var/run/foo.pid').read().strip()) == os.getpid()
		assert subprocess.check_output([sys.executable, '-c', "from univention.lib import locking; print(locking.get_lock('foo', %r))" % (nonblocking,)], shell=True) == b'False'
		locking.release_lock(lock)
	finally:
		os.unlink('/var/run/foo.pid')
