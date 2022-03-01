#!/usr/share/ucs-test/runner pytest-3 -s
## desc: Create/modify groups/group with name which is already in use
## tags: [udm,apptest]
## roles: [domaincontroller_master]
## exposure: careful
## packages:
##   - univention-config
##   - univention-directory-manager-tools


import pytest

import univention.testing.udm as udm_test


def test_group_creation_with_name_already_in_use(udm, ucr):
	"""Create groups/group with name which is already in use"""
	group_name = udm.create_group(position=ucr['ldap/base'])[1]

	with pytest.raises(udm_test.UCSTestUDM_CreateUDMObjectFailed) as exc:
		udm.create_group(name=group_name)
	assert 'Object exists: (group)' in str(exc.value)


def test_group_modification_with_name_already_in_use(udm, ucr):
	"""Modify groups/group with name which is already in use"""
	group = udm.create_group(position=ucr['ldap/base'])[0]
	group_name = udm.create_group()[1]

	with pytest.raises(udm_test.UCSTestUDM_ModifyUDMObjectFailed) as exc:
		udm.modify_object('groups/group', dn=group, name=group_name)
	assert 'The groupname is already in use as groupname or as username' in str(exc.value)
