#!/usr/share/ucs-test/runner python
## desc: Test appending and removing IP addresses for all computer roles
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
	ipAddresses = ('10.20.30.40', '10.20.30.41', '10.20.30.42', '10.20.30.43')
	
	for role in udm_test.UCSTestUDM.COMPUTER_MODULES:
		with udm_test.UCSTestUDM() as udm:
			for ip in ipAddresses: #FIXME: workaround for remaining locks
				udm.addCleanupLock('aRecord', ip)

			computer = udm.create_object(role, name = uts.random_name(), append = {'ip': ipAddresses[:2]})
			if not utils.verify_ldap_object(computer, {'aRecord': ipAddresses[:2]}):
				utils.fail('"aRecord" of %s differed from expectation after trying to append %r during creation' % (role, ipAddresses[:2]))

			udm.modify_object(role, dn = computer, append = {'ip': ipAddresses[2:]})
			if not utils.verify_ldap_object(computer, {'aRecord': ipAddresses}):
				utils.fail('"aRecord" of %s differed from expectation after trying to append %r during modification' % (role, ipAddresses[2:]))

			udm.modify_object(role, dn = computer, remove = {'ip': ipAddresses[:2]})
			if not utils.verify_ldap_object(computer, {'aRecord': ipAddresses[2:]}):
				utils.fail('"aRecord" of %s differed from expectation after trying to remove %r during modification' % (role, ipAddresses[:2]))
