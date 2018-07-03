#!/usr/share/ucs-test/runner python
# -*- coding: utf-8 -*-
## desc: Test UDM API for users/user module
## exposure: dangerous
## roles: [domaincontroller_master]
## packages: [python-univention-directory-manager]

from collections import namedtuple
from unittest import main, TestCase
import univention.testing.utils as utils
from univention.testing.strings import random_string, random_username
from univention.testing.udm import UCSTestUDM, UCSTestUDM_CreateUDMObjectFailed
from univention.testing.ucr import UCSTestConfigRegistry
from univention.udm import Udm
from univention.udm.factory_config import UdmModuleFactoryConfiguration, UdmModuleFactoryConfigurationStorage
from univention.admin.uexceptions import noObject
import univention.admin.modules


class TestUdmGenericVariousModules(TestCase):
	config_storage = None
	objects = []
	mail_domain = ''
	ucr_test = None
	udm_test = None

	@classmethod
	def setUpClass(cls):
		config_storage = UdmModuleFactoryConfigurationStorage(False)
		config_storage._config = {}
		# we want to use only 1 class for all UDM modules
		config = UdmModuleFactoryConfiguration(r'^.*/.*$', 'univention.udm.generic', 'GenericUdm1Module')
		config_storage.register_configuration(config)
		cls.udm._configuration_storage = config_storage
		cls.udm = Udm.using_admin()
		cls.udm_test = UCSTestUDM()
		cls.ucr_test = UCSTestConfigRegistry()
		cls.ucr_test.load()

	@classmethod
	def tearDownClass(cls):
		for obj in cls.objects:
			try:
				obj.delete()
				print('tearDownClass(): Deleted {!r}.'.format(obj))
			except noObject:
				print('tearDownClass(): Already deleted: {!r}.'.format(obj))
		cls.ucr_test.revert_to_original_registry()
		cls.udm_test.cleanup()

	def test_load_modules(self):
		print('Loading all modules...')
		univention.admin.modules.update()
		avail_modules = sorted([mod for mod in univention.admin.modules.modules.keys()])
		for mod_name in avail_modules:
			print('Loading {!r}...'.format(mod_name))
			mod = self.udm.get(mod_name)
			assert mod.__class__.__name__ == 'GenericUdm1Module', 'Wrong UDM module.'
		print('Udm._module_class_cache: {!r}'.format(Udm._module_class_cache))
		print('Udm._module_object_cache: {!r}'.format(Udm._module_object_cache))
		print('OK.')

	# def test_modify_user(self):
	# 	user_mod = self.udm.get('users/user')
	# 	obj = user_mod.get(self.user_objects[0].dn)
	# 	attrs = {
	# 		'firstname': random_username(),
	# 		'lastname': random_username(),
	# 		'description': random_string(),
	# 		'mailPrimaryAddress': '{}@{}'.format(random_string(), self.mail_domain),
	# 		'departmentNumber': random_string(),
	# 	}
	# 	print('Modifying {!r} with attrs: {!r}'.format(obj, attrs))
	# 	for k, v in attrs.items():
	# 		setattr(obj.props, k, v)
	# 	obj.save()
	# 	print('Verifying...')
	# 	utils.verify_ldap_object(
	# 		obj.dn,
	# 		expected_attr={
	# 			'sn': [attrs['lastname']],
	# 			'givenName': [attrs['firstname']],
	# 			'description': [attrs['description']],
	# 			'mailPrimaryAddress': [attrs['mailPrimaryAddress']],
	# 			'departmentNumber': [attrs['departmentNumber']],
	# 		},
	# 		strict=False,
	# 		should_exist=True
	# 	)
	# 	print('OK.')


if __name__ == '__main__':
	main()
