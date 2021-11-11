#!/usr/share/ucs-test/runner pytest-3
## desc: |
##  Test settings/extended_options removal
## tags: [udm]
## roles: [domaincontroller_master]
## exposure: careful
## bugs: [25240,21608,41580]
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
    def test_extended_options_removal(self, udm):
        """Test settings/extended_options removal"""
        # bugs: [25240,21608,41580]
        utils.stop_s4connector()
        eo_name = uts.random_name()
        eo_properties = {
            'name': eo_name,
            'shortDescription': eo_name,
            'module': 'groups/group',
            'objectClass': 'univentionFreeAttributes',
            'editable': '1',
        }
        eo = udm.create_object('settings/extended_options', position=udm.UNIVENTION_CONTAINER, **eo_properties)

        group_dn, group_name = udm.create_group(options=['posix', eo_name])
        utils.verify_ldap_object(group_dn, expected_attr={'objectClass': ['univentionFreeAttributes']}, strict=False)

        udm.modify_object('groups/group', dn=group_dn, options=['posix'])
        with pytest.raises(utils.LDAPObjectValueMissing, message='objectClass was not removed from group %r @ %r' % (group_name, group_dn)):
            utils.verify_ldap_object(group_dn, expected_attr={'objectClass': ['univentionFreeAttributes']}, strict=False, retry_count=0)
        utils.start_s4connector()
