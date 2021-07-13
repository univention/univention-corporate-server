#!/usr/share/ucs-test/runner pytest-3
## desc: Append user memberships during groups/group modification
## tags: [udm,apptest]
## roles: [domaincontroller_master]
## exposure: careful
## packages:
##   - univention-config
##   - univention-directory-manager-tools


import pytest
import univention.testing.utils as utils
import univention.testing.udm as udm_test


@pytest.mark.tags('udm', 'apptest')
@pytest.mark.roles('domaincontroller_master')
@pytest.mark.exposure('careful')
def test_group_modification_append_users(udm):
	"""Append user memberships during groups/group modification"""
	# packages:
	#   - univention-config
	#   - univention-directory-manager-tools
	group = udm.create_group()[0]

	users = [udm.create_user(), udm.create_user()]

	udm.modify_object('groups/group', dn=group, append={'users': [user[0] for user in users]})
	utils.verify_ldap_object(group, {
		'uniqueMember': [user[0] for user in users],
		'memberUid': [user[1] for user in users]
	})
