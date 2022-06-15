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


@pytest.fixture(scope='class')
def udm_class():
	# the udm object needs to persist throuout the test.
	with UCSTestUDM() as udm:
		yield udm


@pytest.fixture(scope='class')
def udm_objects(udm_class, ldap_base):
	# creating all udm objects at the test start saves replication time.
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


class Test_UCR:
	@pytest.mark.parametrize('dn, kwargs, length, pwLength', [
		# ('base_container_dn', 'base_policy_dn', '5', '5'),
		# ('intermediate_container_dn', 'intermediate_policy_dn', '4', '4'),

		('base_policy_dn', {'fixedAttributes': ['univentionPWLength']}, '4', '5'),
		# ('intermediate_policy_dn', {'emptyAttributes': ['univentionPWLength']}, '4', '5'),
		# ('base_policy_dn', {'set': {'fixedAttributes': ""}}, '4', ''),

		# ('intermediate_policy_dn', {'requiredObjectClasses': ['sambaSamAccount']}, '4', '4'),
		# ('base_policy_dn', {'prohibitedObjectClasses': ['sambaSamAccount']}, '4', ''),
	])
	def test_udm_non_ucr_policies(self, udm_class, udm_objects, dn, kwargs, length, pwLength):
		"""Test UMC object policies with non-UCR-policies"""
		# bugs: [35314]

		# unfortunately, objects provided by fixtures cant be parametrized
		if kwargs in ('base_policy_dn', 'intermediate_policy_dn'):
			kwargs = {'policy_reference': udm_objects[kwargs]}
		print('\n\n', kwargs)
		print(type(kwargs), '\n\n')

		udm_class.modify_object(
			'container/cn',
			dn=udm_objects[dn],
			fixedAttributes=['univentionPWLength']
			# **kwargs
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

		assert object_policy[0]['length']['value'] == length
		assert object_policy[0]['pwLength']['value'] == pwLength
