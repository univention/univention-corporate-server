#!/usr/share/ucs-test/runner /usr/bin/py.test -s
# -*- coding: utf-8 -*.
## desc: Test the UMC user creation, modification and deletion
## bugs: [51777]
## tags: [skip_admember]
## exposure: dangerous

from __future__ import print_function

import pytest
import sys
sys.path.insert(0, '.')
from umc import UDMModule
import univention.admin.modules

import univention.testing.udm as udm_test


class TestUMCMultivalueFilter(UDMModule):

	@pytest.fixture(scope="module")
	def pytest_generate_tests(self, udm, metafunc):
		self.create_connection_authenticate()
		univention.admin.modules.update()
		# modules to be ignored by the test
		ignored_modules = {'appcenter/app',
						   'computers/computer',
						   'dhcp/dhcp',
						   'dhcp/host',
						   'dhcp/server',
						   'dns/reverse_zone',
						   'mail/mail',
						   'nagios/nagios',
						   'policies/autostart',
						   'sba/gremium',
						   'settings/cn',
						   'settings/packages',
						   'shares/print',
						   'users/self',
						   'users/passwd'
						   }
		# modules with additional parameters
		default_attributes = {
			'computers/domaincontroller_backup': ['service', 'inventoryNumber', 'reinstall'],
			'computers/domaincontroller_master': ['service', 'inventoryNumber', 'reinstall'],
			'computers/domaincontroller_slave': ['service', 'inventoryNumber', 'reinstall'],
			'computers/ipmanagedclient': ['ip', 'inventoryNumber', 'network'],
			'computers/linux': ['ip', 'inventoryNumber', 'unixhome'],
			'computers/macos': ['ip', 'inventoryNumber', 'unixhome'],
			'computers/memberserver': ['ip', 'inventoryNumber', 'unixhome'],
			'computers/ubuntu': ['ip', 'inventoryNumber', 'unixhome'],
			'computers/windows': ['ip', 'inventoryNumber', 'unixhome'],
			'computers/windows_domaincontroller': ['ip', 'inventoryNumber', 'unixhome'],
			'container/dc': ['dnsForwardZone'],
			'dhcp/host': ['fixedaddress', 'hwaddress'],
			'dhcp/sharedsubnet': ['range'],
			'dhcp/subnet': ['range'],
			'policies/dhcp_routing': ['routers'],
			'policies/maintenance': ['minute'],
			'policies/repositorysync': ['minute'],
			'policies/umc': ['allow'],
			'settings/data': ['meta', 'ucsversionend'],
			'settings/directory': ['users'],
			'settings/ldapacl': ['appidentifier'],
			'settings/ldapschema': ['appidentifier'],
			'settings/packages': ['packagelist'],
			'settings/printer_model': ['printmodel'],
			'settings/printeruri': ['printeruri'],
			'settings/prohibited_username': ['usernames'],
			'settings/syntax': ['attribute'],
			'settings/udm_hook': ['appidentifier'],
			'settings/udm_module': ['appidentifier'],
			'settings/udm_syntax': ['appidentifier'],
			'settings/umc_operationset': ['operation'],
			'settings/usertemplate': ['e-mail', 'departmentNumbuer', 'disabled'],
			'shares/share': ['writeable'],
			'users/contact': ['homePostalAddress'],
			'users/user': ['umcProperty', 'disabled'],
			'uvmm/cloudconnection': ['parameter']
		}
		metafunc.parametrize('default_attributes', default_attributes)
		metafunc.parametrize('modules', set(univention.admin.modules.modules.keys() - ignored_modules))
		metafunc.parametrize('dn', udm.create_object('container/cn', name='TestUMCFilterContainer'))

	@staticmethod
	def check_attribute_gets_queried_lookup(module_element_name, filter_val, dn, search_value='*'):
		filter_s = "%s=%s" % (filter_val, search_value)
		with udm_test.UCSTestUDM as udm:
			return udm.lookup(module_element_name, dn,  filter=filter_s)

	def check_attribute_gets_queried_umc(self, module_element_name, filter_val, dn, search_value='*'):
		options = {"options":
					   {"hidden": True,
						"objectType": module_element_name,
						"objectProperty": filter_val,
						"objectPropertyValue": search_value,
						"container": dn,
						"fields": ["name", "scriptpath", "labelObjectType", "path"]},
				   "flavor": "navigation"}
		return self.client.umc_command('udm/nav/object/query', options).result

	@staticmethod
	@pytest.fixture(scope="module")
	def udm():
		with udm_test.UCSTestUDM() as udm:
			yield udm

	@pytest.fixture(scope="module")
	def test_with_lookup_is_set(self, udm, modules, default_attributes):
		# check if attributes are set
		for m_element in modules:
			module = univention.admin.modules.get(m_element)
			udm.create_with_defaults(m_element)
			required_attributes = [k for k, v in module.items() if v.required]
			add_attributes = [] if m_element not in default_attributes else default_attributes[m_element]
			attributes = required_attributes + add_attributes
			for attribute in attributes:
				found_values = self.check_attribute_gets_queried_lookup(m_element, attribute)
				assert len(found_values) == 2

	@pytest.fixture(scope="module")
	def test_with_lookup_value(self, udm, modules, default_attributes):
		# check if filter with given value works
		for m_element in modules:
			module = univention.admin.modules.get(m_element)
			object_dn = udm.create_with_defaults(m_element)
			found_object = univention.admin.objects.get(object_dn)[0]
			required_attributes = [k for k, v in module.items() if v.required]
			add_attributes = [] if m_element not in default_attributes else default_attributes[m_element]
			attributes = required_attributes + add_attributes
			for attribute in attributes:
				found_values = self.check_attribute_gets_queried_lookup(m_element, attribute, found_object.info.get(attribute))
				assert len(found_values) == 1

	@staticmethod
	@pytest.fixture(scope="module")
	def test_with_umc_is_set(self, udm, modules, default_attributes):
		for m_element in modules:
			module = univention.admin.modules.get(m_element)
			udm.create_with_defaults(m_element)
			required_attributes = [k for k, v in module.items() if v.required]
			add_attributes = [] if m_element not in default_attributes else default_attributes[m_element]
			attributes = required_attributes + add_attributes
			for attribute in attributes:
				found_values = self.check_attribute_gets_queried_umc(m_element, attribute)
				assert len(found_values) == 2

	@staticmethod
	@pytest.fixture(scope="module")
	def test_with_umc_value(self, udm, modules, default_attributes):
		for m_element in modules:
			module = univention.admin.modules.get(m_element)
			object_dn = udm.create_with_defaults(m_element)
			found_object = univention.admin.objects.get(object_dn)[0]
			required_attributes = [k for k, v in module.items() if v.required]
			add_attributes = [] if m_element not in default_attributes else default_attributes[m_element]
			attributes = required_attributes + add_attributes
			for attribute in attributes:
				found_values = self.check_attribute_gets_queried_umc(m_element, attribute, found_object.info.get(attribute))
				assert len(found_values) == 1
