#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Copyright 2020 Univention GmbH
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

from univention.unittests import import_module
fstab = import_module('fstab', 'python/', 'univention.lib.fstab')


def test_fstab():
	fs = fstab.File('unittests/fstab')
	assert len(fs.get()) == 3

	f = fs.get()[0]
	assert (f.spec, f.uuid, f.mount_point, f.type, f.options, f.dump, f.passno, f.comment) == ('proc', None, '/proc', 'proc', ['defaults'], 0, 0, '')

	f = fs.get()[1]
	assert (f.spec, f.uuid, f.mount_point, f.type, f.options, f.dump, f.passno, f.comment) == ('/dev/vda1', None, '/boot', 'ext3', ['defaults', 'acl'], 0, 0, '')

	f = fs.get()[2]
	assert (f.spec, f.uuid, f.mount_point, f.type, f.options, f.dump, f.passno, f.comment) == ('/dev/vda2', None, 'none', 'swap', ['sw'], 0, 0, '')

	f = fs.get('ext3', False)[0]
	assert (f.spec, f.uuid, f.mount_point, f.type, f.options, f.dump, f.passno, f.comment) == ('/dev/vda3', None, '/', 'ext3', ['acl', 'errors=remount-ro'], 0, 1, '')
	assert str(f) == '/dev/vda3\t/\text3\tacl,errors=remount-ro\t0\t1\t'
	assert repr(f).startswith('<univention.lib.fstab.Entry')


def test_fstab_find():
	fs = fstab.File('unittests/fstab')
	assert fs.find(options=['sw']).type == 'swap'
	assert not fs.find(type='cifs')
