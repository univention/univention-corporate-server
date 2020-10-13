#!/usr/share/ucs-test/runner /usr/bin/py.test -s
## desc: Creates extended attributes and usertemplate
## bugs: [51364]
## roles:
##  - domaincontroller_master
## packages:
##   - univention-directory-manager-modules
## exposure: dangerous

import pytest
import univention.testing.udm as udm_test
import univention.testing.ucr as ucr_test
import univention.testing.strings as uts
import univention.testing.utils as utils


@pytest.fixture(scope="module")
def udm():
	with udm_test.UCSTestUDM() as udm:
		yield udm

@pytest.fixture(scope="module")
def ucr():
	with ucr_test.UCSTestConfigRegistry() as ucr:
		yield ucr

def _create_and_verify_extended_attribute(udm, ucr):
	properties = {
		'CLIName': 'mail',
		'copyable': '0',
		'deleteObjectClass': '0',
		'disableUDMWeb': '0',
		'doNotSearch': '0',
		'fullWidth': '0',
		'groupName': 'User account',
		'groupPosition': '11',
		'ldapMapping': 'mail',
		'longDescription': 'Mail Attribut',
		'mayChange': '1',
		'module': 'users/user',
		'module': 'settings/usertemplate',
		'name': 'mail',
		'objectClass': 'inetOrgPerson',
		'overwritePosition': 'None',
		'overwriteTab': '0',
		'shortDescription': 'Mail Attribut',
		'syntax': 'String',
		'tabAdvanced': '0',
		'tabName': 'General',
		'tabPosition': '11',
		'valueRequired': '0'
		}
	extended_attribute = udm.create_object('settings/extended_attribute', position='cn=custom attributes,cn=univention,%s' % (ucr.get('ldap/base')), **properties)
	utils.verify_ldap_object(extended_attribute, should_exist=True)

def _create_and_verify_usertemplate(udm):
	template = udm.create_object('settings/usertemplate', name=uts.random_name(), mail='<username>@example.com')
	utils.verify_ldap_object(template, {'mail': ['<username>@example.com'], 'objectClass': ['top', 'univentionUserTemplate', 'univentionObject']}, strict=True, should_exist=True)

def test_usertemplate_filter(udm, ucr):
	_create_and_verify_extended_attribute(udm, ucr)
	_create_and_verify_usertemplate(udm)
