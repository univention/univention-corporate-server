#!/usr/share/ucs-test/runner python
## desc: Create maximal computers/windows_domaincontroller and validate it's attributes as well as automatically created referring objects and group memberships
## tags: [udm-computers]
## roles: [domaincontroller_master]
## exposure: careful
## packages:
##   - univention-config
##   - univention-directory-manager-tools


import smbpasswd
import univention.testing.udm as udm_test
import univention.testing.strings as uts
import univention.testing.utils as utils
import univention.config_registry as configRegistry


if __name__ == '__main__':
	ldap = utils.get_ldap_connection()
	ucr = configRegistry.ConfigRegistry()
	ucr.load()

	s4Connector = None
	if ucr.is_true('directory/manager/samba3/legacy', False):
		s4Connector = False
	elif ucr.is_false('directory/manager/samba3/legacy', False):
		s4Connector = True

	objectType = 'computers/windows_domaincontroller'
	with udm_test.UCSTestUDM() as udm:
		dhcpZone = udm.create_object('dhcp/service', service = uts.random_name())
		
		properties = {
			'name': uts.random_name(),
			'description': uts.random_string(),
			'operatingSystem': uts.random_string(),
			'operatingSystemVersion': uts.random_string(),
			'domain': '%s.%s' % (uts.random_name(), uts.random_name()),
			'mac': '01:23:45:67:89:ab',
			'network': udm.create_object('networks/network', name = uts.random_name(), network = '10.20.30.0', netmask = '24'),
			'ip': '10.20.30.2',
			'dnsEntryZoneForward': udm.create_object('dns/forward_zone', zone = '%s.%s' % (uts.random_name(), uts.random_name()), nameserver = uts.random_string()),
			'dnsEntryZoneReverse': udm.create_object('dns/reverse_zone', subnet = '10.20.30', nameserver = uts.random_string()),
			'password': uts.random_string(),
			'unixhome': '/home/',
			'shell': uts.random_string(),
			'primaryGroup': udm.create_group()[0],
			'inventoryNumber': uts.random_string(),
			'groups': [udm.create_group()[0], udm.create_group()[0]],
			'sambaRID': uts.random_int(10000, 12000),
			'serverRole': uts.random_string()
		}
		properties['dhcpEntryZone'] = '%s %s %s' % (dhcpZone, properties['ip'], properties['mac'])
		
		expectedLdap = {
			'cn': [properties['name']],
			'sn': [properties['name']],
			'uid': ['%s$' % properties['name']],
			'displayName': [properties['name']],
			'description': [properties['description']],
			'univentionOperatingSystem': [properties['operatingSystem']],
			'univentionOperatingSystemVersion': [properties['operatingSystemVersion']],
			'associatedDomain': [properties['domain']],
			'sambaNTPassword': [smbpasswd.nthash(properties['password'].lower())],
			'macAddress': [properties['mac']],
			'univentionNetworkLink': [properties['network']],
			'aRecord': [properties['ip']],
			'homeDirectory': [properties['unixhome']],
			'loginShell': [properties['shell']],
			'univentionServerRole': [properties['serverRole'], 'windows_domaincontroller'],
			'gidNumber': ldap.search(base = properties['primaryGroup'], attr = ['gidNumber'])[0][1].get('gidNumber', []),
			'univentionInventoryNumber': [properties['inventoryNumber']],
			'sambaSID': ['S-1-4-%s' % str( int(ldap.getAttr('cn=uidNumber,cn=temporary,cn=univentoin,%s' % ucr['ldap/base'], 'univentionLastUsedValue')[0])+1 ) if s4Connector else '%s-%s' % (ldap.search(filter = 'objectClass=sambaDomain', attr = ['sambaSID'])[0][1]['sambaSID'][0], properties['sambaRID'])],
			'sambaPrimaryGroupSID': [ldap.getAttr(properties['primaryGroup'], 'sambaSID')[0]],
			'krb5PrincipalName': ['host/%s.%s@%s' % (properties['name'], properties['domain'].lower(), ldap.getAttr(ucr['ldap/base'], 'krb5RealmName')[0])]
		}


		# validate computer ldap object
		computerDN = udm.create_object(objectType, **properties)
		if not utils.verify_ldap_object(computerDN, expectedLdap):
			utils.fail()

		# validate related DHCP host object
		if not utils.verify_ldap_object('cn=%s,%s' % (properties['name'], dhcpZone), {
			'dhcpHWAddress': ['ethernet %s' % properties['mac']],
			'univentionDhcpFixedAddress': [properties['ip']]
		}):
			utils.fail('Automatically created DHCP host object differs from expectation')

		# validate relalted A record
		if not utils.verify_ldap_object('relativeDomainName=%s,%s' % (properties['name'], properties['dnsEntryZoneForward']), {
			'aRecord': [properties['ip']],
			'relativeDomainName': [properties['name']],
			'zoneName': [properties['dnsEntryZoneForward'].split('zoneName=')[1].split(',')[0]]
		}):
			utils.fail('Automatically created A record differs from expectation')
		
		# validate related PTR record
		if not utils.verify_ldap_object('relativeDomainName=2,%s' % properties['dnsEntryZoneReverse'], {
			'relativeDomainName': '2',
			'pTRRecord': ['%s.%s.' % (properties['name'], properties['dnsEntryZoneForward'].split('zoneName=')[1].split(',')[0])],
			'zoneName': [properties['dnsEntryZoneReverse'].split('zoneName=')[1].split(',')[0]]
		}):
			utils.fail('Automatically created PTR record differs from expectation')

		for group in [properties['primaryGroup']] + properties['groups']:
			if not utils.verify_ldap_object(group, {'memberUid': ['%s$' % properties['name']], 'uniqueMember': [computerDN]}):
				utils.fail('Broken group membership of created %s in group "%s"' % (objectType, group))
