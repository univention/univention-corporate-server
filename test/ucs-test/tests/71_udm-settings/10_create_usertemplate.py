#!/usr/share/ucs-test/runner pytest-3
## desc: Create a usertemplate object and remove it
## tags: [udm-ldapextensions,apptest]
## roles: [domaincontroller_master]
## exposure: dangerous
## packages:
##   - univention-directory-manager-tools

import pytest

import univention.testing.strings as uts
import univention.testing.utils as utils


@pytest.mark.tags('udm-ldapextensions', 'apptest')
@pytest.mark.roles('domaincontroller_master')
@pytest.mark.exposure('dangerous')
def test_create_usertemplate(udm):
	"""Create a usertemplate object and remove it"""
	template_name = uts.random_name()
	template = udm.create_object('settings/usertemplate', name=template_name)
	utils.verify_ldap_object(template, {'cn': [template_name]})

	udm.remove_object('settings/usertemplate', dn=template)
	utils.verify_ldap_object(template, should_exist=False)
