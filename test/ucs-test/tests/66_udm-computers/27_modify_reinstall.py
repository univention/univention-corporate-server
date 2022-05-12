#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: Test modifying reinstall for computers/domaincontroller_master, computers/domaincontroller_slave, computers/domaincontroller_backup and computers/memberserver
## tags: [udm-computers]
## roles: [domaincontroller_master]
## exposure: careful
## packages:
##   - univention-config
##   - univention-directory-manager-tools

import pytest

from univention.testing.strings import random_name
from univention.testing.udm import UCSTestUDM

COMPUTER_MODULES = UCSTestUDM.COMPUTER_MODULES


@pytest.mark.tags('udm-computers')
@pytest.mark.roles('domaincontroller_master')
@pytest.mark.exposure('careful')
@pytest.mark.parametrize('role', ('computers/domaincontroller_master', 'computers/domaincontroller_slave', 'computers/domaincontroller_backup', 'computers/memberserver'))
def test_modify_reinstall(role, verify_ldap_object, udm):
			"""Test modifying reinstall for computers/domaincontroller_master, computers/domaincontroller_slave, computers/domaincontroller_backup and computers/memberserver"""
			reinstall = '1'
			computer = udm.create_object(role, name=random_name())
			udm.modify_object(role, dn=computer, reinstall=reinstall)
			verify_ldap_object(computer, {'univentionServerReinstall': [reinstall]})
