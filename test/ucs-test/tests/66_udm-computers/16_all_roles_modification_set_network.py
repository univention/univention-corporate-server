#!/usr/share/ucs-test/runner pytest-3 -s -l -vv

## desc: Test setting network during modification for all computer roles
## tags: [udm-computers, SKIP]
## roles: [domaincontroller_master]
## exposure: careful
## bugs: [15758,31832]
## packages:
##   - univention-config
##   - univention-directory-manager-tools

import ipaddress

import pytest

import univention.testing.udm as udm_test
from univention.testing.strings import random_name, random_string

COMPUTER_MODULES = udm_test.UCSTestUDM.COMPUTER_MODULES


@pytest.mark.skip(reason=" disabled since 2014, issues when running on AWS instances. See Bug #37365 git:8666c032e7e.")
@pytest.mark.tags('udm-computers')
@pytest.mark.roles('domaincontroller_master')
@pytest.mark.exposure('careful')
@pytest.mark.parametrize('role', COMPUTER_MODULES)
@pytest.mark.parametrize('ip_subnet,ip_network,ip_netmask,ip_range', [
	('10.20.30', '10.20.30.0', '24', '10.20.30.2 10.20.30.254'),
	('2001:0001:0002:0003', '2001:1:2:3::', '64', '2001:1:2:3::2 2001:1:2:3:0:ffff:ffff:ffff'),
])
class Test_ComputerAllRoles():
	def test_all_roles_modification_set_network(self, udm, ucr, lo, verify_ldap_object, role, ip_subnet, ip_network, ip_netmask, ip_range):
			"""Test setting network during modification for all computer roles"""
			# bugs: [15758,31832]

			computerProperties = {
				'mac': '01:23:45:67:89:ab',
				'name': random_name()
			}

			dNSCn = 'cn=dns,%s' % (ucr.get('ldap/base'),)

			forwardZoneName = '%s.%s' % (random_name(), random_name())
			forwardZone = udm.create_object('dns/forward_zone', zone=forwardZoneName, position=dNSCn, nameserver=random_string(numeric=False))
			reverseZone = udm.create_object('dns/reverse_zone', subnet=ip_subnet, position=dNSCn, nameserver=random_string(numeric=False))
			dhcpService = udm.create_object('dhcp/service', service=random_name())

			networkProperties = {
				'name': random_name(),
				'network': ip_network,
				'netmask': ip_netmask,
				'dnsEntryZoneForward': forwardZone,
				'dnsEntryZoneReverse': reverseZone,
				'dhcpEntryZone': dhcpService,
				'ipRange': ip_range,
			}
			network = udm.create_object('networks/network', **networkProperties)

			computer = udm.create_object(role, **computerProperties)
			udm.modify_object(role, dn=computer, network=network)
			aRecord = (lo.getAttr(computer, 'aRecord') or [b''])[0].decode('ASCII')
			aaaRecord = (lo.getAttr(computer, 'aAAARecord') or [b''])[0].decode('ASCII')

			# FIXME: workaround for possibly remaining locks
			if aaaRecord:
				udm.addCleanupLock('aAAARecord', aaaRecord)
			if aRecord:
				udm.addCleanupLock('aRecord', aRecord)
			udm.addCleanupLock('mac', '01:23:45:67:89:ab')

			verify_ldap_object(computer, {'univentionNetworkLink': [network]})
			assert aRecord or aaaRecord

			if aRecord:
				assert aRecord in ['%s.%s' % (ip_subnet, oktett) for oktett in range(2, 255)], 'IP address of computer not in range of its network'

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

			if aaaRecord:
				assert aaaRecord in ['%s:0000:0000:0000:%0.4x' % (ip_subnet, oktett) for oktett in range(2, 255)], 'IP address of computer not in range of its network'

				verify_ldap_object(
					'relativeDomainName=%s,%s' % (computerProperties['name'], forwardZone),
					{'aAAARecord': [aaaRecord]}
				)
				verify_ldap_object(
					'relativeDomainName=%s,%s' % ('.'.join(reversed(''.join(aaaRecord.split(':')[4:]))), reverseZone),
					{'pTRRecord': ['%s.%s.' % (computerProperties['name'], forwardZoneName)]}
				)
				verify_ldap_object(
					'cn=%s,%s' % (computerProperties['name'], dhcpService),
					{'univentionDhcpFixedAddress': [str(ipaddress.IPv6Address(aaaRecord))]}
				)
