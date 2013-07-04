#!/usr/share/ucs-test/runner python
## desc: Check if IP and MAC address locks are removed after computer creation and modification for all computer roles
## tags: [udm-computers]
## roles: [domaincontroller_master]
## bugs: [15743]
## exposure: careful
## packages:
##   - univention-config
##   - univention-directory-manager-tools


import univention.testing.udm as udm_test
import univention.testing.strings as uts
import univention.testing.utils as utils
import univention.config_registry as configRegistry


if __name__ == '__main__':
	ucr = configRegistry.ConfigRegistry()
	ucr.load()

	properties = {
		'ip': '10.20.30.40',
		'mac': '01:23:45:67:89:ab'
	}

	newProperties = {
		'ip': '10.20.30.41',
		'mac': '01:23:45:67:89:ac'
	}

	lockContainer = 'cn=temporary,cn=univention,%s' % ucr['ldap/base']

	for role in udm_test.UCSTestUDM.COMPUTER_MODULES:
		with udm_test.UCSTestUDM() as udm:
			computer = udm.create_object(role, name = uts.random_name(), **properties)
			if utils.verify_ldap_object('cn=%s,cn=aRecord,%s' % (properties['ip'], lockContainer)):
				utils.fail('Could still find lock for IP %s after creation of %s' % (properties['ip'], role))
			if utils.verify_ldap_object('cn=%s,cn=mac,%s' % (properties['mac'], lockContainer)):
				utils.fail('Could still find lock for MAC %s after creation of %s' % (properties['mac'], role))

			udm.modify_object(role, dn = computer, **newProperties)
			if utils.verify_ldap_object('cn=%s,cn=aRecord,%s' % (newProperties['ip'], lockContainer)):
				utils.fail('Could still find lock for IP %s after creation of %s' % (newProperties['ip'], role))
			if utils.verify_ldap_object('cn=%s,cn=mac,%s' % (newProperties['mac'], lockContainer)):
				utils.fail('Could still find lock for MAC %s after creation of %s' % (newProperties['mac'], role))
