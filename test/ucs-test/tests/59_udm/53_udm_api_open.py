#!/usr/share/ucs-test/runner python
# -*- coding: utf-8 -*-
## desc: Test UDM APIs module.meta.auto_open feature
## exposure: dangerous
## roles: [domaincontroller_master]
## packages: [python-univention-directory-manager]

from unittest import main, TestCase
from univention.testing.udm import UCSTestUDM, UCSTestUDM_CreateUDMObjectFailed
from univention.testing.ucr import UCSTestConfigRegistry
from univention.udm import Udm
from univention.udm.factory_config import UdmModuleFactoryConfiguration, UdmModuleFactoryConfigurationStorage


class TestUdmAutoOpen(TestCase):
	ucr_test = None
	udm_test = None

	@classmethod
	def setUpClass(cls):
		# we want to use only 1 class for all UDM modules and not save anything to disk
		config_storage = UdmModuleFactoryConfigurationStorage(False)
		config_storage._config = {}
		config_storage._load_configuration = lambda: 42
		config = UdmModuleFactoryConfiguration(r'^.*/.*$', 'univention.udm.generic', 'GenericUdm1Module')
		config_storage.register_configuration(config)
		cls.udm = Udm.using_admin()
		cls.udm._configuration_storage = config_storage

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
		print('OK.')

	def test_auto_open_false(self):
		print('Opening user with module.meta.auto_open == False...')
		dn, username = self.udm_test.create_user()
		user_mod = self.udm.get('users/user')
		user_mod.meta.auto_open = False
		obj = user_mod.get(dn)
		assert obj.props.groups == []
		print('OK.')


if __name__ == '__main__':
	main()
