#!/usr/share/ucs-test/runner pytest-3
## desc: Test settings/extended_attribute with deleteObjectClass=1
## tags: [udm]
## roles: [domaincontroller_master]
## exposure: careful
## bugs: [41207]
## packages:
##   - univention-config
##   - univention-directory-manager-tools

import univention.testing.strings as uts
import univention.testing.utils as utils
import pytest


class Test_UDMExtension(object):
    @pytest.mark.tags('udm')
    @pytest.mark.roles('domaincontroller_master')
    @pytest.mark.exposure('careful')
    def test_extended_attribute_removal_oc(self, udm):
        """Test settings/extended_attribute with deleteObjectClass=1"""
        # bugs: [41207]
        ea_name = uts.random_name()
        ea_properties = {
            'name': ea_name,
            'shortDescription': ea_name,
            'CLIName': ea_name,
            'module': 'groups/group',
            'objectClass': 'univentionFreeAttributes',
            'ldapMapping': 'univentionFreeAttribute15',
            'deleteObjectClass': '1',
            'mayChange': '1',
        }
        ea = udm.create_object('settings/extended_attribute', position=udm.UNIVENTION_CONTAINER, **ea_properties)
        udm.stop_cli_server()

        ea_value = uts.random_string()
        group_dn, group_name = udm.create_group(**{ea_name: ea_value})
        utils.verify_ldap_object(group_dn, expected_attr={'objectClass': ['univentionFreeAttributes']}, strict=False)

        udm.modify_object('groups/group', dn=group_dn, set={ea_name: ''})
        with pytest.raises(utils.LDAPObjectValueMissing, message='objectClass was not removed from group %r @ %r' % (group_name, group_dn)):
            utils.verify_ldap_object(group_dn, expected_attr={'objectClass': ['univentionFreeAttributes']}, strict=False)
