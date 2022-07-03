#!/usr/share/ucs-test/runner pytest-3
## desc: Test AD Group Type
## tags: [udm,apptest, SKIP-UCSSCHOOL]
## roles: [domaincontroller_master]
## exposure: dangerous
## packages:
##   - univention-config
##   - univention-directory-manager-tools

import pytest

import univention.testing.strings as uts
import univention.testing.udm as udm_test
import univention.testing.utils as utils

GROUP_TYPE_LOCAL = "-2147483643"
GROUP_TYPE_DOMAIN_LOCAL = "-2147483644"
GROUP_TYPE_GLOBAL = "-2147483646"
GROUP_TYPE_UNIVERSAL = "-2147483640"


class Test_AllowedADGroupTypeChanges:
	"""Test the allowed groupType changes"""

	def test_local_group_change(self, udm):
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

	def test_domain_local_group_change(self, udm):
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

	def test_global_group_change(self, udm):
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

	def test_universal_group_change(self, udm):
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


def test_umd_memberUid(udm, ucr, lo):
	"""Test the allowed groupType changes"""
	# create
	group1 = udm.create_group(adGroupType="")[0]

	# validate memberuid after update users in group
	username = uts.random_name()
	for i in range(5):
		user = 'uid=%s,cn=temp_%s,%s' % (username, i, ucr.get('ldap/base'),)
		group1 = udm.modify_object('groups/group', dn=group1, users=user)
		res = lo.get(group1).get('memberUid')
		res1 = lo.get(group1).get('uniqueMember')
		assert res and res1

	# remove group
	group1 = udm.remove_object('groups/group', dn=group1)
	if not group1:
		print("Remove group successfully  ")


def _sid_is_builtin(sid):
	return sid.startswith('S-1-5-32-')


def _sid_is_local(sid):
	return sid.startswith('S-1-4-')


def _sid_is_global(sid):
	return sid.startswith('S-1-5-21-')


def _get_samba_sid(dn):
	lo = utils.get_ldap_connection()
	res = lo.search(base=dn, filter='objectClass=*', attr=['sambaSID'])
	return res[0][1].get('sambaSID')[0].decode('ASCII')


@pytest.mark.parametrize('group_type,use_create_group_parameter,builtin_sid_expected', [
	('-2147483646', False, False),  # default value
	('-2147483646', True, False),  # global group
	('-2147483643', True, True),  # local group
	('-2147483644', True, False),  # domain local group
	('-2147483640', True, False),  # universal group
])
def test_group_type(group_type, use_create_group_parameter, builtin_sid_expected, udm):
	"""Test the groupType attribute while creating groups"""
	if use_create_group_parameter:
		group = udm.create_group(adGroupType=group_type)[0]
	else:
		group = udm.create_group()[0]
	utils.verify_ldap_object(group, {'univentionGroupType': [group_type]})

	utils.wait_for_connector_replication()

	utils.verify_ldap_object(group, {'univentionGroupType': [group_type]})
	sid = _get_samba_sid(group)
	if _sid_is_builtin(sid):
		assert group_type == '-2147483643', 'New generated group has builtin sid: %s' % sid
	else:
		assert group_type != '-2147483643', 'New generated builtin group has no builtin sid: %s' % sid
