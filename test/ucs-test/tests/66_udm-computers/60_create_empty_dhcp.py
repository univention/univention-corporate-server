#!/usr/share/ucs-test/runner python3
## desc: Removing one of multiple DNS PTR RR works
## tags: [udm-computers]
## roles: [domaincontroller_master]
## bugs: [53204]
## exposure: careful
## packages:
##   - univention-config
##   - univention-directory-manager-tools

import univention.testing.strings as uts
import univention.testing.udm as udm_test
import univention.testing.utils as utils

MAC = '00:11:22:33:44:55'


if __name__ == '__main__':
	computerName = uts.random_string()

	with udm_test.UCSTestUDM() as udm:
		service = udm.create_object('dhcp/service', service=uts.random_name())

		computer = udm.create_object(
			'computers/ipmanagedclient',
			name=computerName,
			mac=[MAC],
			dhcpEntryZone=['%s %s %s' % (service, '', MAC)],
		)

		host = 'cn=%s,%s' % (computerName, service)
		((dn, attr),) = udm._lo.search(
			filter='(objectClass=*)',
			base=host,
			scope=utils.ldap.SCOPE_BASE,
			attr=["univentionDhcpFixedAddress"],
		)
		try:
			vals = attr["univentionDhcpFixedAddress"]
			val, = vals
			if val == b'':
				utils.fail("dhp/entry with univentionDhcpFixedAddress:['']")
		except (LookupError, ValueError):
			pass
