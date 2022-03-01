#!/usr/share/ucs-test/runner pytest-3
## desc: Test the allowed groupType changes
## tags: [udm,apptest, SKIP-UCSSCHOOL]
## roles: [domaincontroller_master]
## exposure: dangerous
## packages:
##   - univention-config
##   - univention-directory-manager-tools

from __future__ import print_function

import pytest

import univention.testing.udm as udm_test
import univention.testing.utils as utils

GROUP_TYPE_LOCAL = "-2147483643"
GROUP_TYPE_DOMAIN_LOCAL = "-2147483644"
GROUP_TYPE_GLOBAL = "-2147483646"
GROUP_TYPE_UNIVERSAL = "-2147483640"


def test_local_group_change(udm):
	group1 = udm.create_group(adGroupType=GROUP_TYPE_LOCAL)[0]
	group2 = udm.create_group(adGroupType=GROUP_TYPE_LOCAL)[0]
	group3 = udm.create_group(adGroupType=GROUP_TYPE_LOCAL)[0]

	utils.wait_for_connector_replication()

	utils.verify_ldap_object(group1, {'univentionGroupType': [GROUP_TYPE_LOCAL]})
	utils.verify_ldap_object(group2, {'univentionGroupType': [GROUP_TYPE_LOCAL]})
	utils.verify_ldap_object(group3, {'univentionGroupType': [GROUP_TYPE_LOCAL]})

	with pytest.raises(udm_test.UCSTestUDM_ModifyUDMObjectFailed):
		udm.modify_object('groups/group', dn=group1, adGroupType=GROUP_TYPE_DOMAIN_LOCAL)

	with pytest.raises(udm_test.UCSTestUDM_ModifyUDMObjectFailed):
		udm.modify_object('groups/group', dn=group2, adGroupType=GROUP_TYPE_GLOBAL)

	with pytest.raises(udm_test.UCSTestUDM_ModifyUDMObjectFailed):
		udm.modify_object('groups/group', dn=group3, adGroupType=GROUP_TYPE_UNIVERSAL)


def test_domain_local_group_change(udm):
	group1 = udm.create_group(adGroupType=GROUP_TYPE_DOMAIN_LOCAL)[0]
	group2 = udm.create_group(adGroupType=GROUP_TYPE_DOMAIN_LOCAL)[0]
	group3 = udm.create_group(adGroupType=GROUP_TYPE_DOMAIN_LOCAL)[0]

	group4 = udm.create_group(adGroupType=GROUP_TYPE_DOMAIN_LOCAL)[0]
	group5 = udm.create_group(adGroupType=GROUP_TYPE_DOMAIN_LOCAL, nestedGroup=group4)[0]
	group6 = udm.create_group(adGroupType=GROUP_TYPE_DOMAIN_LOCAL)[0]
	udm.create_group(adGroupType=GROUP_TYPE_DOMAIN_LOCAL, nestedGroup=group6)[0]

	group8 = udm.create_group(adGroupType=GROUP_TYPE_GLOBAL)[0]
	group9 = udm.create_group(adGroupType=GROUP_TYPE_DOMAIN_LOCAL, nestedGroup=group8)[0]
	group10 = udm.create_group(adGroupType=GROUP_TYPE_UNIVERSAL)[0]
	group11 = udm.create_group(adGroupType=GROUP_TYPE_DOMAIN_LOCAL, nestedGroup=group10)[0]

	utils.wait_for_connector_replication()

	utils.verify_ldap_object(group1, {'univentionGroupType': [GROUP_TYPE_DOMAIN_LOCAL]})
	utils.verify_ldap_object(group2, {'univentionGroupType': [GROUP_TYPE_DOMAIN_LOCAL]})
	utils.verify_ldap_object(group3, {'univentionGroupType': [GROUP_TYPE_DOMAIN_LOCAL]})
	utils.verify_ldap_object(group4, {'univentionGroupType': [GROUP_TYPE_DOMAIN_LOCAL]})
	utils.verify_ldap_object(group5, {'univentionGroupType': [GROUP_TYPE_DOMAIN_LOCAL]})

	with pytest.raises(udm_test.UCSTestUDM_ModifyUDMObjectFailed):
		udm.modify_object('groups/group', dn=group1, adGroupType=GROUP_TYPE_LOCAL)

	with pytest.raises(udm_test.UCSTestUDM_ModifyUDMObjectFailed):
		udm.modify_object('groups/group', dn=group2, adGroupType=GROUP_TYPE_GLOBAL)

	udm.modify_object('groups/group', dn=group3, adGroupType=GROUP_TYPE_UNIVERSAL)

	with pytest.raises(udm_test.UCSTestUDM_ModifyUDMObjectFailed):
		udm.modify_object('groups/group', dn=group5, adGroupType=GROUP_TYPE_UNIVERSAL)
		print('E: Domain local group has another domain local group as member. Change to universal group was possible which should not be.')

	udm.modify_object('groups/group', dn=group6, adGroupType=GROUP_TYPE_UNIVERSAL)

	udm.modify_object('groups/group', dn=group9, adGroupType=GROUP_TYPE_UNIVERSAL)
	udm.modify_object('groups/group', dn=group11, adGroupType=GROUP_TYPE_UNIVERSAL)


def test_global_group_change(udm):
	group1 = udm.create_group(adGroupType=GROUP_TYPE_GLOBAL)[0]
	group2 = udm.create_group(adGroupType=GROUP_TYPE_GLOBAL)[0]
	group3 = udm.create_group(adGroupType=GROUP_TYPE_GLOBAL)[0]

	group4 = udm.create_group(adGroupType=GROUP_TYPE_GLOBAL)[0]
	group5 = udm.create_group(adGroupType=GROUP_TYPE_GLOBAL, nestedGroup=group4)[0]
	group6 = udm.create_group(adGroupType=GROUP_TYPE_GLOBAL)[0]
	udm.create_group(adGroupType=GROUP_TYPE_GLOBAL, nestedGroup=group6)[0]

	group8 = udm.create_group(adGroupType=GROUP_TYPE_DOMAIN_LOCAL)[0]
	group9 = udm.create_group(adGroupType=GROUP_TYPE_GLOBAL, nestedGroup=group8)[0]
	group10 = udm.create_group(adGroupType=GROUP_TYPE_UNIVERSAL)[0]
	group11 = udm.create_group(adGroupType=GROUP_TYPE_GLOBAL, nestedGroup=group10)[0]

	utils.wait_for_connector_replication()

	utils.verify_ldap_object(group1, {'univentionGroupType': [GROUP_TYPE_GLOBAL]})
	utils.verify_ldap_object(group2, {'univentionGroupType': [GROUP_TYPE_GLOBAL]})
	utils.verify_ldap_object(group3, {'univentionGroupType': [GROUP_TYPE_GLOBAL]})
	utils.verify_ldap_object(group4, {'univentionGroupType': [GROUP_TYPE_GLOBAL]})
	utils.verify_ldap_object(group5, {'univentionGroupType': [GROUP_TYPE_GLOBAL]})

	with pytest.raises(udm_test.UCSTestUDM_ModifyUDMObjectFailed):
		udm.modify_object('groups/group', dn=group1, adGroupType=GROUP_TYPE_LOCAL)

	with pytest.raises(udm_test.UCSTestUDM_ModifyUDMObjectFailed):
		udm.modify_object('groups/group', dn=group2, adGroupType=GROUP_TYPE_DOMAIN_LOCAL)

	udm.modify_object('groups/group', dn=group3, adGroupType=GROUP_TYPE_UNIVERSAL)

	udm.modify_object('groups/group', dn=group5, adGroupType=GROUP_TYPE_UNIVERSAL)

	with pytest.raises(udm_test.UCSTestUDM_ModifyUDMObjectFailed):
		udm.modify_object('groups/group', dn=group6, adGroupType=GROUP_TYPE_UNIVERSAL)
		print('E: Global group is member of another global group. Change to universal group was possible which should not be.')

	udm.modify_object('groups/group', dn=group9, adGroupType=GROUP_TYPE_UNIVERSAL)
	udm.modify_object('groups/group', dn=group11, adGroupType=GROUP_TYPE_UNIVERSAL)


def test_universal_group_change(udm):
	group1 = udm.create_group(adGroupType=GROUP_TYPE_UNIVERSAL)[0]
	group2 = udm.create_group(adGroupType=GROUP_TYPE_UNIVERSAL)[0]
	group3 = udm.create_group(adGroupType=GROUP_TYPE_UNIVERSAL)[0]

	group4 = udm.create_group(adGroupType=GROUP_TYPE_UNIVERSAL)[0]
	group5 = udm.create_group(adGroupType=GROUP_TYPE_UNIVERSAL, nestedGroup=group4)[0]
	group6 = udm.create_group(adGroupType=GROUP_TYPE_UNIVERSAL)[0]
	udm.create_group(adGroupType=GROUP_TYPE_UNIVERSAL, nestedGroup=group6)[0]

	group8 = udm.create_group(adGroupType=GROUP_TYPE_DOMAIN_LOCAL)[0]
	group9 = udm.create_group(adGroupType=GROUP_TYPE_UNIVERSAL, nestedGroup=group8)[0]
	group10 = udm.create_group(adGroupType=GROUP_TYPE_GLOBAL)[0]
	group11 = udm.create_group(adGroupType=GROUP_TYPE_UNIVERSAL, nestedGroup=group10)[0]

	utils.wait_for_connector_replication()

	utils.verify_ldap_object(group1, {'univentionGroupType': [GROUP_TYPE_UNIVERSAL]})
	utils.verify_ldap_object(group2, {'univentionGroupType': [GROUP_TYPE_UNIVERSAL]})
	utils.verify_ldap_object(group3, {'univentionGroupType': [GROUP_TYPE_UNIVERSAL]})

	with pytest.raises(udm_test.UCSTestUDM_ModifyUDMObjectFailed):
		udm.modify_object('groups/group', dn=group1, adGroupType=GROUP_TYPE_LOCAL)

	udm.modify_object('groups/group', dn=group2, adGroupType=GROUP_TYPE_DOMAIN_LOCAL)

	udm.modify_object('groups/group', dn=group3, adGroupType=GROUP_TYPE_GLOBAL)

	with pytest.raises(udm_test.UCSTestUDM_ModifyUDMObjectFailed):
		udm.modify_object('groups/group', dn=group5, adGroupType=GROUP_TYPE_GLOBAL)
		print('E: Universal group has another universal group as member. Change to global group was possible which should not be.')

	udm.modify_object('groups/group', dn=group6, adGroupType=GROUP_TYPE_GLOBAL)

	udm.modify_object('groups/group', dn=group9, adGroupType=GROUP_TYPE_GLOBAL)
	udm.modify_object('groups/group', dn=group11, adGroupType=GROUP_TYPE_GLOBAL)
