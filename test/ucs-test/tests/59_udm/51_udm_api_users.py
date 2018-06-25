#!/usr/share/ucs-test/runner python
# -*- coding: utf-8 -*-
## desc: Test UDM API for users/user module
## exposure: dangerous
## roles: [domaincontroller_master]
## packages: [python-univention-directory-manager]

from unittest import main, TestCase
import univention.testing.utils as utils
from univention.testing.strings import random_username
from univention.udm import Udm
from univention.udm.factory_config import UdmModuleFactoryConfiguration, UdmModuleFactoryConfigurationStorage
from univention.admin.uexceptions import noObject


class TestUdmUsersBasic(TestCase):
	config_storage = None
	user_objects = []

	@classmethod
	def setUpClass(cls):
		cls.config_storage = UdmModuleFactoryConfigurationStorage(False)
		cls.config_storage._config = {}
		config1 = UdmModuleFactoryConfiguration(r'^users/.*$', 'univention.udm.generic', 'GenericUdm1Module')
		config2 = UdmModuleFactoryConfiguration(r'groups/.*', 'univention.udm.generic', 'GenericUdm1Module')
		config3 = UdmModuleFactoryConfiguration(r'^users/user$', 'univention.udm.users_user', 'UsersUserUdm1Module')
		cls.config_storage.register_configuration(config1)
		cls.config_storage.register_configuration(config2)
		cls.config_storage.register_configuration(config3)
		cls.udm = Udm.using_admin()
		# cls.udm._configuration_storage = cls.config_storage
		user_mod1 = cls.udm.get('users/user')
		assert user_mod1.__class__.__name__ == 'UsersUserUdm1Module', 'Wrong UDM module.'
		user_mod2 = cls.udm.get('users/user')
		assert user_mod1 is user_mod2, 'UDM module object cache miss.'

	@classmethod
	def tearDownClass(cls):
		for obj in cls.user_objects:
			try:
				obj.delete()
				print('tearDownClass(): Deleted {!r}.'.format(obj))
			except noObject:
				print('tearDownClass(): Already deleted: {!r}.'.format(obj))

	def test_create_user(self):
		user_mod = self.udm.get('users/user')
		obj = user_mod.new()
		self.user_objects.append(obj)
		attrs = {
			'firstname': random_username(),
			'lastname': random_username(),
			'username': random_username(),
			'password': random_username(),
		}
		print('Creating user with attrs: {!r}'.format(attrs))
		for k, v in attrs.items():
			setattr(obj.props, k, v)
		obj.save().reload()
		print('Created {!r}.'.format(obj))
		print('Verifying...')
		assert obj.props.password != attrs['password'], 'Password was not hased or object not reloaded!'
		utils.verify_ldap_object(
			obj.dn,
			expected_attr={
				'uid': [attrs['username']],
				'sn': [attrs['lastname']],
				'givenName': [attrs['firstname']],
			},
			strict=False,
			should_exist=True
		)
		print('OK.')

	def test_modify_user(self):
		user_mod = self.udm.get('users/user')
		obj = user_mod.get(self.user_objects[0].dn)
		attrs = {
			'firstname': random_username(),
			'lastname': random_username(),
		}
		print('Modifying {!r} with attrs: {!r}'.format(obj, attrs))
		for k, v in attrs.items():
			setattr(obj.props, k, v)
		obj.save()
		print('Verifying...')
		utils.verify_ldap_object(
			obj.dn,
			expected_attr={
				'sn': [attrs['lastname']],
				'givenName': [attrs['firstname']],
			},
			strict=False,
			should_exist=True
		)
		print('OK.')

	def test_remove_user(self):
		user_mod = self.udm.get('users/user')
		obj = user_mod.get(self.user_objects[0].dn)
		print('Deleting {!r}...'.format(obj))
		obj.delete()
		print('Verifying...')
		utils.verify_ldap_object(
			obj.dn,
			should_exist=False
		)
		print('OK.')


if __name__ == '__main__':
	main()
