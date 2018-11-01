#!/usr/share/ucs-test/runner /usr/bin/py.test
# -*- coding: utf-8 -*-
## desc: Test UDM APIs LDAP connection initialization feature
## exposure: dangerous
## roles: [domaincontroller_master]
## tags: [udm_api]
## packages: [python-univention-directory-manager]
## bugs: [47316]

from unittest import main, TestCase
import univention.debug as ud
from univention.testing.ucr import UCSTestConfigRegistry
from univention.udm import UDM, NoObject


ud.init('/var/log/univention/directory-manager-cmd.log', ud.FLUSH, 0)
ud.set_level(ud.ADMIN, ud.ALL)


class TestUdmAutoOpen(TestCase):
	def test_existing_dn(self):
		ucr_test = UCSTestConfigRegistry()
		ucr_test.load()

		udm = UDM.admin().version(1)
		obj = udm.obj_by_dn(ucr_test['ldap/hostdn'])
		assert obj._udm_module == udm.get('computers/domaincontroller_master')
		assert obj.props.name == ucr_test['hostname']

	def test_non_existing_dn(self):
		ucr_test = UCSTestConfigRegistry()
		ucr_test.load()

		udm = UDM.admin().version(1)
		with self.assertRaises(NoObject):
			udm.obj_by_dn('cn=fantasy,' + ucr_test['ldap/hostdn'])

	def test_without_object_type(self):
		ucr_test = UCSTestConfigRegistry()
		ucr_test.load()

		udm = UDM.admin().version(1)
		with self.assertRaises(NoObject):
			udm.obj_by_dn('cn=backup,%s' % ucr_test['ldap/base'])

if __name__ == '__main__':
	main(verbosity=2)
