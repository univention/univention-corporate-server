#!/usr/share/ucs-test/runner python
# -*- coding: utf-8 -*.
## desc: Test the UMC user creation, modification and deletion
## bugs: [51777]
## tags: [skip_admember]
## exposure: dangerous

from __future__ import print_function

import sys
sys.path.insert(0, '.')
from umc import UDMModule
import univention.admin.modules

import univention.testing.udm as udm_test
import univention.testing.strings as uts


class TestUMCMultivalueFilter(UDMModule):

    def __init__(self):
        """Test Class constructor"""
        super(TestUMCMultivalueFilter, self).__init__()
        self.ldap_base = None
        univention.admin.modules.update()
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
        with udm_test.UCSTestUDM() as udm:
            self.default_attributes = {
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
        self.modules = set(univention.admin.modules.modules.keys() - ignored_modules)

        self.dn = udm.create_object('container/cn', name='TestUMCFilterContainer')

    def run_tests_for_modules(self):
        with udm_test.UCSTestUDM() as udm:
            for m_element in self.modules:
                module = univention.admin.modules.get(m_element)
                # Todo
                objects = univention.admin.objects.get(m_element)
                number_existing_elements = udm.lookup(m_element, self.dn)
                created_elements = self.create_with_complex_attributes(udm, m_element)
                for k, value in [(k, v) for k, v in module.items() if not v.dontsearch]:
                    found_values = self.check_attribute_gets_queried(m_element, k)
                    if k in self.default_attributes[m_element]:
                        assert 1 <= len(found_values) < number_existing_elements + 2
                    elif value.required:
                        assert len(found_values) - number_existing_elements == (2 if created_elements else 1)

    def create_with_complex_attributes(self, udm, m_element):
        created_multiple = False
        if m_element in self.default_attributes:
            udm.create_with_defaults(m_element, **self.default_attributes[m_element])
            created_multiple = True
        udm.create_with_defaults(m_element)
        return created_multiple

    @staticmethod
    def check_attribute_gets_queried(module_element_name, filter_val):
        filter_s = "%s=*" % filter_val
        with udm_test.UCSTestUDM as udm:
            return udm.lookup(module_element_name, self.dn,  filter=filter_s)

    def main(self):
        """
        Method to test UMC users creation, modification and deletion
        """
        self.create_connection_authenticate()
        self.ldap_base = self.ucr.get('ldap/base')

        self.run_tests_for_modules()


if __name__ == '__main__':
    TestUMC = TestUMCMultivalueFilter()
    sys.exit(TestUMC.main())
