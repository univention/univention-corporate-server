#!/usr/share/ucs-test/runner pytest-3
## desc: settings/extented_attribute
## tags: [udm,apptest]
## roles: [domaincontroller_master]
## exposure: careful
## packages:
##   - univention-directory-manager-tools

import univention.testing.udm as udm_test
from univention.config_registry import ConfigRegistry
import pytest


class Test_UDMExtension(object):
	@pytest.mark.tags('udm', 'apptest')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	def test_extended_attribute_set_user_required_field_without_default(self, udm, ucr):
		"""settings/extented_attribute"""
		kwargs = dict(name='test', ldapMapping='foo', objectClass='bar', shortDescription='test', valueRequired='1', CLIName='test', module=['users/user'])
		with pytest.raises(udm_test.UCSTestUDM_CreateUDMObjectFailed):
			udm.create_object('settings/extended_attribute', position='cn=custom attributes, cn=univention, %s' % ucr['ldap/base'], **kwargs)
		kwargs['default'] = 'foo'
		udm.create_object('settings/extended_attribute', position='cn=custom attributes, cn=univention, %s' % ucr['ldap/base'], **kwargs)
