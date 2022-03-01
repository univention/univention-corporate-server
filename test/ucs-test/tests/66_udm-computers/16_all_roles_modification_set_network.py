#!/usr/share/ucs-test/runner /usr/bin/py.test -s
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

import univention.config_registry as configRegistry
import univention.testing.strings as uts
import univention.testing.udm as udm_test
import univention.testing.utils as utils


@pytest.mark.parametrize('ip_subnet,ip_network,ip_netmask,ip_range', [
	('10.20.30', '10.20.30.0', '24', '10.20.30.2 10.20.30.254'),
	('2001:0001:0002:0003', '2001:1:2:3::', '64', '2001:1:2:3::2 2001:1:2:3:0:ffff:ffff:ffff'),
])
def test_all_roles_modification_set_network(ip_subnet, ip_network, ip_netmask, ip_range):
	ucr = configRegistry.ConfigRegistry()
	ucr.load()

	for role in udm_test.UCSTestUDM.COMPUTER_MODULES:
		computerProperties = {
			'mac': '01:23:45:67:89:ab',
			'name': uts.random_name()
		}

		with udm_test.UCSTestUDM() as udm:
			dNSCn = 'cn=dns,%s' % (ucr.get('ldap/base'),)

			forwardZoneName = '%s.%s' % (uts.random_name(), uts.random_name())
			forwardZone = udm.create_object('dns/forward_zone', zone=forwardZoneName, position=dNSCn, nameserver=uts.random_string(numeric=False))
			reverseZone = udm.create_object('dns/reverse_zone', subnet=ip_subnet, position=dNSCn, nameserver=uts.random_string(numeric=False))
			dhcpService = udm.create_object('dhcp/service', service=uts.random_name())

			networkProperties = {
				'name': uts.random_name(),
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
			aRecord = (utils.get_ldap_connection().getAttr(computer, 'aRecord') or [b''])[0].decode('ASCII')
			aaaRecord = (utils.get_ldap_connection().getAttr(computer, 'aAAARecord') or [b''])[0].decode('ASCII')

			# FIXME: workaround for possibly remaining locks
			if aaaRecord:
				udm.addCleanupLock('aAAARecord', aaaRecord)
			if aRecord:
				udm.addCleanupLock('aRecord', aRecord)
			udm.addCleanupLock('mac', '01:23:45:67:89:ab')

			utils.verify_ldap_object(computer, {'univentionNetworkLink': [network]})
			assert aRecord or aaaRecord
			if aRecord:
				assert aRecord in ['%s.%s' % (ip_subnet, oktett) for oktett in range(2, 255)], 'IP address of computer not in range of its network'
			if aaaRecord:
				assert aaaRecord in ['%s:0000:0000:0000:%0.4x' % (ip_subnet, oktett) for oktett in range(2, 255)], 'IP address of computer not in range of its network'
			if aRecord:
				utils.verify_ldap_object('relativeDomainName=%s,%s' % (computerProperties['name'], forwardZone), {'aRecord': [aRecord]})
				utils.verify_ldap_object('relativeDomainName=%s,%s' % (aRecord.split(".")[-1], reverseZone), {'pTRRecord': ['%s.%s.' % (computerProperties['name'], forwardZoneName)]})
				utils.verify_ldap_object('cn=%s,%s' % (computerProperties['name'], dhcpService), {'univentionDhcpFixedAddress': [aRecord]})
			if aaaRecord:
				utils.verify_ldap_object('relativeDomainName=%s,%s' % (computerProperties['name'], forwardZone), {'aAAARecord': [aaaRecord]})
				utils.verify_ldap_object('relativeDomainName=%s,%s' % ('.'.join(reversed(''.join(aaaRecord.split(':')[4:]))), reverseZone), {'pTRRecord': ['%s.%s.' % (computerProperties['name'], forwardZoneName)]})
				utils.verify_ldap_object('cn=%s,%s' % (computerProperties['name'], dhcpService), {'univentionDhcpFixedAddress': [str(ipaddress.IPv6Address(aaaRecord))]})
