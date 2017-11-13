#!/usr/share/ucs-test/runner /usr/share/ucs-test/selenium
# -*- coding: utf-8 -*-
## desc: test adding, modifying, removal of UDM objects
## packages:
##  - univention-management-console-module-udm
## roles-not:
##  - memberserver
##  - basesystem
## join: true
## exposure: dangerous

from univention.admin import localization
from univention.testing import selenium
import univention.testing.selenium.udm as selenium_udm

translator = localization.translation('ucs-test-selenium')
_ = translator.translate


class UmcUdmError(Exception):
	pass


class UMCTester(object):

	def test_umc(self):
		self.selenium.do_login()

		# The product test requires to create and delete _some_ udm objects.
		# I think those four should be enough.
		# fbest: No, they aren't!
		modules = [
			Users(self.selenium),
			Groups(self.selenium),
			Computers(self.selenium),
			Policies(self.selenium)
		]
		for module in modules:
			self.selenium.open_module(module.name)
			module.wait_for_main_grid_load()
			added_object = self.test_adding_object(module)
			self.test_modifying_object(module, added_object)
			self.test_deleting_object(module, added_object)

	def test_adding_object(self, module):
		print '*** test adding object'
		added_object = module.add()
		if not module.exists(added_object):
			raise UmcUdmError(
				'Adding the object %r in the module %r did not work.'
				% (added_object, module.name)
			)
		return added_object

	def test_modifying_object(self, module, added_object):
		print '*** test modifying object'
		module.open_details(added_object)
		module.edit_some_property_of_the_open_object()
		self.selenium.click_button(_('Save'))
		module.wait_for_main_grid_load()

	def test_deleting_object(self, module, added_object):
		print '*** test removing object'
		module.delete(added_object)
		if module.exists(added_object):
			raise UmcUdmError(
				'Deleting the object %r in the module %r did not work.'
				% (added_object, module.name)
			)


class Users(selenium_udm.Users):
	def edit_some_property_of_the_open_object(self):
		self.selenium.enter_input('description', 'Test description')


class Groups(selenium_udm.Groups):
	def edit_some_property_of_the_open_object(self):
		self.selenium.enter_input('description', 'Test description')


class Computers(selenium_udm.Computers):
	def edit_some_property_of_the_open_object(self):
		self.selenium.enter_input('description', 'Test description')


class Policies(selenium_udm.Policies):
	def edit_some_property_of_the_open_object(self):
		self.selenium.enter_input('releaseVersion', '4.0')


if __name__ == '__main__':
	with selenium.UMCSeleniumTest() as s:
		umc_tester = UMCTester()
		umc_tester.selenium = s

		umc_tester.test_umc()
