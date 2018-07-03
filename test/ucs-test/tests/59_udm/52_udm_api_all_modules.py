#!/usr/share/ucs-test/runner python
# -*- coding: utf-8 -*-
## desc: Test UDM API for users/user module
## exposure: dangerous
## roles: [domaincontroller_master]
## packages: [python-univention-directory-manager]

from collections import defaultdict
from unittest import main, TestCase
import univention.debug as ud
from univention.testing.udm import UCSTestUDM, UCSTestUDM_CreateUDMObjectFailed
from univention.testing.ucr import UCSTestConfigRegistry
from univention.udm import Udm
from univention.udm.factory_config import UdmModuleFactoryConfiguration, UdmModuleFactoryConfigurationStorage
import univention.admin.modules


ud.init('/var/log/univention/directory-manager-cmd.log', ud.FLUSH, 0)
ud.set_level(ud.ADMIN, ud.ALL)


class TestUdmGenericVariousModules(TestCase):
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

	def test_load_modules(self):
		print('Loading all modules...')
		univention.admin.modules.update()
		avail_modules = sorted([mod for mod in univention.admin.modules.modules.keys()])
		for mod_name in avail_modules:
			print('Loading {!r}...'.format(mod_name))
			mod = self.udm.get(mod_name)
			assert mod.__class__.__name__ == 'GenericUdm1Module', 'Wrong UDM module, expected {!r}, got {!r}.'.format(
				'GenericUdm1Module', mod.__class__.__name__)
		print('OK: all modules could be loaded.')
		assert len(Udm._module_class_cache) == 1
		assert len(Udm._module_object_cache) == len(avail_modules)
		print('OK: class and object caches are used.')
		stats = defaultdict(int)
		for mod_name in avail_modules:
			print('Listing objects of type {!r}...'.format(mod_name))
			mod = self.udm.get(mod_name)
			mod.meta.auto_open = False
			num = -1
			for num, obj in enumerate(mod.search()):
				print('{}: {}'.format(num, obj))
			print('OK: found {} objects of type {!r}.'.format(num + 1, mod_name))
			if num > 0:
				stats['mods'] += 1
				stats['objs'] += 1
		print('OK: loaded {objs} objects in {mods} modules.'.format(**stats))


if __name__ == '__main__':
	main()
