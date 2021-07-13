#!/usr/share/ucs-test/runner pytest-3
## desc: Add user with single letter name to groups/group during creation
## tags: [udm,apptest]
## roles: [domaincontroller_master]
## exposure: careful
## packages:
##   - univention-config
##   - univention-directory-manager-tools


import pytest
import univention.testing.strings as uts
import univention.testing.utils as utils


@pytest.mark.tags('udm', 'apptest')
@pytest.mark.roles('domaincontroller_master')
@pytest.mark.exposure('careful')
def test_group_creation_set_single_letter_name_user(udm):
	"""Add user with single letter name to groups/group during creation"""
	# packages:
	#   - univention-config
	#   - univention-directory-manager-tools
	user = udm.create_user(name=uts.random_username(1))
	group = udm.create_group(users=user[0])[0]

	utils.verify_ldap_object(group, {'uniqueMember': [user[0]], 'memberUid': [user[1]]})
