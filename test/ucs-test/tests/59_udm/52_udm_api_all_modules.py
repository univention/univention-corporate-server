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


class TestUdmGenericVariousModules(TestCase):
	config_storage = None
	objects = []
	mail_domain = ''
	ucr_test = None
	udm_test = None

	@classmethod
	def setUpClass(cls):
		cls.config_storage = UdmModuleFactoryConfigurationStorage(False)
		cls.config_storage._config = {}
		config1 = UdmModuleFactoryConfiguration(r'^.*/.*$', 'univention.udm.generic', 'GenericUdm1Module')
		cls.config_storage.register_configuration(config1)
		cls.udm = Udm.using_admin()
		for mod in ('')
		mod = cls.udm.get('users/user')
		assert mod.__class__.__name__ == 'GenericUdm1Module', 'Wrong UDM module.'
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
			'description': random_string(),
			'mailPrimaryAddress': '{}@{}'.format(random_string(), self.mail_domain),
			'departmentNumber': random_string(),
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
				'description': [attrs['description']],
				'mailPrimaryAddress': [attrs['mailPrimaryAddress']],
				'departmentNumber': [attrs['departmentNumber']],
			},
			strict=False,
			should_exist=True
		)
		print('OK.')

	def test_modify_user_homePostalAddress_udm1_generic(self):
		addresses = [
			PostalAddress(random_string(), random_string(), random_string()),
			PostalAddress(random_string(), random_string(), random_string()),
			PostalAddress(random_string(), random_string(), random_string()),
		]
		dn, username = self.udm_test.create_user()
		utils.verify_ldap_object(
			dn,
			expected_attr={
				'uid': [username],
				'homePostalAddress': [],
			},
		)
		config = UdmModuleFactoryConfiguration('users/user', 'univention.udm.generic', 'GenericUdm1Module')
		user_mod_generic = self.udm.get_by_factory_config('users/user', config)
		obj = user_mod_generic.get(dn)
		assert username == obj.props.username
		obj.props.homePostalAddress = [[ad.street, ad.zipcode, ad.city] for ad in addresses]
		obj.save()
		utils.verify_ldap_object(
			dn,
			expected_attr={
				'homePostalAddress': ['{street}${zipcode}${city}'.format(**ad.__dict__) for ad in addresses],
			},
		)
		print('OK.')

	def test_modify_user_homePostalAddress_as_dict(self):
		addresses = [
			PostalAddress(random_string(), random_string(), random_string()),
			PostalAddress(random_string(), random_string(), random_string()),
			PostalAddress(random_string(), random_string(), random_string()),
		]
		dn, username = self.udm_test.create_user()
		utils.verify_ldap_object(
			dn,
			expected_attr={
				'uid': [username],
				'homePostalAddress': [],
			},
		)
		config = UdmModuleFactoryConfiguration('users/user', 'univention.udm.users_user', 'UsersUserUdm1Module')
		user_mod_usersuser = self.udm.get_by_factory_config('users/user', config)
		obj = user_mod_usersuser.get(dn)
		assert username == obj.props.username
		obj.props.homePostalAddress.extend([ad.__dict__ for ad in addresses])
		obj.save()
		utils.verify_ldap_object(
			dn,
			expected_attr={
				'homePostalAddress': ['{street}${zipcode}${city}'.format(**ad.__dict__) for ad in addresses],
			},
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
