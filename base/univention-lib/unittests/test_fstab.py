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

import pytest

from .conftest import import_lib_module

fstab = import_lib_module('fstab')


def test_fstab():
	fs = fstab.File('unittests/fstab')
	assert len(fs.get()) == 5

	f = fs.get()[0]
	assert (f.spec, f.uuid, f.mount_point, f.type, f.options, f.dump, f.passno, f.comment) == ('proc', None, '/proc', 'proc', ['defaults'], 0, 0, '')

	f = fs.get()[1]
	# TODO: The spec gets resolved to a device if the uuid is found in /dev/disk/by-uuid
	assert (f.spec, f.uuid, f.mount_point, f.type, f.options, f.dump, f.passno, f.comment) == ('UUID=testtest-0cbd-4f72-809e-89c4c9af0c3d', 'testtest-0cbd-4f72-809e-89c4c9af0c3d', '/boot', 'ext2', ['defaults', 'acl', 'user_xattr'], 0, 2, '')

	f = fs.get()[2]
	assert (f.spec, f.uuid, f.mount_point, f.type, f.options, f.dump, f.passno, f.comment) == ('/dev/vda1', None, '/var', 'ext3', ['defaults', 'acl', 'user_xattr'], 0, 2, '')

	f = fs.get()[3]
	assert (f.spec, f.uuid, f.mount_point, f.type, f.options, f.dump, f.passno, f.comment) == ('/dev/vda2', None, 'none', 'swap', ['sw'], None, None, '#0\t1\t# foo bar baz')

	f = fs.get()[4]
	assert (f.spec, f.uuid, f.mount_point, f.type, f.options, f.dump, f.passno, f.comment) == ('192.168.0.81:/home', None, '/home', 'nfs', ['defaults', 'timeo=21', 'retrans=9', 'wsize=8192', 'rsize=8192', 'nfsvers=3'], 1, 2, '# LDAP bind')

	f = fs.get('ext3', False)[0]
	assert (f.spec, f.uuid, f.mount_point, f.type, f.options, f.dump, f.passno, f.comment) == ('/dev/vda3', None, '/', 'ext3', ['errors=remount-ro', 'acl', 'user_xattr'], 0, 1, None)
	assert str(f) == '/dev/vda3\t/\text3\terrors=remount-ro,acl,user_xattr\t0\t1'
	assert repr(f) == "univention.lib.fstab.Entry('/dev/vda3', '/', 'ext3', options='errors=remount-ro,acl,user_xattr', freq=0, passno=1)"


def test_fstab_save(mocker):
	content = open('unittests/fstab').read()
	fs = fstab.File('unittests/fstab')
	fd = mocker.Mock()
	fd.__enter__ = mocker.Mock(return_value=fd)
	fd.__exit__ = mocker.Mock(return_value=None)
	mocker.patch.object(fstab, 'open', mocker.Mock(return_value=fd))
	fs.save()
	write_calls = [args[0] for _, args, _ in fd.write.mock_calls]
	assert content == ''.join(write_calls)


def test_fstab_broken():
	with pytest.raises(fstab.InvalidEntry):
		fstab.File('unittests/broken_fstab')


def test_fstab_find():
	fs = fstab.File('unittests/fstab')
	assert fs.find(options=['sw']).type == 'swap'
	assert not fs.find(type='cifs')


def test_fstab_find_line_with_comment():
	fs = fstab.File('unittests/fstab')
	assert fs.find(mount_point='/home').type == 'nfs'
	assert fs.find(mount_point='/home').comment == '# LDAP bind'
	assert fs.find(type='swap').comment == '#0\t1\t# foo bar baz'
