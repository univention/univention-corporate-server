#!/usr/share/ucs-test/runner /usr/bin/py.test
# -*- coding: utf-8 -*-
## desc: Test UDM API for users/user module
## exposure: dangerous
## roles: [domaincontroller_master]
## tags: [udm_api, skip_admember]
## packages: [python-univention-directory-manager]
## bugs: [47316]

from __future__ import print_function

from copy import deepcopy
from collections import namedtuple
from unittest import main, TestCase
import univention.debug as ud
import univention.testing.utils as utils
from univention.testing.strings import random_string, random_username
from univention.testing.udm import UCSTestUDM, UCSTestUDM_CreateUDMObjectFailed
from univention.testing.ucr import UCSTestConfigRegistry
from univention.udm import UDM
from univention.udm.exceptions import DeleteError, UnknownProperty, NotYetSavedError, DeletedError, NoObject, ModifyError, CreateError


ud.init('/var/log/univention/directory-manager-cmd.log', ud.FLUSH, 0)
ud.set_level(ud.ADMIN, ud.ALL)


PostalAddress = namedtuple('PostalAddress', ['street', 'zipcode', 'city'])


class TestUdmUsersBasic(TestCase):
	user_objects = []
	mail_domain = ''
	ucr_test = None
	udm_test = None
	_user0_attrs = {}

	@classmethod
	def setUpClass(cls):
		cls.udm = UDM.admin().version(1)

		user_mod1 = cls.udm.get('users/user')
		assert user_mod1.__class__.__name__ == 'UsersUserModule', 'Wrong UDM module.'
		user_mod2 = cls.udm.get('users/user')
		assert user_mod1 is user_mod2, 'UDM module object cache miss.'

		cls.udm_test = UCSTestUDM()
		cls.ucr_test = UCSTestConfigRegistry()
		cls.ucr_test.load()
		try:
			cls.mail_domain = cls.ucr_test['mail/hosteddomains'].split()[0]
		except (AttributeError, IndexError):
			cls.mail_domain = cls.ucr_test['domainname']
			try:
				cls.udm_test.create_object(
					'mail/domain',
					position='cn=domain,cn=mail,{}'.format(cls.ucr_test['ldap/base']),
					name=cls.mail_domain,
					wait_for_replication=True
				)
			except UCSTestUDM_CreateUDMObjectFailed as exc:
				print('Creating mail domain {!r} failed: {}'.format(cls.mail_domain, exc))

	@classmethod
	def tearDownClass(cls):
		for obj in cls.user_objects:
			try:
				obj.delete()
				print('tearDownClass(): Deleted {!r}.'.format(obj))
			except DeleteError:
				print('tearDownClass(): Already deleted: {!r}.'.format(obj))
		cls.ucr_test.revert_to_original_registry()
		cls.udm_test.cleanup()

	def test_create_user_error(self):
		user_mod = self.udm.get('users/user')
		obj = user_mod.new()
		with self.assertRaises(CreateError):
			obj.save()

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
		self._user0_attrs.update(attrs)
		print('Creating user with attrs: {!r}'.format(attrs))
		for k, v in attrs.items():
			setattr(obj.props, k, v)
		obj.save()
		print('Created {!r}.'.format(obj))
		print('Verifying...')
		assert obj.props.password != attrs['password'], 'Password was not hased or object not reloaded!'
		utils.verify_ldap_object(
			obj.dn,
			expected_attr={
				'uid': [attrs['username']],
				'sn': [attrs['lastname']],
				'givenName': [attrs['firstname']],
				'displayName': ['{} {}'.format(attrs['firstname'], attrs['lastname'])],
			},
			strict=False,
			should_exist=True
		)
		obj2 = user_mod.get_by_id(obj.props.username)
		assert obj2.dn == obj.dn

	def test_move_user(self):
		user_mod = self.udm.get('users/user')
		dn = self.user_objects[0].dn
		obj = user_mod.get(dn)
		old_position = obj.position
		obj.position = self.ucr_test['ldap/base']
		obj.save()
		with self.assertRaises(NoObject):
			assert user_mod.get(dn)
		obj.position = old_position
		obj.save()
		utils.wait_for_connector_replication()
		assert user_mod.get(dn) is not None

	def test_modify_error(self):
		user_mod = self.udm.get('users/user')
		obj = user_mod.new()
		self.user_objects.append(obj)
		attrs = {
			'firstname': random_username(),
			'lastname': random_username(),
			'username': random_username(),
			'password': random_username(),
		}
		for k, v in attrs.items():
			setattr(obj.props, k, v)
		assert obj.save()
		obj.props.username = 'Administrator'
		with self.assertRaises(ModifyError):
			obj.save()

	def test_modify_user(self):
		user_mod = self.udm.get('users/user')
		obj = user_mod.get(self.user_objects[0].dn)
		attrs = {
			'firstname': random_username(),
			'lastname': random_username(),
			'description': random_string(),
			'mailPrimaryAddress': '{}@{}'.format(random_string(), self.mail_domain.lower()),
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
				'displayName': ['{} {}'.format(attrs['firstname'], attrs['lastname'])],
			},
			strict=False,
			should_exist=True
		)

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
		obj = UDM.admin().version(0).get('users/user').get(dn)
		assert username == obj.props.username
		obj.props.homePostalAddress = [[ad.street, ad.zipcode, ad.city] for ad in addresses]
		obj.save()
		utils.verify_ldap_object(
			dn,
			expected_attr={
				'homePostalAddress': ['{street}${zipcode}${city}'.format(**ad.__dict__) for ad in addresses],
			},
		)

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
		obj = UDM.admin().version(1).get('users/user').get(dn)
		assert username == obj.props.username
		obj.props.homePostalAddress.extend([ad._asdict() for ad in addresses])
		obj.save()
		utils.verify_ldap_object(
			dn,
			expected_attr={
				'homePostalAddress': ['{street}${zipcode}${city}'.format(**ad.__dict__) for ad in addresses],
			},
		)

	def test_read_user(self):
		obj = self.user_objects[0]
		print('Checking properties of previously created user {!r}...'.format(obj.props.username))
		expected_properties = deepcopy(self._user0_attrs)
		del expected_properties['password']
		expected_properties.update({
			'e-mail': [],
			'displayName': '{} {}'.format(self._user0_attrs['firstname'], self._user0_attrs['lastname']),
		})
		if hasattr(obj.props, 'oxDisplayName'):
			expected_properties['oxDisplayName'] = expected_properties['displayName']
			expected_properties['oxTimeZone'] = self.udm.obj_by_dn(
				'cn=oxTimeZone,cn=open-xchange,cn=custom attributes,cn=univention,{}'.format(self.ucr_test['ldap/base'])
			).props.default
		if hasattr(obj.props, 'mailUserQuota'):
			expected_properties['mailUserQuota'] = 0
		for k, v in expected_properties.items():
			got = getattr(obj.props, k)
			if got != v:
				utils.fail('Expected for {!r}: {!r} got: {!r}'.format(k, v, got))
		with self.assertRaises(UnknownProperty):
			obj.props.unknown = 'Unknown'
		with self.assertRaises(AttributeError):
			obj.props.unknown

	def test_remove_user(self):
		user_mod = self.udm.get('users/user')
		obj = user_mod.new()
		with self.assertRaises(NotYetSavedError):
			obj.reload()
		with self.assertRaises(NotYetSavedError):
			obj.delete()

		obj = user_mod.get(self.user_objects[0].dn)
		print('Deleting {!r}...'.format(obj))
		obj.delete()
		print('Verifying...')
		utils.verify_ldap_object(
			obj.dn,
			should_exist=False
		)
		with self.assertRaises(DeletedError):
			obj.save()
		with self.assertRaises(DeletedError):
			obj.reload()
		assert obj.delete() is None


if __name__ == '__main__':
	main(verbosity=2)
