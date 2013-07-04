#!/usr/share/ucs-test/runner python
## desc: Test modifying inventoryNumber for all computer roles
## tags: [udm-computers]
## roles: [domaincontroller_master]
## exposure: careful
## packages:
##   - univention-config
##   - univention-directory-manager-tools


import univention.testing.udm as udm_test
import univention.testing.strings as uts
import univention.testing.utils as utils


if __name__ == '__main__':
	inventoryNumber = uts.random_string()
	
	with udm_test.UCSTestUDM() as udm:
		for role in udm.COMPUTER_MODULES:
			computer = udm.create_object(role, name = uts.random_name())
			udm.modify_object(role, dn = computer, inventoryNumber = inventoryNumber)
			if not utils.verify_ldap_object(computer, {'univentionInventoryNumber': [inventoryNumber]}):
				utils.fail('"univentionInventoryNumber" of %s differed from expectation after modification')
