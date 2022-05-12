#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: Validate adoption of network properties during creation for all computer roles
## tags: [udm-computers, SKIP]
## roles: [domaincontroller_master]
## exposure: careful
## bugs: [15758]
## packages:
##   - univention-config
##   - univention-directory-manager-tools

import pytest

from univention.testing.strings import random_name, random_string
from univention.testing.udm import UCSTestUDM

COMPUTER_MODULES = UCSTestUDM.COMPUTER_MODULES
COMPUTER_MODULES_EXCEPT_MACOS = [i for i in COMPUTER_MODULES if i != 'computers/macos']


@pytest.mark.skip(reason="Fails due to a bug in the UDM-CLI, see Bug #25163. Issues when running on AWS instances, see Bug #37365 git:8666c032e7e")
@pytest.mark.tags('udm-computers')
@pytest.mark.roles('domaincontroller_master')
@pytest.mark.exposure('careful')
@pytest.mark.parametrize('role', COMPUTER_MODULES_EXCEPT_MACOS)
class Test_ComputerAllRoles():
	def test_all_roles_creation_set_network(self, udm, ucr, verify_ldap_object, lo, role):
			"""Validate adoption of network properties during creation for all computer roles"""
			# bugs: [15758]

			computerProperties = {
				'mac': '01:23:45:67:89:ab',
				'name': random_name()
			}

			dNSCn = 'cn=dns,%s' % (ucr.get('ldap/base'),)

			forwardZoneName = '%s.%s' % (random_name(), random_name())

			forwardZone = udm.create_object('dns/forward_zone', zone=forwardZoneName, position=dNSCn, nameserver=random_string(numeric=False))
			reverseZone = udm.create_object('dns/reverse_zone', subnet='10.20.30', position=dNSCn, nameserver=random_string(numeric=False))
			dhcpService = udm.create_object('dhcp/service', service=random_name())
			networkProperties = {
				'name': random_name(),
				'network': '10.20.30.0',
				'netmask': '24',
				'dnsEntryZoneForward': forwardZone,
				'dnsEntryZoneReverse': reverseZone,
				'dhcpEntryZone': dhcpService,
				'ipRange': '10.20.30.2 10.20.30.254'
			}
			network = udm.create_object('networks/network', **networkProperties)

			computer = udm.create_object(role, network=network, **computerProperties)
			aRecord = lo.getAttr(computer, 'aRecord')[0].decode('ASCII')

			# FIXME: workaround for remaining locks
			udm.addCleanupLock('aRecord', aRecord)
			udm.addCleanupLock('mac', '01:23::89:ab')

			# verify that properties have been adopted correctly during creation
			verify_ldap_object(computer, {'univentionNetworkLink': [network]})

			assert aRecord in ['10.20.30.%s' % str(oktett) for oktett in range(2, 255)], "IP address of computer not in range of it's network"

			verify_ldap_object(
				'relativeDomainName=%s,%s' % (computerProperties['name'], forwardZone),
				{'aRecord': [aRecord]}
			)

			verify_ldap_object(
				'relativeDomainName=%s,%s' % (aRecord.split(".")[-1], reverseZone),
				{'pTRRecord': ['%s.%s.' % (computerProperties['name'], forwardZoneName)]}
			)

			verify_ldap_object(
				'cn=%s,%s' % (computerProperties['name'], dhcpService),
				{'univentionDhcpFixedAddress': [aRecord]}
			)
