#!/usr/share/ucs-test/runner python3
## desc: Try to create invalid ldap schema objects
## tags: [udm-ldapextensions,apptest]
## roles: [domaincontroller_master]
## exposure: dangerous
## packages:
##   - univention-directory-manager-tools

import base64
import bz2

import univention.testing.strings as uts
import univention.testing.udm as udm_test
import univention.testing.utils as utils

if __name__ == '__main__':
	with udm_test.UCSTestUDM() as udm:
		schema_name = uts.random_name()
		filename = '/90%s' % uts.random_name()
		data = '# schema test'
		try:
			schema = udm.create_object('settings/ldapschema', name=schema_name, filename=filename, data=base64.b64encode(bz2.compress(data.encode('UTF-8'))).decode('ASCII'))
		except udm_test.UCSTestUDM_CreateUDMObjectFailed:
			pass
		else:
			utils.fail('settings/ldapschema object with / in filename was created')

		schema_name = uts.random_name()
		filename = '90%s' % uts.random_name()
		data = '# schema test'
		try:
			schema = udm.create_object('settings/ldapschema', name=schema_name, filename=filename, data=base64.b64encode(data.encode('UTF-8')).decode('ASCII'))
		except udm_test.UCSTestUDM_CreateUDMObjectFailed:
			pass
		else:
			utils.fail('settings/ldapschema object with invalid data was created')

		schema_name = uts.random_name()
		filename = '90%s' % uts.random_name()
		data = '# schema test'
		try:
			schema = udm.create_object('settings/ldapschema', name=schema_name, filename=filename, data=base64.b64encode(bz2.compress(data.encode('UTF-8'))).decode('ASCII'), active='YES')
		except udm_test.UCSTestUDM_CreateUDMObjectFailed:
			pass
		else:
			utils.fail('settings/ldapschema object with invalid active attribute was created')
