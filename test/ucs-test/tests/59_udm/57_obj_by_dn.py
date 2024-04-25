#!/usr/share/ucs-test/runner pytest-3
## desc: Test UDM APIs LDAP connection initialization feature
## exposure: dangerous
## roles: [domaincontroller_master]
## tags: [udm_api]
## packages: [python3-univention-directory-manager]
## bugs: [47316]

from unittest import TestCase, main

import pytest

import univention.debug as ud
import univention.logging
from univention.config_registry import ucr
from univention.udm import UDM, NoObject


univention.logging.basicConfig(filename='/var/log/univention/directory-manager-cmd.log', univention_debug_level=ud.ALL)


class TestUdmAutoOpen(TestCase):
    def test_existing_dn(self):
        udm = UDM.admin().version(1)
        obj = udm.obj_by_dn(ucr['ldap/hostdn'])
        assert obj._udm_module == udm.get('computers/domaincontroller_master')
        assert obj.props.name == ucr['hostname']

    def test_non_existing_dn(self):
        udm = UDM.admin().version(1)
        with pytest.raises(NoObject):
            udm.obj_by_dn('cn=fantasy,' + ucr['ldap/hostdn'])

    def test_without_object_type(self):
        udm = UDM.admin().version(1)
        with pytest.raises(NoObject):
            udm.obj_by_dn('cn=backup,%s' % ucr['ldap/base'])


if __name__ == '__main__':
    main(verbosity=2)
