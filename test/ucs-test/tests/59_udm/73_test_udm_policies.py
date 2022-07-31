#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: Test UDM policies
## tags: [udm,udm-policies,apptest]
## exposure: careful
## bugs: [38663, 38712, 41641]

import subprocess

import pytest

from univention.lib.policy_result import policy_result
from univention.testing import strings as uts

NET = '192.168.2.0'
router = '192.168.2.1'
router2 = '192.168.2.254'


@pytest.fixture(scope='session')
def service_subnet_routing(udm_session):
	udm = udm_session
	service = udm.create_object('dhcp/service', service=uts.random_name(), wait_for_replication=False)
	subnet = udm.create_object('dhcp/subnet', subnet=NET, subnetmask='255.255.255.0', superordinate=service, wait_for_replication=False)
	dhcp_routing = udm.create_object('policies/dhcp_routing', position=subnet, name='p1', routers=router, wait_for_replication=False)
	udm.modify_object('dhcp/service', dn=service, policy_reference=dhcp_routing, wait_for_replication=False)
	return service, subnet, dhcp_routing


@pytest.mark.parametrize('prop,propval', [
	('requiredObjectClasses', 'univentionDhcpSubnet'),
	('requiredObjectClasses', 'univentionDhcpSubnet'.swapcase()),
	('prohibitedObjectClasses', 'univentionDhcpService'),
	('prohibitedObjectClasses', 'univentionDhcpService'.swapcase()),
	('ldapFilter', '(objectClass=univentionDhcpSubnet)'),
	('ldapFilter', '(objectClass=' + 'univentionDhcpSubnet)'.swapcase()),

])
def test_policy_object_classes_and_filter(udm_session, lo, prop, propval, service_subnet_routing):
	"""Test requiredObjectClasses, prohibitedObjectClasses, ldapFilter in UMC policy"""
	udm = udm_session
	service, subnet, dhcp_routing = service_subnet_routing
	udm.modify_object('policies/dhcp_routing', dn=dhcp_routing, **{prop: propval})

	result = policy_result(service)
	assert result[0].get('univentionDhcpRouters') != [router]
	pol_result = lo.getPolicies(service).get("univentionPolicyDhcpRouting", {}).get("univentionDhcpRouters", {})
	assert pol_result.get('policy') != dhcp_routing

	result = policy_result(subnet)
	assert result[0]['univentionDhcpRouters'] == [router]
	pol_result = lo.getPolicies(subnet).get("univentionPolicyDhcpRouting", {}).get("univentionDhcpRouters", {})
	assert pol_result.get('policy') == dhcp_routing
	assert pol_result.get('fixed') is False
	assert pol_result.get('value') == [router.encode()]


@pytest.mark.parametrize('pol1_attributes,pol2_attributes,expected_policy,expected_router,expected_fixed', [
	({'fixedAttributes': 'univentionDhcpRouters'}, {}, '1', [router], True),
	({}, {'emptyAttributes': 'univentionDhcpRouters'}, '2', [], False),
])
def test_policy_fixed_empty_attributes(udm, lo, pol1_attributes, pol2_attributes, expected_policy, expected_router, expected_fixed):
	"""Test fixedAttributes and emptyAttributes in UMC policy"""
	service = udm.create_object('dhcp/service', service=uts.random_name(), wait_for_replication=False)
	subnet = udm.create_object('dhcp/subnet', subnet=NET, subnetmask='255.255.255.0', superordinate=service, wait_for_replication=False)
	dhcp_routing = udm.create_object('policies/dhcp_routing', position=subnet, name='p1', routers=router, wait_for_replication=False, **pol1_attributes)
	udm.modify_object('dhcp/service', dn=service, policy_reference=dhcp_routing, wait_for_replication=False)
	dhcp_routing2 = udm.create_object('policies/dhcp_routing', position=subnet, name='p2', routers=router2, **pol2_attributes, wait_for_replication=False)
	udm.modify_object('dhcp/subnet', dn=subnet, policy_reference=dhcp_routing2)
	expected_policy = dhcp_routing if expected_policy == '1' else dhcp_routing2

	result = policy_result(service)
	assert result[0]['univentionDhcpRouters'] == [router]
	pol_result = lo.getPolicies(service).get("univentionPolicyDhcpRouting", {}).get("univentionDhcpRouters", {})
	assert pol_result.get('policy') == dhcp_routing
	assert pol_result.get('fixed') is expected_fixed
	assert pol_result.get('value') == [router.encode()]

	result = policy_result(subnet)
	assert result[0]['univentionDhcpRouters'] == expected_router
	pol_result = lo.getPolicies(subnet).get("univentionPolicyDhcpRouting", {}).get("univentionDhcpRouters", {})
	assert pol_result.get('policy') == expected_policy
	assert pol_result.get('fixed') is expected_fixed
	assert pol_result.get('value') == ([expected_router[0].encode()] if expected_router else expected_router)


def test_policy_inheritance(udm, lo):
	"""Test policy inheritance in UMC policy"""
	service = udm.create_object('dhcp/service', service=uts.random_name(), wait_for_replication=False)
	subnet = udm.create_object('dhcp/subnet', subnet=NET, subnetmask='255.255.255.0', superordinate=service, wait_for_replication=False)
	pool = udm.create_object('dhcp/pool', name='pool', range='192.168.2.2 192.168.2.253', superordinate=subnet, wait_for_replication=False)
	dhcp_routing = udm.create_object('policies/dhcp_routing', position=subnet, name='p1', routers=router, fixedAttributes='univentionDhcpRouters', wait_for_replication=False)
	udm.modify_object('dhcp/service', dn=service, policy_reference=dhcp_routing, wait_for_replication=False)
	dhcp_routing2 = udm.create_object('policies/dhcp_routing', position=subnet, name='p2', routers=router2, wait_for_replication=False)
	udm.modify_object('dhcp/pool', dn=pool, policy_reference=dhcp_routing2)

	result = policy_result(pool)
	assert result[0]['univentionDhcpRouters'] == [router]
	pol_result = lo.getPolicies('cn=notexisting,' + service).get("univentionPolicyDhcpRouting", {}).get("univentionDhcpRouters", {})
	assert pol_result.get('policy') == dhcp_routing
	assert pol_result.get('fixed') is True
	assert pol_result.get('value') == [router.encode()]


@pytest.mark.roles('domaincontroller_master')
def test_policy_object_class_order(udm, lo):
	"""Test policy ignores ordering of objectClasses"""
	## bugs: [41641]
	service = udm.create_object('dhcp/service', service=uts.random_name(), wait_for_replication=False)
	dhcp_routing = f'cn=p1,{service}'
	dhcp_routing2 = f'cn=p2,{service}'
	proc = subprocess.Popen(['ldapadd', '-x', '-D', f'cn=admin,{lo.base}', '-y', '/etc/ldap.secret'], stdin=subprocess.PIPE)
	proc.communicate(f'''
dn: {dhcp_routing}
objectClass: top
objectClass: univentionPolicy
objectClass: univentionPolicyDhcpRouting
objectClass: univentionObject
univentionObjectType: policies/dhcp_routing
cn: p1
univentionDhcpRouters: 192.168.0.1

dn: {dhcp_routing2}
objectClass: top
objectClass: univentionPolicyDhcpRouting
objectClass: univentionPolicy
objectClass: univentionObject
univentionObjectType: policies/dhcp_routing
cn: p2
univentionDhcpRouters: 192.168.0.1
'''.encode('UTF-8'))
	udm.modify_object('dhcp/service', dn=service, policy_reference=dhcp_routing)
	result1 = policy_result(service)
	udm.modify_object('dhcp/service', dn=service, policy_reference=dhcp_routing2)
	result2 = policy_result(service)
	assert result1 == result2
