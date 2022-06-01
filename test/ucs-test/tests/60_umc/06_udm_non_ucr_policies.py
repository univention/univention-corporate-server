#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: Test UMC object policies with non-UCR-policies
## bugs: [35314]
## roles:
##  - domaincontroller_master
##  - domaincontroller_backup
## exposure: dangerous

import pytest

from univention.testing.strings import random_username
from univention.testing.udm import UCSTestUDM
from univention.testing.umc import Client

from univention.config_registry import ConfigRegistry


@pytest.fixture
def udm_class():
	# the udm object needs to persist throuout the test.
	with UCSTestUDM() as udm:
		yield udm


# might not be needed if I can use the existing fixture :thinking:
@pytest.fixture
def ldap_base():
	with ConfigRegistry() as ucr:
		ucr.load()
		return ucr['ldap/base']


@pytest.fixture
def udm_objects():
	# creating all udm objects at the test start saves replication time.
	print(type(udm_class))
	udm_objects = {}
	udm_objects['base_container_dn'] = udm_class.create_object(
		'container/cn',
		name='base_test_container',
		position=ldap_base
	)
	udm_objects['intermediate_container_dn'] = udm_class.create_object(
		'container/cn',
		name='intermediate_test_container',
		position=udm_objects['base_container_dn']
	)

	udm_objects['base_policy_dn'] = udm_class.create_object(
			'policies/pwhistory',
			position="cn=policies," + ldap_base,
			name='umc_test_policy_base',
			length="5",
			pwQualityCheck=False,
			pwLength="5",
			**{"$policies$": {}}
		)
	udm_objects['intermediate_policy_dn'] = udm_class.create_object(
		'policies/pwhistory',
		position="cn=policies," + ldap_base,
		name='umc_test_policy_intermediate',
		length="4",
		pwQualityCheck=False,
		pwLength="4",
		**{"$policies$": {}}
	)
	udm_objects['user_policy_dn'] = udm_class.create_object(
		'policies/pwhistory',
		position="cn=policies," + ldap_base,
		name='umc_test_user_policy',
		length="3",
		pwQualityCheck=False,
		pwLength="3",
		**{"$policies$": {}}
	)

	udm_objects['user_dn'] = udm_class.create_user(
		position=udm_objects['intermediate_container_dn'],
		username='umc_test_user_' + random_username()
	)[0]

	return udm_objects


def test_check_single_and_multiple_policies(udm_class, udm_objects, ldap_base):
	"""Test UMC object policies with non-UCR-policies"""
	# bugs: [35314]
	udm_class.modify_object(
		'container/cn',
		dn=udm_objects['base_container_dn'],
		policy_reference=udm_objects['base_policy_dn'],
	)
	# check_policies('5', '5', user_dn)
	# def check_policies(length, pwLength, user_dn):
	# def get_user_policy(user_dn):
	options = [{
		"objectType": "users/user",
		"policies": [None],
		"policyType": "policies/pwhistory",
		"objectDN": udm_objects['user_dn'],
		"container": None
	}]

	client = Client.get_test_connection()
	object_policy = client.umc_command('udm/object/policies', options, 'navigation').result
	assert object_policy, "The object policy response result should not be empty"
	print(object_policy)

	length = '5'
	pwLength = '5'
	assert object_policy[0]['length']['value'] == length
	assert object_policy[0]['pwLength']['value'] == pwLength


	# udm_class.modify_object(
	# 	'container/cn',
	# 	dn=intermediate_container_dn,
	# 	policy_reference=intermediate_policy_dn
	# )
	# check_policies('4', '4', user_dn)

	# def check_fixed_and_empty_attributes(, user_dn):
	# 	udm_class.modify_object(
	# 		'policies/pwhistory',
	# 		dn=base_policy_dn,
	# 		fixedAttributes=['univentionPWLength']
	# 	)
	# 	check_policies('4', '5', user_dn)

	# 	udm_class.modify_object(
	# 		'policies/pwhistory',
	# 		dn=intermediate_policy_dn,
	# 		emptyAttributes=['univentionPWLength']
	# 	)
	# 	check_policies('4', '5', user_dn)
	# 	udm_class.modify_object(
	# 		'policies/pwhistory',
	# 		dn=base_policy_dn,
	# 		set={'fixedAttributes': ""}
	# 	)
	# 	check_policies('4', '', user_dn)

	# def check_required_excluded_object_classes(, user_dn):
	# 	udm_class.modify_object(
	# 		'policies/pwhistory',
	# 		dn=intermediate_policy_dn,
	# 		requiredObjectClasses=["sambaSamAccount"]
	# 	)
	# 	check_policies('4', '', user_dn)
	# 	udm_class.modify_object(
	# 		'policies/pwhistory',
	# 		dn=base_policy_dn,
	# 		prohibitedObjectClasses=["sambaSamAccount"]
	# 	)
	# 	check_policies('4', '', user_dn)

	# def main():


	# 		check_single_and_multiple_policies(user_dn, base_container_dn, intermediate_container_dn)
	# 		check_fixed_and_empty_attributes(user_dn)
	# 		check_required_excluded_object_classes(user_dn)


