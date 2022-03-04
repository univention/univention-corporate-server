#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## tags: [udm]
## roles: [domaincontroller_master,domaincontroller_backup,domaincontroller_slave,memberserver]
## exposure: careful
## bugs: [40129,41072,38856,41694,43562]
## packages:
##   - univention-config
##   - univention-directory-manager-tools

import pytest

from ldap import AVA_STRING
from ldap.dn import dn2str, str2dn

from univention.testing import utils
from univention.testing.strings import random_name, random_string
import univention.testing.udm as udm_test


MODULE = 'tests/ipservice'


@pytest.mark.tags('udm')
@pytest.mark.roles('domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver')
@pytest.mark.exposure('careful')
def test_multi_valued_rdn(udm):
	"""Create UDM object with multi-malued RDN"""
	# bugs: [#40129]
	print("Creating...")
	testing = udm.create_object('container/cn', name=random_name())
	str_tcp = udm.create_object(MODULE, position=testing, name='echo', protocol='tcp', port='7')
	str_udp = udm.create_object(MODULE, position=testing, name='echo', protocol='udp', port='7')
	utils.wait_for_replication()

	print("Testing DNs...")
	utils.verify_ldap_object(str_tcp)
	utils.verify_ldap_object(str_udp)

	print("Testing reversed DNs...")
	dn_tcp = str2dn(str_tcp)
	dn_tcp[0].reverse()
	utils.verify_ldap_object(dn2str(dn_tcp))

	dn_udp = str2dn(str_udp)
	dn_udp[0].reverse()
	utils.verify_ldap_object(dn2str(dn_udp))

	print("Testing modify...")
	DESC = 'The UDP echo service'
	str_udp = udm.modify_object(MODULE, dn=str_udp, description=DESC)
	utils.verify_ldap_object(str_udp, expected_attr={'description': [DESC]}, strict=False)

	print("Testing delete...")
	udm.remove_object(MODULE, dn=str_udp)
	utils.verify_ldap_object(str_udp, should_exist=False)

	print("Testing rename...")
	new_tcp = udm.modify_object(MODULE, dn=str_tcp, port='8')
	# Bug #41694: does NOT return new_dn !
	ATTR = 'ipServicePort'
	new_tcp = dn2str([
		[
			(ATTR, '8', AVA_STRING) if ava[0] == ATTR else ava
			for ava in rdn
		] for rdn in dn_tcp
	])

	utils.verify_ldap_object(str_tcp, should_exist=False)
	utils.verify_ldap_object(new_tcp)


@pytest.mark.skip()
@pytest.mark.tags('udm', 'apptest')
@pytest.mark.roles('domaincontroller_master')
@pytest.mark.exposure('dangerous')
@pytest.mark.parametrize('object_type', ['container/cn', 'mail/domain'])
def test_policy_reference_after_object_change(udm, object_type):
	"""policy reference works after changing the objects dn"""
	# bugs: [41694]
	print('testing', object_type)
	policy = udm.create_object('policies/pwhistory', **{'name': random_string()})
	old_dn = udm.create_object(object_type, **{'name': random_string()})

	new_dn = udm.modify_object(object_type, **{'name': random_string(), 'dn': old_dn, 'policy_reference': policy})
	print('new_dn', new_dn)
	utils.verify_ldap_object(new_dn, {'univentionPolicyReference': [policy]})
	print('old_dn', old_dn)
	utils.verify_ldap_object(old_dn, should_exist=False)


@pytest.mark.tags('udm')
@pytest.mark.roles('domaincontroller_master')
@pytest.mark.exposure('careful')
def test_create_existing_object_does_not_policy_reference(udm):
	"""Test that --policy-reference is not evaluated when creating a existing object"""
	# bugs:  [38856]
	dhcp_service = udm.create_object('dhcp/service', service=random_name())
	policy = udm.create_object('policies/pwhistory', **{'name': random_string()})

	subnet_mask = '24'
	subnet = '10.20.30.0'
	dhcp_subnet = udm.create_object('dhcp/subnet', superordinate=dhcp_service, subnet=subnet, subnetmask=subnet_mask)
	with pytest.raises(udm_test.UCSTestUDM_CreateUDMObjectFailed):
		dhcp_subnet = udm.create_object('dhcp/subnet', superordinate=dhcp_service, subnet=subnet, subnetmask=subnet_mask, policy_reference=policy)

	utils.verify_ldap_object(dhcp_subnet, {'univentionPolicyReference': []})


@pytest.mark.tags('udm')
@pytest.mark.roles('domaincontroller_master')
@pytest.mark.exposure('careful')
def test_remove_values_from_ucr_policy(udm):
	"""Test removing values from UCR policy"""
	# bugs: [43562]
	policy = udm.create_object('policies/registry', name='test', registry=['foo bar', 'bar baz'])
	utils.verify_ldap_object(policy, {'univentionRegistry;entry-hex-666f6f': ['bar'], 'univentionRegistry;entry-hex-626172': ['baz']})
	udm.modify_object('policies/registry', dn=policy, remove={'registry': ['bar baz']})
	utils.verify_ldap_object(policy, {'univentionRegistry;entry-hex-666f6f': ['bar']})


@pytest.mark.tags('apptest')
@pytest.mark.roles('domaincontroller_master')
@pytest.mark.exposure('careful')
def test_remove_values_from_share_sambaCustomSettings(udm):
	"""Test removing values from share"""
	# bug: [41072]
	share = udm.create_object('shares/share', name='test', host='localhost', path='/path/', sambaCustomSettings='"follow symlinks" "yes"')
	utils.verify_ldap_object(share, {'univentionShareSambaCustomSetting': ['follow symlinks = yes']})
	udm.modify_object('shares/share', dn=share, remove={'sambaCustomSettings': ['"follow symlinks" "yes"']})
	utils.verify_ldap_object(share, {'univentionShareSambaCustomSetting': []})
