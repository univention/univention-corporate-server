#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: Test all role modifications of udm
## tags: [udm-computers,apptest]
## roles: [domaincontroller_master]
## exposure: careful
## packages:
##   - univention-config
##   - univention-directory-manager-tools

import ipaddress
import time
from random import choice

import pytest

import ldap.dn
import passlib.hash

from univention import uldap
from univention.testing.decorators import SetTimeout
from univention.testing import utils

from univention.testing.strings import random_name, random_string

from univention.testing.udm import UCSTestUDM


@pytest.fixture
def cleanup():
	if utils.s4connector_present():
		utils.stop_s4connector()
		yield
		utils.start_s4connector()
	else:
		yield


class Test_UDMAllRoles:

	COMPUTER_MODULES = UCSTestUDM.COMPUTER_MODULES
	COMPUTER_MODULES_EXCEPT_MACOS = [i for i in COMPUTER_MODULES if i != 'computers/macos']
	COMPUTER_MODULES_EXCEPT_IPMANAGEDCLIENT = [i for i in COMPUTER_MODULES if i != 'computers/ipmanagedclient']

	@pytest.mark.tags('udm-computers', 'apptest')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	@pytest.mark.parametrize('role', COMPUTER_MODULES)
	def test_all_roles_creation(self, udm, role):
		"""Create minimal object for all computer roles"""
		computer = udm.create_object(role, name=random_string())
		utils.verify_ldap_object(computer)

	utils.verify_ldap_object = SetTimeout(utils.verify_ldap_object)

	@pytest.mark.tags('udm-computers')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	@pytest.mark.parametrize('role', COMPUTER_MODULES)
	def test_all_role_removal(self, udm, role):
		"""Remove object for all computer roles"""
		computer = udm.create_object(role, name=random_string())
		udm.remove_object(role, dn=computer)

		utils.verify_ldap_object(computer, should_exist=False)

	available_ip_nums = list(range(1, 10))  # will be used for IP endings
	available_mac_nums = list(range(11, 99))  # will be used for MAC endings

	@pytest.mark.tags('udm-computers', 'apptest')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	@pytest.mark.parametrize('role', COMPUTER_MODULES_EXCEPT_MACOS)
	def test_all_roles_creation_with_all_attributes(self, ucr, udm, lo, role, cleanup):
		"""Create object with all attributes set for all computer roles"""

		dhcpZone = udm.create_object('dhcp/service', service=random_name())

		# get random, but unique IP and MAC endings Bug #38212:
		rand_ip = choice(self.available_ip_nums)
		self.available_ip_nums.remove(rand_ip)  # so it won't be used again
		rand_mac = choice(self.available_mac_nums)
		self.available_mac_nums.remove(rand_mac)  # so it won't be used again

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
		utils.verify_ldap_object(computer_DN, expectedLdap)

		# validate related DHCP host object
		utils.verify_ldap_object('cn=%s,%s' % (properties['name'], dhcpZone), {
			'dhcpHWAddress': ['ethernet %s' % properties['mac']],
			'univentionDhcpFixedAddress': [properties['ip']]
		})

		# validate related A record
		utils.verify_ldap_object('relativeDomainName=%s,%s' % (properties['name'], properties['dnsEntryZoneForward']), {
			'aRecord': [properties['ip']],
			'relativeDomainName': [properties['name']],
			'zoneName': [properties['dnsEntryZoneForward'].split('zoneName=')[1].split(',')[0]]
		})

		# validate related PTR record
		utils.verify_ldap_object('relativeDomainName=%s,%s' % (rand_ip, properties['dnsEntryZoneReverse']), {
			'relativeDomainName': str(rand_ip),
			'pTRRecord': ['%s.%s.' % (properties['name'], properties['dnsEntryZoneForward'].split('zoneName=')[1].split(',')[0])],
			'zoneName': [properties['dnsEntryZoneReverse'].split('zoneName=')[1].split(',')[0]]
		})

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
				utils.verify_ldap_object(group, {'memberUid': ['%s$' % properties['name']], 'uniqueMember': [computer_DN]})

	@pytest.mark.tags('udm-computers')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	@pytest.mark.parametrize('role', COMPUTER_MODULES)
	def test_all_roles_check_nagios(self, udm, lo, role):
		"""Validate nagios for all computer roles"""

		forwardZone = udm.create_object('dns/forward_zone', zone='%s.%s' % (random_name(), random_name()), nameserver=random_string(numeric=False))
		nagiosService = udm.create_object('nagios/service', name=random_name(), checkCommand=random_string(), checkPeriod=random_string(), notificationPeriod=random_string())

		nagiosParentProperties = {
			'options': ['nagios'],
			'name': random_name(),
			'ip': '10.20.30.2'
		}
		# FIXME: workaround for remaining locks
		udm.addCleanupLock('aRecord', nagiosParentProperties['ip'])

		computerProperties = {
			'dnsEntryZoneForward': forwardZone,
			'nagiosServices': nagiosService,
			'nagiosContactEmail': '%s@%s.%s' % (random_name(), random_name(), random_name()),
			'nagiosParents': udm.create_object('computers/domaincontroller_backup', dnsEntryZoneForward=forwardZone, **nagiosParentProperties),
			'name': random_name(),
			'ip': '10.20.30.3',
			'options': ['posix', 'nagios']
		}
		# FIXME: workaround for remaining locks
		udm.addCleanupLock('aRecord', computerProperties['ip'])

		computer = udm.create_object(role, wait_for=True, **computerProperties)

		# validate that nagios related properties of computer are set correctly
		utils.verify_ldap_object(computer, {
			'univentionNagiosEmail': [computerProperties['nagiosContactEmail']],
			'univentionNagiosEnabled': ['1'],
			'univentionNagiosParent': [b'%s.%s' % (nagiosParentProperties['name'].encode('UTF-8'), lo.getAttr(computerProperties['nagiosParents'], 'associatedDomain')[0])]
		})

		# check if computer has been added to nagios service
		utils.verify_ldap_object(nagiosService, {'univentionNagiosHostname': [b'%s.%s' % (computerProperties['name'].encode('UTF-8'), lo.getAttr(computer, 'associatedDomain')[0])]})

	# This test was disabled since 2014 due to issues when running on aws instaces
	# For further information, see Bug #37365 and commit 8666c032e7e
	@pytest.mark.skip(reason="")
	@pytest.mark.tags('udm-computers')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	@pytest.mark.parametrize('role', COMPUTER_MODULES)
	@pytest.mark.parametrize('ip_subnet,ip_network,ip_netmask,ip_range', [
		('10.20.30', '10.20.30.0', '24', '10.20.30.2 10.20.30.254'),
		('2001:0001:0002:0003', '2001:1:2:3::', '64', '2001:1:2:3::2 2001:1:2:3:0:ffff:ffff:ffff'),
	])
	def test_all_roles_modification_set_network(self, udm, ucr, lo, role, ip_subnet, ip_network, ip_netmask, ip_range):
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

		utils.verify_ldap_object(computer, {'univentionNetworkLink': [network]})
		assert aRecord or aaaRecord

		if aRecord:
			assert aRecord in ['%s.%s' % (ip_subnet, oktett) for oktett in range(2, 255)], 'IP address of computer not in range of its network'

			utils.verify_ldap_object(
				'relativeDomainName=%s,%s' % (computerProperties['name'], forwardZone),
				{'aRecord': [aRecord]}
			)
			utils.verify_ldap_object(
				'relativeDomainName=%s,%s' % (aRecord.split(".")[-1], reverseZone),
				{'pTRRecord': ['%s.%s.' % (computerProperties['name'], forwardZoneName)]}
			)
			utils.verify_ldap_object(
				'cn=%s,%s' % (computerProperties['name'], dhcpService),
				{'univentionDhcpFixedAddress': [aRecord]}
			)

		if aaaRecord:
			assert aaaRecord in ['%s:0000:0000:0000:%0.4x' % (ip_subnet, oktett) for oktett in range(2, 255)], 'IP address of computer not in range of its network'

			utils.verify_ldap_object(
				'relativeDomainName=%s,%s' % (computerProperties['name'], forwardZone),
				{'aAAARecord': [aaaRecord]}
			)
			utils.verify_ldap_object(
				'relativeDomainName=%s,%s' % ('.'.join(reversed(''.join(aaaRecord.split(':')[4:]))), reverseZone),
				{'pTRRecord': ['%s.%s.' % (computerProperties['name'], forwardZoneName)]}
			)
			utils.verify_ldap_object(
				'cn=%s,%s' % (computerProperties['name'], dhcpService),
				{'univentionDhcpFixedAddress': [str(ipaddress.IPv6Address(aaaRecord))]}
			)

	@pytest.mark.tags('udm-computers')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	@pytest.mark.parametrize('role', COMPUTER_MODULES)
	def test_all_roles_ip_and_mac_lock_removal(self, udm, ucr, role):
		"""Check if IP and MAC address locks are removed after computer creation and modification for all computer roles"""
		# bugs: [15743]
		properties = {
			'ip': '10.20.30.40',
			'mac': '01:23:45:67:89:ab'
		}

		newProperties = {
			'ip': '10.20.30.41',
			'mac': '01:23:45:67:89:ac'
		}

		lockContainer = 'cn=temporary,cn=univention,%s' % ucr['ldap/base']

		computer = udm.create_object(role, name=random_name(), **properties)
		utils.verify_ldap_object('cn=%s,cn=aRecord,%s' % (properties['ip'], lockContainer), should_exist=False)
		utils.verify_ldap_object('cn=%s,cn=mac,%s' % (properties['mac'], lockContainer), should_exist=False)

		udm.modify_object(role, dn=computer, **newProperties)
		utils.verify_ldap_object('cn=%s,cn=aRecord,%s' % (newProperties['ip'], lockContainer), should_exist=False)
		utils.verify_ldap_object('cn=%s,cn=mac,%s' % (newProperties['mac'], lockContainer), should_exist=False)

	@pytest.mark.tags('udm-computers', 'apptest')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	@pytest.mark.parametrize('role', COMPUTER_MODULES)
	def test_all_roles_modification_append_macs(self, udm, role):
		"""Append macs during modification for all computer roles"""
		macAddresses = ['11:11:11:11:11:11', '22:22:22:22:22:22']

		for mac in macAddresses:  # FIXME: workaround for remaining locks
			udm.addCleanupLock('mac', mac)

		computer = udm.create_object(role, name=random_name())

		udm.modify_object(role, dn=computer, append={'mac': macAddresses[:2]})
		utils.verify_ldap_object(computer, {'macAddress': macAddresses})

	@pytest.mark.tags('udm-computers')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	@pytest.mark.parametrize('role', COMPUTER_MODULES)
	def test_all_roles_modification_set_inventoryNumber(self, udm, role):
		"""Test setting inventoryNumber during modification for all computer roles"""
		inventoryNumber = random_string()

		computer = udm.create_object(role, name=random_name())
		udm.modify_object(role, dn=computer, inventoryNumber=inventoryNumber)
		utils.verify_ldap_object(computer, {'univentionInventoryNumber': [inventoryNumber]})

	@pytest.mark.tags('udm-computers', 'apptest')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	@pytest.mark.parametrize('role', COMPUTER_MODULES)
	def test_all_roles_modification_append_and_remove_ip(self, udm, role):
		"""Test appending and removing IP addresses for all computer roles"""
		ipAddresses = ('10.20.30.40', '10.20.30.41', '10.20.30.42', '10.20.30.43')
		for ip in ipAddresses:  # FIXME: workaround for remaining locks
			udm.addCleanupLock('aRecord', ip)

		computer = udm.create_object(role, name=random_name(), append={'ip': ipAddresses[:2]})
		utils.verify_ldap_object(computer, {'aRecord': ipAddresses[:2]})

		udm.modify_object(role, dn=computer, append={'ip': ipAddresses[2:]})
		utils.verify_ldap_object(computer, {'aRecord': ipAddresses})

		udm.modify_object(role, dn=computer, remove={'ip': ipAddresses[:2]})
		utils.verify_ldap_object(computer, {'aRecord': ipAddresses[2:]})

	@pytest.mark.tags('udm-computers')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	@pytest.mark.parametrize('role', COMPUTER_MODULES_EXCEPT_IPMANAGEDCLIENT)
	def test_all_roles_modification_append_and_remove_groups(self, udm, role):
		"""Test appending and removing groups for all computer roles (except computers/ipmanagedclient)"""

		groups = (udm.create_group()[0], udm.create_group()[0], udm.create_group()[0], udm.create_group()[0])

		computerName = random_name()
		computer = udm.create_object(role, name=computerName)

		udm.modify_object(role, dn=computer, append={'groups': groups})
		utils.wait_for_connector_replication()
		# validate group memberships set during modification
		for group in groups:
			utils.verify_ldap_object(group, {'memberUid': ['%s$' % computerName], 'uniqueMember': [computer]})

		udm.modify_object(role, dn=computer, remove={'groups': groups[:2]})
		utils.wait_for_connector_replication()
		# validate that group memberships of groups removed during seccond modification have been decomposed
		for group in groups[:2]:
			utils.verify_ldap_object(group, {'memberUid': [], 'uniqueMember': []})

		# validate that the other group memberships are still unimpaired after seccond modification
		for group in groups[2:]:
			utils.verify_ldap_object(group, {'memberUid': ['%s$' % computerName], 'uniqueMember': [computer]})

	@pytest.mark.tags('udm-computers')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	@pytest.mark.parametrize('role', COMPUTER_MODULES)
	def test_all_roles_modification_append_and_remove_dhcpEntryZone(self, udm, role):
		"""Test appending and removing dhcpEntryZone for all computer roles"""
		computerName = random_name()

		dhcpEntryZones = (
			['%s' % udm.create_object('dhcp/service', service=random_name()), '10.20.30.40', '11:11:11:11:11:11'],
			['%s' % udm.create_object('dhcp/service', service=random_name()), '10.20.30.41', '22:22:22:22:22:22'],
			['%s' % udm.create_object('dhcp/service', service=random_name()), '10.20.30.42', '33:33:33:33:33:33'],
			['%s' % udm.create_object('dhcp/service', service=random_name()), '10.20.30.43', '44:44:44:44:44:44']
		)

		computer = udm.create_object(role, name=computerName)

		udm.modify_object(role, dn=computer, append={
			'ip': [zone[1] for zone in dhcpEntryZones],
			'mac': [zone[2] for zone in dhcpEntryZones],
			'dhcpEntryZone': [' '.join(zone) for zone in dhcpEntryZones]
		})
		for service, ip, mac in dhcpEntryZones:
			utils.verify_ldap_object('cn=%s,%s' % (computerName, service), {
				'univentionDhcpFixedAddress': [ip],
				'dhcpHWAddress': ['ethernet %s' % mac]
			})

		udm.modify_object(role, dn=computer, remove={
			'ip': [zone[1] for zone in dhcpEntryZones[:2]],
			'mac': [zone[2] for zone in dhcpEntryZones[:2]],
			'dhcpEntryZone': [' '.join(zone) for zone in dhcpEntryZones[:2]]
		})
		for service, ip, mac in dhcpEntryZones[:2]:
			utils.verify_ldap_object('cn=%s,%s' % (ldap.dn.escape_dn_chars(computerName), service), should_exist=False)

		for service, ip, mac in dhcpEntryZones[2:]:
			utils.verify_ldap_object('cn=%s,%s' % (ldap.dn.escape_dn_chars(computerName), service), {
				'univentionDhcpFixedAddress': [ip],
				'dhcpHWAddress': ['ethernet %s' % mac]
			})

	@pytest.mark.tags('udm-computers', 'apptest')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	@pytest.mark.parametrize('role', COMPUTER_MODULES)
	def test_all_roles_modification_description(self, udm, role):
		"""Test modifying description for all computer roles"""
		description = random_string()

		computer = udm.create_object(role, name=random_name())
		udm.modify_object(role, dn=computer, description=description)
		utils.verify_ldap_object(computer, {'description': [description]})

	@pytest.mark.tags('udm-computers')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	@pytest.mark.parametrize('role', COMPUTER_MODULES_EXCEPT_IPMANAGEDCLIENT)
	def test_all_roles_modification_unixhome(self, udm, role):
		"""Test modifying unixhome for all computer roles (except computers/ipmanagedclient)"""
		unixHome = '/home/'

		computer = udm.create_object(role, name=random_name())
		udm.modify_object(role, dn=computer, unixhome=unixHome)
		utils.verify_ldap_object(computer, {'homeDirectory': [unixHome]})

	@pytest.mark.tags('udm-computers')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	@pytest.mark.parametrize('role', COMPUTER_MODULES_EXCEPT_IPMANAGEDCLIENT)
	def test_all_roles_modification_set_shell(self, udm, role):
		"""Test modifying shell for all computer roles (except computers/ipmanagedclient)"""
		shell = random_string()

		computer = udm.create_object(role, name=random_name())
		udm.modify_object(role, dn=computer, shell=shell)
		utils.verify_ldap_object(computer, {'loginShell': [shell]})

	@pytest.mark.tags('udm-computers')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	@pytest.mark.parametrize('role', ('computers/domaincontroller_master', 'computers/domaincontroller_slave', 'computers/domaincontroller_backup', 'computers/memberserver'))
	def test_modify_reinstall(self, role, udm):
		"""Test modifying reinstall for computers/domaincontroller_master, computers/domaincontroller_slave, computers/domaincontroller_backup and computers/memberserver"""
		reinstall = '1'
		computer = udm.create_object(role, name=random_name())
		udm.modify_object(role, dn=computer, reinstall=reinstall)
		utils.verify_ldap_object(computer, {'univentionServerReinstall': [reinstall]})


	@pytest.mark.tags('udm-computers')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	@pytest.mark.parametrize('role', ('computers/domaincontroller_master', 'computers/domaincontroller_slave', 'computers/domaincontroller_backup', 'computers/memberserver'))
	def test_modify_instprofile(self, udm, role):
		"""Test modifying instprofile for computers/domaincontroller_master, computers/domaincontroller_slave, computers/domaincontroller_backup and computers/memberserver"""
		instprofile = random_string()

		computer = udm.create_object(role, name=random_name())
		udm.modify_object(role, dn=computer, instprofile=instprofile)
		utils.verify_ldap_object(computer, {'univentionServerInstallationProfile': [instprofile]})

	@pytest.mark.tags('udm-computers')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	@pytest.mark.parametrize('role', COMPUTER_MODULES)
	def test_all_roles_modification_append_and_remove_nagios_services(self, udm, lo, role):
		"""Test modifying nagiosServices for all computer roles"""
		nagiosServices = (
			udm.create_object('nagios/service', name=random_name(), checkCommand=random_string(), checkPeriod=random_string(), notificationPeriod=random_string()),
			udm.create_object('nagios/service', name=random_name(), checkCommand=random_string(), checkPeriod=random_string(), notificationPeriod=random_string()),
			udm.create_object('nagios/service', name=random_name(), checkCommand=random_string(), checkPeriod=random_string(), notificationPeriod=random_string()),
			udm.create_object('nagios/service', name=random_name(), checkCommand=random_string(), checkPeriod=random_string(), notificationPeriod=random_string())
		)
		computerIp = '10.20.30.2'
		computerName = random_name()

		# FIXME: workaround for remaining locks
		udm.addCleanupLock('aRecord', computerIp)

		# create computer, appending the first two nagiosServices
		computer = udm.create_object(
			role,
			options=['posix', 'nagios'],
			dnsEntryZoneForward=udm.create_object('dns/forward_zone', zone='%s.%s' % (random_name(), random_name()), nameserver=random_string(numeric=False)),
			name=computerName,
			ip=computerIp,
			wait_for=True,
		)
		computerAssociatedDomain = lo.getAttr(computer, 'associatedDomain')[0]

		udm.modify_object(role, dn=computer, append={'nagiosServices': nagiosServices})
		# validate that computer has been added to the new nagios services
		for nagiosService in nagiosServices:
			utils.verify_ldap_object(nagiosService, {'univentionNagiosHostname': [b'%s.%s' % (computerName.encode('ASCII'), computerAssociatedDomain)]})

		# modify computer again, removing the nagios services which have been set during creation
		udm.modify_object(role, dn=computer, remove={'nagiosServices': nagiosServices[:2]})
		# validate that the computer has been removed from the related nagios services
		for nagiosService in nagiosServices[:2]:
			utils.verify_ldap_object(nagiosService, {'univentionNagiosHostname': []})

		# validated that the computers is still set at the not removed nagios services
		for nagiosService in nagiosServices[2:]:
			utils.verify_ldap_object(nagiosService, {'univentionNagiosHostname': [b'%s.%s' % (computerName.encode('ASCII'), computerAssociatedDomain)]})

	# This test is disabled since 2014 due to issues when running on aws instaces
	# For further information, see Bug #37365 and commit 8666c032e7e
	@pytest.mark.skip(reason="utils.verify_ldap_object fails for some reason")
	@pytest.mark.tags('udm-computers')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	@pytest.mark.parametrize('role', COMPUTER_MODULES_EXCEPT_MACOS)
	def test_all_roles_creation_set_network(self, udm, ucr, lo, role):
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
		utils.verify_ldap_object(computer, {'univentionNetworkLink': [network]})

		assert aRecord in ['10.20.30.%s' % str(oktett) for oktett in range(2, 255)], "IP address of computer not in range of it's network"

		utils.verify_ldap_object(
			'relativeDomainName=%s,%s' % (computerProperties['name'], forwardZone),
			{'aRecord': [aRecord]}
		)

		utils.verify_ldap_object(
			'relativeDomainName=%s,%s' % (aRecord.split(".")[-1], reverseZone),
			{'pTRRecord': ['%s.%s.' % (computerProperties['name'], forwardZoneName)]}
		)

		utils.verify_ldap_object(
			'cn=%s,%s' % (computerProperties['name'], dhcpService),
			{'univentionDhcpFixedAddress': [aRecord]}
		)

	NET = '192.0.3'
	MAC = '00:00:6e:00:53'
	NAME = random_name()
	UNIQUE = range(2, 254).__iter__()


	@pytest.mark.tags('udm-computers')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	@pytest.mark.parametrize('role', COMPUTER_MODULES)
	@pytest.mark.parametrize(
		'manual_ip,manual_network,manual_dhcp', [
			(False, True,  False),
			(True,  True,  False),
			(False, False, True),
			(True,  False, True),
		], ids=[
			'Let Network choose the IP',
			'Give explicit IP, but DHCP from Network',
			'Manual DHCP with dynamic IP from known-hosts-pool',
			'Manual DHCP with fixed IP',
		]
	)
	def test_all_roles_modification_ip_choosing(self, udm, lo, role, manual_ip, manual_network, manual_dhcp):
		"""Test creating DHCP entries for some computer roles"""
		# bugs: [16923]
		service = udm.create_object('dhcp/service', service=random_name())
		unique = next(UNIQUE)

		ip = None
		if manual_ip:
			ip = '%s.%d' % (NET, unique)

		dhcp = None
		if manual_dhcp:
			dhcp = service

		udm.create_object(
			'networks/network',
			name=random_name(),
			network='%s.0' % (NET,) if manual_network else None,
			netmask='24',
			dhcpEntryZone=dhcp,
			ipRange='%s.2 %s.253' % (NET, NET)
		)

		computerName = "%s%d" % (NAME, unique)
		mac = '%s:%02x' % (MAC, unique)
		dhcp = ' '.join(filter(None, [dhcp, ip, mac])) if dhcp else None
		udm.create_object(
			role,
			name=computerName,
			mac=mac,
			ip=ip,
			network=network,
			dhcpEntryZone=dhcp,
		)

		dn = 'cn=%s,%s' % (ldap.dn.escape_dn_chars(computerName), service)
		expected = {
			'dhcpHWAddress': ['ethernet %s' % (mac,)],
			'univentionObjectType': ['dhcp/host'],
		}
		if manual_ip and manual_dhcp:
			expected['univentionDhcpFixedAddress'] = [ip]
		utils.verify_ldap_object(dn, expected)
		if not manual_ip and not manual_dhcp:
			result_ip = lo.getAttr(dn, 'univentionDhcpFixedAddress')[0].decode('ASCII')
			assert result_ip == ip

	@pytest.mark.tags('udm-computers')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	@pytest.mark.parametrize('role', COMPUTER_MODULES)
	def test_nameserver_update_in_zone_on_delete(self, udm, role):
		"""Check if nameservers in forward/reverse DNS zones are updated when deleting the nameserver"""
		# create zones and computer
		server_name = 'qwertzu'
		domain = 'asdfgh'
		fqdn_dot = server_name + '.' + domain + '.'
		forward = udm.create_object('dns/forward_zone', zone=domain, nameserver='aaa.aa.')
		reverse = udm.create_object('dns/reverse_zone', subnet='10.20.30', nameserver='aaa.aa.')
		computer = udm.create_object(role, set={
			'ip': '10.20.30.3',
			'name': server_name,
			'dnsEntryZoneForward': forward,
			'dnsEntryZoneReverse': reverse,
			'domain': domain,
		})
		udm.modify_object('dns/forward_zone', dn=forward, nameserver=[fqdn_dot], wait_for_replication=False)
		udm.modify_object('dns/reverse_zone', dn=reverse, nameserver=[fqdn_dot], wait_for=True)
		utils.wait_for_connector_replication()
		utils.verify_ldap_object(forward, {'nSRecord': ['aaa.aa.', fqdn_dot]})
		utils.verify_ldap_object(reverse, {'nSRecord': ['aaa.aa.', fqdn_dot]})

		# delete computer and check new name in zones
		udm.remove_object(role, dn=computer, wait_for=True)
		utils.wait_for_connector_replication()
		utils.verify_ldap_object(forward, {'nSRecord': ['aaa.aa.', ]})
		utils.verify_ldap_object(reverse, {'nSRecord': ['aaa.aa.', ]})


	@pytest.mark.tags('udm-computers', 'apptest')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	@pytest.mark.parametrize('role', COMPUTER_MODULES)
	def test_all_roles_univentionLastUsedValue(self, udm, ucr, role):
		"""
		Computer objects request a uidNumber when creating an object, but the value of
		univentionLastUsedValue has never been incremented.
		Since UCS 4.3-2erratumX this is no longer the case and univentionLastUsedValue
		is never changed.
		Create minimal object for all computer roles and check univentionLastUsedValue
		"""

		luv_dn = 'cn=uidNumber,cn=temporary,cn=univention,%s' % (ucr.get('ldap/base'),)
		lo = uldap.getAdminConnection()

		lastUsedValue_old = lo.get(luv_dn).get('univentionLastUsedValue', [-1])[0]
		computer_dn = udm.create_object(role, name=random_string(), wait_for_replication=False)
		utils.verify_ldap_object(computer_dn)
		lastUsedValue_new = lo.get(luv_dn).get('univentionLastUsedValue', [-1])[0]
		if lastUsedValue_old == lastUsedValue_new and role not in ('computers/ipmanagedclient',):
			utils.fail('Create %s with automatic uidNumber: univentionLastUsedValue did not change, but it should!' % (role,))
		if lastUsedValue_old != lastUsedValue_new and role in ('computers/ipmanagedclient',):
			utils.fail('Create %s: univentionLastUsedValue did change, but it should not!' % (role,))

		lastUsedValue_old = lo.get(luv_dn).get('univentionLastUsedValue', [-1])[0]
		kwargs = {
			'dn': computer_dn,
			'description': 'modified at {}'.format(time.ctime()),
			'wait_for_replication': False,
		}
		computer_dn = udm.modify_object(role, **kwargs)
		utils.verify_ldap_object(computer_dn, expected_attr={'description': [kwargs['description']]})
		lastUsedValue_new = lo.get(luv_dn).get('univentionLastUsedValue', [-1])[0]
		if lastUsedValue_old != lastUsedValue_new:
			utils.fail('Modified %s with specified uidNumber: univentionLastUsedValue did change, but it should not!' % (role,))

	# TODO: This is an artefact from the pytest conversion and needs to change
	utils.wait_for_replication()

	@pytest.mark.tags('udm-computers')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	@pytest.mark.parametrize('role', COMPUTER_MODULES)
	def test_multiple_dhcp_entry_zones(self, udm, role):
		"""Test appending and removing dhcpEntryZone for all computer roles"""
		# bugs: [44937]
		computerName = random_name()

		service = udm.create_object('dhcp/service', service=random_name())
		dhcpEntryZones = (
			[service, '10.20.30.40', '11:11:11:11:11:11'],
			[service, '10.20.30.41', '22:22:22:22:22:22'],
			[service, '10.20.30.42', '33:33:33:33:33:33'],
			[service, '10.20.30.43', '44:44:44:44:44:44']
		)

		computer = udm.create_object(role, name=computerName)

		udm.modify_object(role, dn=computer, append={
			'ip': [zone[1] for zone in dhcpEntryZones],
			'mac': [zone[2] for zone in dhcpEntryZones],
			'dhcpEntryZone': [' '.join(zone) for zone in dhcpEntryZones]
		})
		for i, (service, ip, mac) in enumerate(dhcpEntryZones, -1):
			addon = '' if i < 0 else '_uv%d' % (i,)
			utils.verify_ldap_object('cn=%s%s,%s' % (computerName, addon, service), {
				'univentionDhcpFixedAddress': [ip],
				'dhcpHWAddress': ['ethernet %s' % mac]
			})

		udm.modify_object(role, dn=computer, remove={
			'ip': [zone[1] for zone in dhcpEntryZones[:2]],
			'mac': [zone[2] for zone in dhcpEntryZones[:2]],
			'dhcpEntryZone': [' '.join(zone) for zone in dhcpEntryZones[:2]]
		})
		for i, (service, ip, mac) in list(enumerate(dhcpEntryZones, -1))[:2]:
			addon = '' if i < 0 else '_uv%d' % (i,)
			utils.verify_ldap_object('cn=%s%s,%s' % (ldap.dn.escape_dn_chars(computerName), addon, service), should_exist=False)

		for i, (service, ip, mac) in list(enumerate(dhcpEntryZones, -1))[2:]:
			addon = '' if i < 0 else '_uv%d' % (i,)
			utils.verify_ldap_object('cn=%s%s,%s' % (ldap.dn.escape_dn_chars(computerName), addon, service), {
				'univentionDhcpFixedAddress': [ip],
				'dhcpHWAddress': ['ethernet %s' % mac]
			})
