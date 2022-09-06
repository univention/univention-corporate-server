#!/usr/share/ucs-test/runner pytest-3
# -*- coding: utf-8 -*-
## desc: Test UDM API for users/user module
## exposure: dangerous
## roles: [domaincontroller_master]
## tags: [udm_api, skip_admember]
## packages: [python3-univention-directory-manager]
## bugs: [47316, 51184, 53620]


import os
from collections import defaultdict, namedtuple
from copy import deepcopy
from subprocess import call
from typing import List, Tuple  # noqa: F401

import pytest
from six import reraise, string_types
from unittest import TestCase, main

import univention.admin.modules
import univention.debug as ud
import univention.testing.strings as uts
from univention.testing import utils
from univention.testing.strings import random_string, random_username
from univention.testing.ucr import UCSTestConfigRegistry
from univention.testing.udm import UCSTestUDM, UCSTestUDM_CreateUDMObjectFailed
from univention.udm import (
	UDM, ApiVersionMustNotChange, ApiVersionNotSupported, ConnectionError, NoApiVersionSet, WrongObjectType,
)
from univention.udm.connections import LDAP_connection
from univention.udm.exceptions import (
	CreateError, DeletedError, DeleteError, ModifyError, MoveError, NoObject, NoSuperordinate,
	NotYetSavedError, UnknownProperty,
)

ud.init('/var/log/univention/directory-manager-cmd.log', ud.FLUSH, 0)
ud.set_level(ud.ADMIN, ud.ALL)

PostalAddress = namedtuple('PostalAddress', ['street', 'zipcode', 'city'])


class TestUdmUsersBasic(TestCase):
	"""Test UDM API for users/user module"""
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
				'homePostalAddress': ['{street}${zipcode}${city}'.format(**ad._asdict()) for ad in addresses],
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
				'homePostalAddress': ['{street}${zipcode}${city}'.format(**ad._asdict()) for ad in addresses],
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
			assert got == v, 'Expected for {!r}: {!r} got: {!r}'.format(k, v, got)
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


class TestUdmGenericVariousModules(TestCase):
	"""Test UDM API for users/user module"""
	ox_modules = ['oxmail/oxdomain', 'oxmail/oxfolder', 'oxmail/oxlists', 'oxmail/oxmail']
	mail_modules = ['mail/domain', 'mail/folder', 'mail/lists', 'mail/mail']

	@classmethod
	def setUpClass(cls):
		# we want to use only 1 class for all UDM modules
		cls.udm = UDM.admin().version(0)
		cls.udm._module_object_cache.clear()
		univention.admin.modules.update()
		cls.avail_modules = sorted([mod for mod in univention.admin.modules.modules.keys()])

	def get_new_obj(self, mod):
		try:
			return mod.new()
		except NoSuperordinate as exc:
			exc_thrown = exc
		print('Module {!r} requires a superordinate, trying to find one...'.format(mod.name))
		try:
			sup_modules = mod._orig_udm_module.superordinate
		except AttributeError:
			print('Got NoSuperordinate exception ({}), but {!r} has no "superordinate" attribute!'.format(exc_thrown, mod.name))
			reraise(NoSuperordinate, exc_thrown)
		if isinstance(sup_modules, string_types):
			sup_modules = [sup_modules]
		for sup_module in sup_modules:
			for obj in self.udm.get(sup_module).search():
				print('Using {!r} object at {!r} as superordinate for model of {!r} object.'.format(
					sup_module, obj.dn, mod.name))
				return mod.new(obj)
		reraise(NoSuperordinate, exc_thrown)

	def test_load_modules(self):
		print('Loading all modules...')
		mail_and_ox_modules = self.ox_modules + self.mail_modules
		for mod_name in self.avail_modules:
			print('Loading {!r}...'.format(mod_name))
			mod = self.udm.get(mod_name)
			if mod_name in mail_and_ox_modules:
				assert mod.__class__.__name__ == 'GenericModule', 'Wrong UDM module, expected {!r}, got {!r}.'.format(
					'GenericModule', mod.__class__.__name__)
		print('OK: all modules could be loaded.')
		len_module_object_cache = len(UDM._module_object_cache)
		assert len_module_object_cache == len(self.avail_modules), 'UDM._module_object_cache has {} entries (should be {}).'.format(len_module_object_cache, len(self.avail_modules))
		print('OK: object cache is used.')
		stats = defaultdict(int)
		for mod_name in self.avail_modules:
			print('Listing objects of type {!r}...'.format(mod_name))
			mod = self.udm.get(mod_name)
			if mod_name == 'users/self':
				print('Skipping module "users/self" with broken mapping.')
				continue
			else:
				try:
					self.get_new_obj(mod)  # test whether a new object may be initialized
				except NoSuperordinate:
					# for now...
					print('Cannot test "new" for {!r}. Requires superordinate'.format(mod_name))
			mod.meta.auto_open = False
			num = -1
			try:
				for num, obj in enumerate(mod.search()):
					print('{}: {}'.format(num, obj))
			except WrongObjectType as exc:
				if exc.module_name.startswith('oxmail/'):
					# oxmail modules also loading non-ox objects
					continue
			print('OK: found {} objects of type {!r}.'.format(num + 1, mod_name))
			if num > 0:
				stats['mods'] += 1
				stats['objs'] += num
		print('OK: loaded {objs} objects in {mods} modules.'.format(**stats))


class TestUdmAutoOpen(TestCase):
	"""Test UDM APIs module.meta.auto_open feature"""
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


class TestUdmLDAPConnection(TestCase):
	"""Test UDM APIs LDAP connection initialization feature"""
	ucr_test = None
	udm_test = None

	@classmethod
	def setUpClass(cls):
		cls.udm_test = UCSTestUDM()
		cls.ucr_test = UCSTestConfigRegistry()
		cls.ucr_test.load()

	@classmethod
	def tearDownClass(cls):
		cls.ucr_test.revert_to_original_registry()
		cls.udm_test.cleanup()

	@classmethod
	def setUp(self):
		LDAP_connection._clear()

	def test_error_in_version(self):
		with self.assertRaises(NoApiVersionSet):
			UDM.admin().get('users/user')
		with self.assertRaises(ApiVersionNotSupported):
			UDM.admin().version('1')
		with self.assertRaises(ApiVersionMustNotChange):
			UDM.admin().version(0).version(1)
		with self.assertRaises(ApiVersionNotSupported):
			UDM.admin().version(20).get('users/user')

	def test_admin(self):
		mod = UDM.admin().version(0).get('users/user')
		assert mod.connection.binddn == 'cn=admin,{}'.format(self.ucr_test['ldap/base'])

	def test_admin_io_error(self):
		try:
			os.rename('/etc/ldap.secret', '/etc/ldap.secret.test')
			with self.assertRaises(ConnectionError) as cm:
				UDM.admin()
			assert str(cm.exception) == 'Could not read secret file'
		finally:
			os.rename('/etc/ldap.secret.test', '/etc/ldap.secret')

	def test_machine(self):
		mod = UDM.machine().version(0).get('users/user')
		assert mod.connection.binddn == self.ucr_test['ldap/hostdn']

	def test_machine_down_error(self):
		assert call(['systemctl', 'stop', 'slapd']) == 0
		try:
			with self.assertRaises(ConnectionError) as cm:
				UDM.machine()
			assert str(cm.exception) == 'The LDAP Server is not running'
		finally:
			assert call(['systemctl', 'start', 'slapd']) == 0

	def test_machine_credentials_error(self):
		pw = open('/etc/machine.secret').read()
		try:
			open('/etc/machine.secret', 'w').write('garbage')
			with self.assertRaises(ConnectionError) as cm:
				UDM.machine()
			assert str(cm.exception) == 'Credentials invalid'
		finally:
			open('/etc/machine.secret', 'w').write(pw)

	def test_credentials(self):
		password = uts.random_name()
		dn, username = self.udm_test.create_user(password=password)
		mod = UDM.credentials(identity=username, password=password).version(0).get('users/user')
		assert mod.connection.binddn == dn

		password = uts.random_name()
		dn, username = self.udm_test.create_user(password=password)
		mod = UDM.credentials(identity=dn, password=password).version(0).get('users/user')
		assert mod.connection.binddn == dn

	def test_local(self):
		password = uts.random_name()
		dn, username = self.udm_test.create_user(password=password)
		server = self.ucr_test['ldap/server/name']
		port = self.ucr_test['ldap/server/port']
		mod = UDM.credentials(identity=username, password=password, server=server, port=port).version(0).get('users/user')
		assert mod.connection.binddn == dn

	def test_credentials_error(self):
		username = uts.random_name()
		password = uts.random_name()
		with self.assertRaises(ConnectionError) as cm:
			UDM.credentials(identity=username, password=password)
		assert str(cm.exception) == 'Cannot get DN for username'

		with self.assertRaises(ConnectionError) as cm:
			UDM.credentials(identity='Administrator', password=password)
		assert str(cm.exception) == 'Credentials invalid'


class TestUdmModuleCaching(TestCase):
	"""Test UDM APIs module caching"""

	def test_caching(self):
		assert UDM.admin().version(0).get('users/user') is UDM.admin().version(0).get('users/user')
		assert UDM.admin().version(0).get('users/user') is not UDM.admin().version(1).get('users/user')
		assert UDM.admin().version(1).get('users/user') is UDM.admin().version(1).get('users/user')
		assert UDM.admin().version(0).get('users/user') is not UDM.admin().version(0).get('groups/group')
		assert UDM.admin().version(0).get('users/user') is not UDM.machine().version(0).get('users/user')


class TestUdmDNSBasic(TestCase):
	"""Test UDM API for dns/* module"""
	@classmethod
	def setUpClass(cls):
		cls.udm = UDM.admin().version(1)
		cls.ucr_test = UCSTestConfigRegistry()
		cls.ucr_test.load()

	def test_superordinate_and_duplicate(self):
		host_records = self.udm.get('dns/host_record')
		with self.assertRaises(NoSuperordinate):
			host_records.new()
		forward_zones = self.udm.get('dns/forward_zone')
		forward_zone = list(forward_zones.search())[0]
		host_record1 = host_records.new(forward_zone)
		assert host_record1.position == forward_zone.dn
		host_record1.props.name = 'x1'
		host_record1.save()
		try:
			host_record1_dup = host_records.new(forward_zone)
			host_record1_dup.props.name = 'x1'
			with self.assertRaises(CreateError):
				host_record1_dup.save()
		finally:
			host_record1.delete()

	def test_superordinate_and_move(self):
		host_records = self.udm.get('dns/host_record')
		with self.assertRaises(NoSuperordinate):
			host_records.new()
		forward_zones = self.udm.get('dns/forward_zone')
		forward_zone = list(forward_zones.search())[0]
		host_record2 = host_records.new(forward_zone.dn)
		host_record2.props.name = 'x2'
		host_record2.save()
		try:
			host_record2.position = self.ucr_test['ldap/base']
			with self.assertRaises(MoveError):
				host_record2.save()
		finally:
			host_record2.delete()


class TestUdmComputersBasic(TestCase):
	"""Test UDM API for computers/* module"""
	@classmethod
	def setUpClass(cls):
		cls.udm = UDM.admin().version(1)
		cls.ucr_test = UCSTestConfigRegistry()
		cls.ucr_test.load()

	def test_cleanup(self):
		ubuntu = self.udm.get('computers/ubuntu').new()
		ubuntu.props.name = 'ubuntu'
		ubuntu.props.network = 'cn=default,cn=networks,%s' % self.ucr_test['ldap/base']
		ubuntu.save()
		try:
			num_ptr_records = len(list(self.udm.get('dns/ptr_record').search()))
			ip = ubuntu.props.ip[0]
			forward_zone = list(self.udm.get('dns/forward_zone').search())[0]
			reverse_zone = list(self.udm.get('dns/reverse_zone').search())[0]
			ubuntu.props.dnsEntryZoneForward = [[forward_zone.dn, ip]]
			ubuntu.props.dnsEntryZoneReverse = [[reverse_zone.dn, ip]]
			ubuntu.save()
			# assert newly created ptr record
			assert num_ptr_records + 1 == len(list(self.udm.get('dns/ptr_record').search()))
			ubuntu.delete()
			assert num_ptr_records == len(list(self.udm.get('dns/ptr_record').search()))
		finally:
			ubuntu.delete()

	def test_move_error(self):
		ubuntu = self.udm.get('computers/ubuntu').new()
		ubuntu.props.name = 'ubuntu'
		ubuntu.save()
		try:
			containers = self.udm.get('container/cn')
			container = containers.new()
			container.props.name = 'ubuntu'
			container.save()
			try:
				container.position = ubuntu.position
				with self.assertRaises(MoveError):
					container.save()
			finally:
				container.delete()
		finally:
			ubuntu.delete()

	def test_default_position(self):
		ubuntu = self.udm.get('computers/ubuntu').new()
		assert ubuntu.position == 'cn=computers,%s' % self.ucr_test['ldap/base']
		memberserver = self.udm.get('computers/memberserver').new()
		assert memberserver.position == 'cn=memberserver,cn=computers,%s' % self.ucr_test['ldap/base']
		slave = self.udm.get('computers/domaincontroller_slave').new()
		assert slave.position == 'cn=dc,cn=computers,%s' % self.ucr_test['ldap/base']
		backup = self.udm.get('computers/domaincontroller_backup').new()
		assert backup.position == 'cn=dc,cn=computers,%s' % self.ucr_test['ldap/base']
		master = self.udm.get('computers/domaincontroller_master').new()
		assert master.position == 'cn=dc,cn=computers,%s' % self.ucr_test['ldap/base']


class TestEncoders(TestCase):
	"""Test UDM API encoders"""
	# bugs: [51184]
	user_objects = []

	@classmethod
	def setUpClass(cls):
		cls.udm = UDM.admin().version(2)

	@classmethod
	def tearDownClass(cls):
		for obj in cls.user_objects:
			try:
				obj.delete()
				print('tearDownClass(): Deleted {!r}.'.format(obj))
			except DeleteError:
				print('tearDownClass(): Already deleted: {!r}.'.format(obj))

	def test_dn_list_property_encoder(self):
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
		obj.save()
		assert obj.props.secretary.objs == []

		obj2 = user_mod.new()
		self.user_objects.append(obj2)
		attrs = {
			'firstname': random_username(),
			'lastname': random_username(),
			'username': random_username(),
			'password': random_username(),
		}
		print('Creating user with attrs: {!r}'.format(attrs))
		for k, v in attrs.items():
			setattr(obj2.props, k, v)
		obj2.save()

		obj.props.secretary.append(obj2.dn)
		obj.save()
		assert [o.dn for o in obj.props.secretary.objs] == [obj2.dn]


@pytest.fixture
def simple_udm(ucr):  # type: () -> UDM
	account = utils.UCSTestDomainAdminCredentials()
	return UDM.credentials(
		account.binddn,
		account.bindpw,
		ucr["ldap/base"],
		ucr["ldap/master"],
		ucr["ldap/master/port"],
	).version(1)


@pytest.fixture
def schedule_delete_udm_obj(simple_udm):
	objs = []  # type: List[Tuple[str, str]]

	def _func(dn, udm_mod):  # type: (str, str) -> None
		objs.append((dn, udm_mod))

	yield _func

	for dn, udm_mod_name in objs:
		mod = simple_udm.get(udm_mod_name)
		try:
			udm_obj = mod.get(dn)
		except NoObject:
			print("UDM {!r} object {!r} does not exist (anymore).".format(udm_mod_name, dn))
			continue
		try:
			udm_obj.delete(remove_childs=True)
			print("Deleted UDM {!r} object {!r} through UDM.".format(udm_mod_name, dn))
		except NotYetSavedError:
			print("UDM {!r} object {!r} not deleted, it had not been saved.".format(udm_mod_name, dn))


def test_remove_children(ldap_base, schedule_delete_udm_obj, simple_udm):
	"""Test 'remove' operation in UDM API"""
	# bugs: [53620]
	cn_mod = simple_udm.get("container/cn")
	cn_obj = cn_mod.new(ldap_base)
	cn_obj.props.name = random_username()
	cn_obj.save()
	schedule_delete_udm_obj(cn_obj.dn, "container/cn")
	cn_obj_dn = cn_obj.dn
	assert cn_mod.get(cn_obj_dn)

	users_mod = simple_udm.get("users/ldap")
	user_obj = users_mod.new()
	user_obj.position = cn_obj.dn
	user_obj.props.username = random_username()
	user_obj.props.password = random_username()
	user_obj.save()
	schedule_delete_udm_obj(user_obj.dn, "users/user")
	user_obj_dn = user_obj.dn

	user_obj2 = users_mod.get(user_obj_dn)
	assert user_obj2
	assert user_obj2.position == cn_obj_dn

	cn_obj.delete(remove_childs=True)

	with pytest.raises(NoObject):
		cn_mod.get(cn_obj_dn)

	with pytest.raises(NoObject):
		users_mod.get(user_obj_dn)


def test_remove_children_missing(ldap_base, schedule_delete_udm_obj, simple_udm):
	"""Test 'remove' operation in UDM API"""
	# bugs: [53620]
	cn_mod = simple_udm.get("container/cn")
	cn_obj = cn_mod.new(ldap_base)
	cn_obj.props.name = random_username()
	cn_obj.save()
	schedule_delete_udm_obj(cn_obj.dn, "container/cn")
	cn_obj_dn = cn_obj.dn
	assert cn_mod.get(cn_obj_dn)

	users_mod = simple_udm.get("users/ldap")
	user_obj = users_mod.new()
	user_obj.position = cn_obj.dn
	user_obj.props.username = random_username()
	user_obj.props.password = random_username()
	user_obj.save()
	schedule_delete_udm_obj(user_obj.dn, "users/user")
	user_obj_dn = user_obj.dn

	user_obj2 = users_mod.get(user_obj_dn)
	assert user_obj2
	assert user_obj2.position == cn_obj_dn

	with pytest.raises(DeleteError) as excinfo:
		cn_obj.delete()  # default: remove_childs=False
	assert "Operation not allowed on non-leaf" in str(excinfo.value)

	assert cn_mod.get(cn_obj_dn)
	assert users_mod.get(user_obj_dn)


if __name__ == '__main__':
	main(verbosity=2)
