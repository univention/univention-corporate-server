#!/usr/share/ucs-test/runner /usr/bin/py.test
# -*- coding: utf-8 -*-
## desc: Test UDM APIs module.meta.auto_open feature
## exposure: dangerous
## roles: [domaincontroller_master]
## tags: [udm_api, skip_admember]
## packages: [python-univention-directory-manager]
## bugs: [47316]

from __future__ import print_function

from unittest import main, TestCase
import univention.debug as ud
from univention.testing.udm import UCSTestUDM
from univention.testing.ucr import UCSTestConfigRegistry
from univention.udm import UDM


ud.init('/var/log/univention/directory-manager-cmd.log', ud.FLUSH, 0)
ud.set_level(ud.ADMIN, ud.ALL)


class TestUdmAutoOpen(TestCase):
	ucr_test = None
	udm_test = None

	@classmethod
	def setUpClass(cls):
		cls.udm = UDM.admin().version(1)

		cls.udm_test = UCSTestUDM()
		cls.ucr_test = UCSTestConfigRegistry()
		cls.ucr_test.load()

	@classmethod
	def tearDownClass(cls):
		cls.ucr_test.revert_to_original_registry()
		cls.udm_test.cleanup()

	def test_auto_open_default(self):
		print('Opening user with default settings (module.meta.auto_open == True)...')
		dn, username = self.udm_test.create_user()
		user_mod = self.udm.get('users/user')
		assert user_mod.meta.auto_open is True
		obj = user_mod.get(dn)
		assert 'cn=Domain Users,cn=groups,{}'.format(self.ucr_test['ldap/base']) in obj.props.groups

	def test_auto_open_false(self):
		print('Opening user with module.meta.auto_open == False...')
		dn, username = self.udm_test.create_user()
		user_mod = self.udm.get('users/user')
		user_mod.meta.auto_open = False
		obj = user_mod.get(dn)
		assert obj.props.groups == []


if __name__ == '__main__':
	main(verbosity=2)
