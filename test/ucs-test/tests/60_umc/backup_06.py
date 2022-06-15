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

# only until i can package everything neatly into a pytest
from univention.config_registry import ConfigRegistry
ucr = ConfigRegistry()
ucr.load()
ldap_base = ucr['ldap/base']


def stuff(udm):
	base_container_dn = udm.create_object(
		'container/cn',
		name='base_test_container',
		position=ldap_base
	)
	intermediate_container_dn = udm.create_object(
		'container/cn',
		name='intermediate_test_container',
		position=base_container_dn
	)
	return (base_container_dn, intermediate_container_dn)

def test_check_single_and_multiple_policies(udm): # user_dn, base_container_dn, intermediate_container_dn):

		# create_test_policies()
		base_policy_dn = udm.create_object(
			'policies/pwhistory',
			position="cn=policies," + ldap_base,
			name='umc_test_policy_base',
			length="5",
			pwQualityCheck=False,
			pwLength="5",
			**{"$policies$": {}}
		)
		intermediate_policy_dn = udm.create_object(
			'policies/pwhistory',
			position="cn=policies," + ldap_base,
			name='umc_test_policy_intermediate',
			length="4",
			pwQualityCheck=False,
			pwLength="4",
			**{"$policies$": {}}
		)
		user_policy_dn = udm.create_object(
			'policies/pwhistory',
			position="cn=policies," + ldap_base,
			name='umc_test_user_policy',
			length="3",
			pwQualityCheck=False,
			pwLength="3",
			**{"$policies$": {}}
		)

		# create test users
		user_dn = udm.create_user(
			position=intermediate_container_dn,
			username='umc_test_user_' + random_username()
		)[0]

		# check stuff
		udm.modify_object(
			'container/cn',
			dn=base_container_dn,
			policy_reference=base_policy_dn
		)

		# def check_policies(length, pwLength, user_dn):
		# def get_user_policy(user_dn):
		# check_policies('5', '5', user_dn)
		length = '5'
		pwLength = '5'

		options = [{
			"objectType": "users/user",
			"policies": [None],
			"policyType": "policies/pwhistory",
			"objectDN": user_dn,
			"container": None
		}]

		flavor = "navigation"
		client = Client.get_test_connection()
		object_policy = client.umc_command('udm/object/policies', options, flavor).result
		assert object_policy, "The object policy response result should not be empty"
		print(object_policy)

		assert length == object_policy[0]['length']['value']
		assert pwLength == object_policy[0]['pwLength']['value']

		# udm.modify_object(
		# 	'container/cn',
		# 	dn=intermediate_container_dn,
		# 	policy_reference=intermediate_policy_dn
		# )
		# check_policies('4', '4', user_dn)

		# self.check_fixed_and_empty_attributes(user_dn)
		# self.check_required_excluded_object_classes(user_dn)



# class TestUMCNonUCRPolicies():


# 	def check_fixed_and_empty_attributes(self, user_dn):
# 		self.UDM.modify_object(
# 			'policies/pwhistory',
# 			dn=self.base_policy_dn,
# 			fixedAttributes=['univentionPWLength']
# 		)
# 		check_policies('4', '5', user_dn)

# 		self.UDM.modify_object(
# 			'policies/pwhistory',
# 			dn=self.intermediate_policy_dn,
# 			emptyAttributes=['univentionPWLength']
# 		)
# 		check_policies('4', '5', user_dn)
# 		self.UDM.modify_object(
# 			'policies/pwhistory',
# 			dn=self.base_policy_dn,
# 			set={'fixedAttributes': ""}
# 		)
# 		check_policies('4', '', user_dn)

# 	def check_required_excluded_object_classes(self, user_dn):
# 		self.UDM.modify_object(
# 			'policies/pwhistory',
# 			dn=self.intermediate_policy_dn,
# 			requiredObjectClasses=["sambaSamAccount"]
# 		)
# 		check_policies('4', '', user_dn)
# 		self.UDM.modify_object(
# 			'policies/pwhistory',
# 			dn=self.base_policy_dn,
# 			prohibitedObjectClasses=["sambaSamAccount"]
# 		)
# 		check_policies('4', '', user_dn)

