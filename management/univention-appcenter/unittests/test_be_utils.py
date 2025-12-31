#!/usr/bin/python3
# SPDX-FileCopyrightText: 2020-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
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
    ],
)
def test_create_url(server, prefix, username, password, port, expected):
    assert expected == create_url(server, prefix, username, password, port)
