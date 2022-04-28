#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: Create UDM object with multi-malued RDN
## roles: [domaincontroller_master,domaincontroller_backup,domaincontroller_slave,memberserver]
## exposure: careful
## bugs: [40129]

import pytest

from ldap import AVA_STRING
from ldap.dn import dn2str, str2dn

from univention.testing.strings import random_name
from univention.testing.utils import verify_ldap_object, wait_for_replication

MODULE = 'tests/ipservice'


@pytest.mark.tags('udm')
@pytest.mark.roles('domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver')
@pytest.mark.exposure('careful')
def test_multi_valued_rdn(udm):
	print("Creating...")
	testing = udm.create_object('container/cn', name=random_name())
	str_tcp = udm.create_object(MODULE, position=testing, name='echo', protocol='tcp', port='7')
	str_udp = udm.create_object(MODULE, position=testing, name='echo', protocol='udp', port='7')
	wait_for_replication()

	print("Testing DNs...")
	verify_ldap_object(str_tcp)
	verify_ldap_object(str_udp)

	print("Testing reversed DNs...")
	dn_tcp = str2dn(str_tcp)
	dn_tcp[0].reverse()
	verify_ldap_object(dn2str(dn_tcp))

	dn_udp = str2dn(str_udp)
	dn_udp[0].reverse()
	verify_ldap_object(dn2str(dn_udp))

	print("Testing modify...")
	DESC = 'The UDP echo service'
	str_udp = udm.modify_object(MODULE, dn=str_udp, description=DESC)
	verify_ldap_object(str_udp, expected_attr={'description': [DESC]}, strict=False)

	print("Testing delete...")
	udm.remove_object(MODULE, dn=str_udp)
	verify_ldap_object(str_udp, should_exist=False)

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

	verify_ldap_object(str_tcp, should_exist=False)
	verify_ldap_object(new_tcp)
#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: policy reference works after changing the objects dn
## tags: [udm,apptest,SKIP]
## roles: [domaincontroller_master]
## bugs: [41694]
## exposure: dangerous
## packages:
##   - univention-config
##   - univention-directory-manager-tools


import pytest

import univention.testing.utils as utils
from univention.testing.strings import random_string


@pytest.mark.tags('udm')
@pytest.mark.roles('domaincontroller_master')
@pytest.mark.exposure('dangerous')
@pytest.mark.parametrize('object_type', ['container/cn', 'mail/domain'])
def test_policy_reference_after_object_change(udm, object_type):
	print('testing', object_type)
	policy = udm.create_object('policies/pwhistory', **{'name': random_string()})
	old_dn = udm.create_object(object_type, **{'name': random_string()})

	new_dn = udm.modify_object(object_type, **{'name': random_string(), 'dn': old_dn, 'policy_reference': policy})
	print('new_dn', new_dn)
	utils.verify_ldap_object(new_dn, {'univentionPolicyReference': [policy]})
	print('old_dn', old_dn)
	utils.verify_ldap_object(old_dn, should_exist=False)
#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: Test that --policy-reference is not evaluated when creating a existing object
## tags: [udm]
## roles: [domaincontroller_master]
## exposure: careful
## bugs: [38856]
## packages:
##   - univention-config
##   - univention-directory-manager-tools

import pytest

import univention.testing.strings as uts
import univention.testing.udm as udm_test
import univention.testing.utils as utils


@pytest.mark.tags('udm')
@pytest.mark.roles('domaincontroller_master')
@pytest.mark.exposure('careful')
def test_create_existing_object_does_not_policy_reference(udm):
	dhcp_service = udm.create_object('dhcp/service', service=uts.random_name())
	policy = udm.create_object('policies/pwhistory', **{'name': uts.random_string()})

	subnet_mask = '24'
	subnet = '10.20.30.0'
	dhcp_subnet = udm.create_object('dhcp/subnet', superordinate=dhcp_service, subnet=subnet, subnetmask=subnet_mask)
	with pytest.raises(udm_test.UCSTestUDM_CreateUDMObjectFailed):
		dhcp_subnet = udm.create_object('dhcp/subnet', superordinate=dhcp_service, subnet=subnet, subnetmask=subnet_mask, policy_reference=policy)

	utils.verify_ldap_object(dhcp_subnet, {'univentionPolicyReference': []})
#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: Test removing values from UCR policy
## bugs: [43562]
## roles:
##  - domaincontroller_master
## exposure: dangerous

import pytest

from univention.testing import utils


@pytest.mark.tags('udm')
@pytest.mark.roles('domaincontroller_master')
@pytest.mark.exposure('careful')
def test_remove_values_from_ucr_policy(udm):
	policy = udm.create_object('policies/registry', name='test', registry=['foo bar', 'bar baz'])
	utils.verify_ldap_object(policy, {'univentionRegistry;entry-hex-666f6f': ['bar'], 'univentionRegistry;entry-hex-626172': ['baz']})
	udm.modify_object('policies/registry', dn=policy, remove={'registry': ['bar baz']})
	utils.verify_ldap_object(policy, {'univentionRegistry;entry-hex-666f6f': ['bar']})
#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: Test removing values from share
## bugs: [41072]
## roles:
##  - domaincontroller_master
## tags: [apptest]
## exposure: dangerous

import pytest

from univention.testing import utils


@pytest.mark.tags('udm')
@pytest.mark.roles('domaincontroller_master')
@pytest.mark.exposure('careful')
def test_remove_values_from_share_sambaCustomSettings(udm):
	share = udm.create_object('shares/share', name='test', host='localhost', path='/path/', sambaCustomSettings='"follow symlinks" "yes"')
	utils.verify_ldap_object(share, {'univentionShareSambaCustomSetting': ['follow symlinks = yes']})
	udm.modify_object('shares/share', dn=share, remove={'sambaCustomSettings': ['"follow symlinks" "yes"']})
	utils.verify_ldap_object(share, {'univentionShareSambaCustomSetting': []})
