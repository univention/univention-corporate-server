#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2020-2023 Univention GmbH
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


import pytest

from univention.management.console.modules.appcenter.util import create_url


@pytest.mark.parametrize(
    'server,prefix,username,password,port,expected',
    [
        ('updates.knut.univention.de', 'the/prefix', 'the_user', 'the_password', '80', 'http://the_user:the_password@updates.knut.univention.de/the/prefix'),
        ('updates.knut.univention.de', 'the/prefix', 'the_user', 'the_password', '443', 'https://the_user:the_password@updates.knut.univention.de/the/prefix'),
        ('updates.knut.univention.de', 'the/prefix', 'the_user', 'the_password', '8080', 'http://the_user:the_password@updates.knut.univention.de:8080/the/prefix'),
        ('updates.knut.univention.de', '', 'the_user', 'the_password', '80', 'http://the_user:the_password@updates.knut.univention.de'),
        ('updates.knut.univention.de', '', '', '', '', 'http://updates.knut.univention.de'),
        ('http://us:pw@updates.knut.univention.de:4711/pre/fix', 'the/prefix', 'the_user', 'the_password', '80', 'http://us:pw@updates.knut.univention.de:4711/pre/fix'),
        ('http://updates.knut.univention.de:4711/pre/fix', 'the/prefix', 'the_user', 'the_password', '443', 'http://the_user:the_password@updates.knut.univention.de:4711/pre/fix'),
        ('http://us:pw@updates.knut.univention.de/pre/fix', 'the/prefix', 'the_user', 'the_password', '8080', 'http://us:pw@updates.knut.univention.de:8080/pre/fix'),
        ('http://updates.knut.univention.de', '', '', '', '', 'http://updates.knut.univention.de'),
        ('http://updates.knut.univention.de', 'the/prefix', '', '', '', 'http://updates.knut.univention.de/the/prefix'),
        ('http://updates.knut.univention.de', '', '', 'the_password', '', 'http://updates.knut.univention.de'),
        ('https://updates.knut.univention.de', '', '', '', '', 'https://updates.knut.univention.de'),
        ('https://updates.knut.univention.de:8443', '', '', '', '80', 'https://updates.knut.univention.de:8443'),
        ('file://updates.knut.univention.de', '', '', '', '80', 'file://updates.knut.univention.de'),
        ('file://updates.knut.univention.de', '', '', '', '42', 'file://updates.knut.univention.de:42'),
        ('file://updates.knut.univention.de', '', 'the_user', 'the_password', '42', 'file://the_user:the_password@updates.knut.univention.de:42'),
    ],)
def test_create_url(server, prefix, username, password, port, expected,):
    assert expected == create_url(server, prefix, username, password, port,)
