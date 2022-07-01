#!/usr/share/ucs-test/runner pytest-3 -s
## desc: Creates extended attributes and usertemplate
## bugs: [51364]
## roles:
##  - domaincontroller_master
## packages:
##   - univention-directory-manager-tools
## exposure: dangerous

import univention.testing.strings as uts
import univention.testing.utils as utils


def test_usertemplate_filter(udm, ucr):
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
		'module': ['users/user', 'settings/usertemplate'],
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

	template = udm.create_object('settings/usertemplate', name=uts.random_name(), mail='<username>@example.com')
	utils.verify_ldap_object(template, {'mail': ['<username>@example.com'], 'objectClass': ['top', 'univentionUserTemplate', 'univentionObject']}, strict=True, should_exist=True)
