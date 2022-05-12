#!/usr/share/ucs-test/runner python3
## desc: Validate handling of "ntCompatibility" attribute in computers/windows module
## tags: [udm-computers]
## roles: [domaincontroller_master]
## exposure: careful
## packages:
##   - univention-config
##   - univention-directory-manager-tools

import passlib.hash

import univention.testing.strings as uts
import univention.testing.udm as udm_test
import univention.testing.utils as utils

if __name__ == '__main__':
	windowsHostName = uts.random_string()
	with udm_test.UCSTestUDM() as udm:
		utils.verify_ldap_object(udm.create_object('computers/windows', name=windowsHostName, ntCompatibility='1'), {'sambaNTPassword': [passlib.hash.nthash.hash(windowsHostName.lower()).upper()]})
