#!/usr/bin/python3
# SPDX-FileCopyrightText: 2003-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import os
import unittest

import univention.license as ul


class TestBasic(unittest.TestCase):
    def test_double_free(self):
        ul.free()
        ul.free()

    def test_getValues(self):
        """Return value from globally selected licence."""
        with self.assertRaises(KeyError):
            ul.getValue('doesNotExists')


@unittest.skipUnless(os.access('/etc/machine.secret', os.R_OK), 'Requires /etc/machine.secret')
class TestSelect(unittest.TestCase):
    def test_select(self):
        """Select licence by LDAP search `(univentionLicenseModule=admin)`"""
        ret = ul.select('admin')
        assert ret == 0
        ul.free()
        ul.free()

    def test_getValues(self):
        """Return value from globally selected licence."""
        ret = ul.select('admin')
        assert ret == 0
        val = ul.getValue('univentionLicenseBaseDN')
        assert val is not None
        ul.free()

    @unittest.skip('WIP')
    def test_selectDN(self):
        """Select licence by LDAP DN."""
        ret = ul.selectDN('cn=admin,cn=license,cn=univention,%s')
        assert ret == 0
        ul.free()

    @unittest.skip('WIP')
    def test_check(self):
        """
        Just check licence by LDAP DN. Returns bit-field:

        0b0001: Invalid signature
        0b0010: Invalid end date
        0b0100: Invalid base DN
        0b1000: Invalid search path
        """
        ret = ul.check('cn=admin,cn=license,cn=univention,%s')
        assert ret == 0
        ul.free()


if __name__ == '__main__':
    unittest.main()
