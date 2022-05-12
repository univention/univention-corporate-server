#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: Create object with all attributes set for all computer roles
## tags: [udm-computers,apptest]
## roles: [domaincontroller_master]
## exposure: careful
## packages:
##   - univention-config
##   - univention-directory-manager-tools

import random

import passlib.hash
import pytest

import univention.testing.udm as udm_test
from univention.testing import utils
from univention.testing.strings import random_name, random_string

COMPUTER_MODULES = udm_test.UCSTestUDM.COMPUTER_MODULES
COMPUTER_MODULES_EXCEPT_MACOS = [i for i in COMPUTER_MODULES if i != 'computers/macos']


@pytest.fixture
def stopped_s4connector():
	if utils.s4connector_present():
		utils.stop_s4connector()
		yield
		utils.start_s4connector()
	else:
		yield


class Test_ComputerAllRoles():
	@pytest.mark.tags('udm-computers', 'apptest')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	@pytest.mark.parametrize(
		'role,rand_ip,rand_mac',
		list(zip(
			COMPUTER_MODULES_EXCEPT_MACOS,
			# get random, but unique IP and MAC endings Bug #38212:
			random.sample(range(5, 19), 9),  # will be used for IP endings
			random.sample(range(20, 99), 9),  # will be used for MAC endings
		))
	)
	def test_all_roles_creation_with_all_attributes(self, ucr, udm, verify_ldap_object, lo, stopped_s4connector, role, rand_ip, rand_mac):
			"""Create object with all attributes set for all computer roles"""

			dhcpZone = udm.create_object('dhcp/service', service=random_name())

			properties = {
				'name': random_name(),
				'description': random_string(),
				'mac': '01:23:45:67:89:%s' % rand_mac,
				'network': udm.create_object('networks/network', name=random_name(), network='10.20.30.0', netmask='24'),
				'ip': '10.20.30.%s' % rand_ip,
				'dnsEntryZoneForward': udm.create_object('dns/forward_zone', zone='%s.%s' % (random_name(), random_name()), nameserver=random_string(numeric=False)),
				'dnsEntryZoneReverse': udm.create_object('dns/reverse_zone', subnet='10.20.30', nameserver=random_string(numeric=False)),
				'inventoryNumber': random_string(),
				'domain': '%s.%s' % (random_name(), random_name())
			}
			properties['dhcpEntryZone'] = '%s %s %s' % (dhcpZone, properties['ip'], properties['mac'])

			expectedLdap = {
				'cn': [properties['name']],
				'sn': [properties['name']],
				'description': [properties['description']],
				'macAddress': [properties['mac']],
				'univentionNetworkLink': [properties['network']],
				'aRecord': [properties['ip']],
				'univentionInventoryNumber': [properties['inventoryNumber']],
				'associatedDomain': [properties['domain']]
			}

			if role != 'computers/ipmanagedclient':
				properties['password'] = random_string()
				properties['unixhome'] = '/home/'
				properties['shell'] = random_string()
				properties['primaryGroup'] = udm.create_group(check_for_drs_replication=False)[0]
				properties['groups'] = [udm.create_group(check_for_drs_replication=False)[0], udm.create_group(check_for_drs_replication=False)[0]]
				expectedLdap['gidNumber'] = lo.search(base=properties['primaryGroup'], attr=['gidNumber'])[0][1].get('gidNumber', [])
				expectedLdap['loginShell'] = [properties['shell']]
				expectedLdap['sambaPrimaryGroupSID'] = [lo.getAttr(properties['primaryGroup'], 'sambaSID')[0]]
				expectedLdap['homeDirectory'] = [properties['unixhome']]
				expectedLdap['uid'] = ['%s$' % properties['name']]
				expectedLdap['displayName'] = [properties['name']]
				expectedLdap['sambaNTPassword'] = [passlib.hash.nthash.hash(properties['password'].lower()).upper()]
				expectedLdap['krb5PrincipalName'] = [b'host/%s.%s@%s' % (properties['name'].encode('UTF-8'), properties['domain'].lower().encode('UTF-8'), lo.getAttr(ucr['ldap/base'], 'krb5RealmName')[0])]

			if role not in ('computers/domaincontroller_master', 'computers/domaincontroller_backup', 'computers/domaincontroller_slave', 'computers/memberserver', 'computers/ipmanagedclient'):
				properties['operatingSystem'] = random_string()
				properties['operatingSystemVersion'] = random_string()
				expectedLdap['univentionOperatingSystem'] = [properties['operatingSystem']]
				expectedLdap['univentionOperatingSystemVersion'] = [properties['operatingSystemVersion']]

			# create object
			computer_DN = udm.create_object(role, **properties)

			# FIXME: workaround for remaining locks
			udm.addCleanupLock('aRecord', lo.getAttr(computer_DN, 'aRecord')[0].decode('ASCII'))
			udm.addCleanupLock('mac', lo.getAttr(computer_DN, 'macAddress')[0].decode('ASCII'))

			# validate computer ldap object
			verify_ldap_object(computer_DN, expectedLdap)

			# validate related DHCP host object
			verify_ldap_object('cn=%s,%s' % (properties['name'], dhcpZone), {
				'dhcpHWAddress': ['ethernet %s' % properties['mac']],
				'univentionDhcpFixedAddress': [properties['ip']]
			})

			# validate related A record
			verify_ldap_object('relativeDomainName=%s,%s' % (properties['name'], properties['dnsEntryZoneForward']), {
				'aRecord': [properties['ip']],
				'relativeDomainName': [properties['name']],
				'zoneName': [properties['dnsEntryZoneForward'].split('zoneName=')[1].split(',')[0]]
			})

			# validate related PTR record
			verify_args = ('relativeDomainName=%s,%s' % (rand_ip, properties['dnsEntryZoneReverse']), {
				'relativeDomainName': [str(rand_ip)],
				'pTRRecord': ['%s.%s.' % (properties['name'], properties['dnsEntryZoneForward'].split('zoneName=')[1].split(',')[0])],
				'zoneName': [properties['dnsEntryZoneReverse'].split('zoneName=')[1].split(',')[0]]
			})
			print(f'\n\nverify_args: \n{verify_args}\n')
			verify_ldap_object(*verify_args)

			if role != 'computers/ipmanagedclient':
				# validate computer sambaSID
				computer_sambaSID = lo.getAttr(computer_DN, 'sambaSID')[0].decode('ASCII')
				udm.addCleanupLock('sid', computer_sambaSID)
				if utils.s4connector_present():
					assert computer_sambaSID.startswith('S-1-4'), '"sambaSID" of %s did not start with "S-1-4-" as expected' % computer_DN
				else:
					sambaDomainSID = lo.search(filter='objectClass=sambaDomain', attr=['sambaSID'])[0][1]['sambaSID'][0].decode('ASCII')
					assert computer_sambaSID.startswith(sambaDomainSID), '"sambaSID" of %s did not start with "%s" as expected' % (computer_DN, sambaDomainSID)

				# validate group memberships
				for group in [properties['primaryGroup']] + properties['groups']:
					verify_ldap_object(group, {'memberUid': ['%s$' % properties['name']], 'uniqueMember': [computer_DN]})
