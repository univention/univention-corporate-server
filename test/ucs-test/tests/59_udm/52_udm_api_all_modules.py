#!/usr/share/ucs-test/runner /usr/bin/py.test
# -*- coding: utf-8 -*-
## desc: Test UDM API for users/user module
## exposure: dangerous
## roles: [domaincontroller_master]
## tags: [udm_api]
## packages: [python-univention-directory-manager]
## bugs: [47316]

from __future__ import print_function

import sys
from collections import defaultdict
from six import string_types
from unittest import main, TestCase
import univention.debug as ud
from univention.udm import UDM, WrongObjectType, NoSuperordinate
import univention.admin.modules


ud.init('/var/log/univention/directory-manager-cmd.log', ud.FLUSH, 0)
ud.set_level(ud.ADMIN, ud.ALL)


class TestUdmGenericVariousModules(TestCase):
	ox_modules = ['oxmail/oxdomain', 'oxmail/oxfolder', 'oxmail/oxlists', 'oxmail/oxmail']
	mail_modules = ['mail/domain', 'mail/folder', 'mail/lists', 'mail/mail']

	@classmethod
	def setUpClass(cls):
		# we want to use only 1 class for all UDM modules
		cls.udm = UDM.admin().version(0)
		cls.udm._module_object_cache.clear()
		univention.admin.modules.update()
		cls.avail_modules = sorted([mod for mod in univention.admin.modules.modules.keys()])

	def get_new_obj(self, mod):  # type: (GenericModuleTV) -> GenericObjectTV
		try:
			return mod.new()
		except NoSuperordinate as exc:
			pass
		print('Module {!r} requires a superordinate, trying to find one...'.format(mod.name))
		try:
			sup_modules = mod._orig_udm_module.superordinate
		except AttributeError:
			print('Got NoSuperordinate exception ({}), but {!r} has no "superordinate" attribute!'.format(exc, mod.name))
			raise NoSuperordinate, exc, sys.exc_info()[2]
		if isinstance(sup_modules, string_types):
			sup_modules = [sup_modules]
		for sup_module in sup_modules:
			for obj in self.udm.get(sup_module).search():
				print('Using {!r} object at {!r} as superordinate for model of {!r} object.'.format(
					sup_module, obj.dn, mod.name))
				return mod.new(obj)
		raise NoSuperordinate, exc, sys.exc_info()[2]

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


if __name__ == '__main__':
	main(verbosity=2)
