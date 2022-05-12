#!/usr/share/ucs-test/runner python3
## desc: Removing one of multiple DNS PTR RR works
## tags: [udm-computers]
## roles: [domaincontroller_master]
## bugs: [53204]
## exposure: careful
## packages:
##   - univention-config
##   - univention-directory-manager-tools

import pytest

from univention.testing import utils
from univention.testing.strings import random_name, random_string

MAC = '00:11:22:33:44:55'


@pytest.mark.tags('udm-computers')
@pytest.mark.roles('domaincontroller_master')
@pytest.mark.exposure('careful')
def test_create_empty_dhcp(udm):
		computerName = random_string()

		service = udm.create_object('dhcp/service', service=random_name())

		udm.create_object(
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
			assert val != b'', "dhp/entry with univentionDhcpFixedAddress:['']"
		except (LookupError, ValueError):
			pass
