#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: Test creating DHCP entries for some computer roles
## tags: [udm-computers]
## roles: [domaincontroller_master]
## exposure: careful
## bugs: [16923]

import ldap.dn
import pytest

import univention.testing.udm as udm_test
from univention.testing.strings import random_name
from univention.testing.udm import UCSTestUDM

COMPUTER_MODULES = udm_test.UCSTestUDM.COMPUTER_MODULES

UNIQUE = range(2, 254).__iter__()


@pytest.fixture(scope='class')
def service_and_network():
	# the udm fixture has the wrong scope and thus can't be used
	with UCSTestUDM() as udm:

		NET = '192.0.3'
		service = udm.create_object('dhcp/service', service=random_name())

		network = udm.create_object(
			'networks/network',
			name=random_name(),
			network='%s.0' % (NET,),
			netmask='24',
			dhcpEntryZone=service,
			ipRange='%s.2 %s.253' % (NET, NET))

		yield udm, service, network, NET


@pytest.mark.tags('udm-computers')
@pytest.mark.roles('domaincontroller_master')
@pytest.mark.exposure('careful')
@pytest.mark.parametrize('role', COMPUTER_MODULES)
@pytest.mark.parametrize(
	'ip,manual_network,manual_dhcp', [
		(False, True, False),
		(True, True, False),
		(False, False, True),
		(True, False, True),
	], ids=[
		'Let Network choose the IP',
		'Give explicit IP, but DHCP from Network',
		'Manual DHCP with dynamic IP from known-hosts-pool',
		'Manual DHCP with fixed IP',
	]
)
class Test_AllRoles:
	def test_all_roles_modification_ip_choosing(self, lo, verify_ldap_object, role, ip, manual_network, manual_dhcp, service_and_network):
		"""
		Test creating DHCP entries for some computer roles
		"""
		udm, service, network, NET = service_and_network
		unique = next(UNIQUE)

		# create
		computerName = "%s%d" % (random_name(), unique)
		mac = '00:00:6e:00:53:%02x' % (unique)
		ip = '%s.%d' % (NET, unique) if ip else None
		dhcp = ' '.join(filter(None, [service, ip, mac])) if manual_dhcp else None

		udm.create_object(
			role,
			name=computerName,
			mac=mac,
			ip=ip,
			network=network if manual_network else None,
			dhcpEntryZone=dhcp,
		)

		# verify
		dn = 'cn=%s,%s' % (ldap.dn.escape_dn_chars(computerName), service)
		expected = {
			'dhcpHWAddress': ['ethernet %s' % (mac,)],
			'univentionObjectType': ['dhcp/host'],
		}
		if ip:
			expected['univentionDhcpFixedAddress'] = [ip]

		verify_ldap_object(dn, expected)

		if manual_network and not ip:
			result_ip = lo.getAttr(dn, 'univentionDhcpFixedAddress')[0].decode('ASCII')
			assert result_ip.startswith(NET)
