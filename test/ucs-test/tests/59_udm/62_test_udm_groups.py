#!/usr/share/ucs-test/runner pytest-3
# -*- coding: utf-8 -*-
## desc: Test groups/group
## tags: [udm,udm-groups,apptest]
## roles: [domaincontroller_master]
## exposure: careful
## packages:
##   - univention-config
##   - univention-directory-manager-tools

import grp
import os
import random
import subprocess
import tempfile

import pytest
from ldap.dn import dn2str, str2dn

import univention.testing.strings as uts
import univention.testing.udm as udm_test
import univention.testing.utils as utils
import univention.uldap
from univention.testing.ucs_samba import wait_for_s4connector


@pytest.mark.tags('udm', 'apptest')
@pytest.mark.roles('domaincontroller_master')
@pytest.mark.exposure('careful')
def test_group_creation(udm):
	"""Create groups/group"""

	group = udm.create_group()[0]
	utils.verify_ldap_object(group)


@pytest.mark.tags('udm', 'apptest')
@pytest.mark.xfail(reason='Bug #35521')
@pytest.mark.roles('domaincontroller_master')
@pytest.mark.exposure('careful')
def test_group_creation_with_umlaut_in_name(udm):
	"""Create groups/group with umlaut in name"""
	# bugs: [35521]
	# This test case is strange: Initially (2013) it should check that
	# the "gid" UDM syntax doesn't allow non-ASCII chracters.
	# But then, in 2014 Bug #35521 made a change to allow non-ASCII characters,
	# but that adjustment only had an effect for group names passed as unicode,
	# which probably is the case in case a UDM group is created via AD-Connector
	# So we have an inconsistent behavior here with PYthon2, Umlauts in group
	# names are allowed when passed as unicode, but, as the continued success of
	# this test case here shows, they apparently are not allowed, when passed
	# via udm-cli (probably as UTF-8 bytes).
	#
	# I set this test case to SKIP for now, because it didn't work any longer
	# for Python3 UDM, at the time of writing, as the value passed to the
	# "gid" UDM syntax is unicode now even when used from udm-cli. I don't think
	# we want to explicitly lower the bar again to the state of 2013.
	# Also I think it is more consistend to always allow Umlaut characters in
	# group names, not only when used from python, as done on the AD-Connector.
	# This should not be a problem since they are stored in LDAP as UTF-8.

	with pytest.raises(udm_test.UCSTestUDM_CreateUDMObjectFailed):
		udm.create_group(name='%säÄöÖüÜ%s' % (uts.random_groupname(4), uts.random_groupname(4)))[0]
		# udm.create_group(name='Contrôleurs de domaine d’entreprise')[0]


@pytest.mark.tags('udm', 'apptest')
@pytest.mark.roles('domaincontroller_master')
@pytest.mark.exposure('careful')
def test_group_creation_with_single_letter_name(udm):
	"""Create groups/group with single letter name"""

	group = udm.create_group(name=uts.random_groupname(1))[0]
	utils.verify_ldap_object(group)


@pytest.mark.tags('udm', 'apptest')
@pytest.mark.roles('domaincontroller_master')
@pytest.mark.exposure('careful')
def test_group_modification_append_users(udm):
	"""Append user memberships during groups/group modification"""

	group = udm.create_group()[0]

	users = [udm.create_user(), udm.create_user()]

	udm.modify_object('groups/group', dn=group, append={'users': [user[0] for user in users]})
	utils.verify_ldap_object(group, {
		'uniqueMember': [user[0] for user in users],
		'memberUid': [user[1] for user in users]
	})


@pytest.mark.tags('udm', 'apptest')
@pytest.mark.roles('domaincontroller_master')
@pytest.mark.exposure('careful')
def test_group_creation_set_single_letter_name_user(udm):
	"""Add user with single letter name to groups/group during creation"""

	user = udm.create_user(name=uts.random_username(1))
	group = udm.create_group(users=user[0])[0]

	utils.verify_ldap_object(group, {'uniqueMember': [user[0]], 'memberUid': [user[1]]})


@pytest.mark.tags('udm', 'apptest')
@pytest.mark.roles('domaincontroller_master')
@pytest.mark.exposure('careful')
def test_group_modification_append_nestedGroups(udm):
	"""Append nestedGroups during groups/group modification"""

	group = udm.create_group()[0]
	nested_groups = [udm.create_group()[0], udm.create_group()[0]]

	udm.modify_object('groups/group', dn=group, append={'nestedGroup': nested_groups})
	utils.verify_ldap_object(group, {'uniqueMember': nested_groups})


@pytest.mark.tags('udm', 'apptest')
@pytest.mark.roles('domaincontroller_master')
@pytest.mark.exposure('careful')
def test_group_creation_set_single_letter_name_nestedGroup(udm):
	"""Add nestedGroup with single letter name to groups/group during creation"""

	nestedGroup = udm.create_group(name=uts.random_groupname(1))[0]
	group = udm.create_group(nestedGroup=nestedGroup)[0]

	utils.verify_ldap_object(group, {'uniqueMember': [nestedGroup]})


@pytest.mark.tags('udm', 'apptest')
@pytest.mark.roles('domaincontroller_master')
@pytest.mark.exposure('careful')
def test_rename_a_group_which_contains_a_nestedGroup(udm):
	"""Rename group/groups which contains a nested groups/group"""

	nested_group = udm.create_group()[0]
	group = udm.create_group(nestedGroup=nested_group)[0]

	new_group_name = uts.random_groupname()
	udm.modify_object('groups/group', dn=group, name=new_group_name)
	group = 'cn=%s,%s' % (new_group_name, ','.join(group.split(',')[1:]))
	utils.verify_ldap_object(group, {'uniqueMember': [nested_group]})


@pytest.mark.tags('udm')
@pytest.mark.roles('domaincontroller_master')
@pytest.mark.exposure('careful')
def test_rename_a_neasted_group(udm):
	"""Rename a nested groups/group"""

	nested_group = udm.create_group()[0]
	group = udm.create_group(nestedGroup=nested_group)[0]
	wait_for_s4connector()
	new_nested_group_name = uts.random_groupname()
	udm.modify_object('groups/group', dn=nested_group, name=new_nested_group_name)
	wait_for_s4connector()
	nested_group = 'cn=%s,%s' % (new_nested_group_name, ','.join(nested_group.split(',')[1:]))
	utils.verify_ldap_object(group, {'uniqueMember': [nested_group]})


@pytest.mark.tags('udm', 'apptest')
@pytest.mark.roles('domaincontroller_master')
@pytest.mark.exposure('careful')
def test_group_creation_with_name_already_in_use(udm, ucr):
	"""Create groups/group with name which is already in use"""
	group_name = udm.create_group(position=ucr['ldap/base'])[1]

	with pytest.raises(udm_test.UCSTestUDM_CreateUDMObjectFailed) as exc:
		udm.create_group(name=group_name)
	assert 'Object exists: (group)' in str(exc.value)


@pytest.mark.tags('udm', 'apptest')
@pytest.mark.roles('domaincontroller_master')
@pytest.mark.exposure('careful')
def test_group_modification_with_name_already_in_use(udm, ucr):
	"""Modify groups/group with name which is already in use"""
	group = udm.create_group(position=ucr['ldap/base'])[0]
	group_name = udm.create_group()[1]

	with pytest.raises(udm_test.UCSTestUDM_ModifyUDMObjectFailed) as exc:
		udm.modify_object('groups/group', dn=group, name=group_name)
	assert 'The groupname is already in use as groupname or as username' in str(exc.value)


@pytest.mark.tags('udm')
@pytest.mark.roles('domaincontroller_master')
@pytest.mark.exposure('careful')
def test_group_creation_with_same_name_as_existing_user(udm):
	"""Create groups/group with the same name as an existing user"""

	name = uts.random_name()

	udm.create_user(username=name)[0]

	with pytest.raises(udm_test.UCSTestUDM_CreateUDMObjectFailed):
		udm.create_group(name=name)


@pytest.mark.tags('udm', 'apptest')
@pytest.mark.roles('domaincontroller_master')
@pytest.mark.exposure('careful')
def test_remove_user_which_is_group_member(udm):
	"""Remove a user which is member in a groups/group"""
	user = udm.create_user()
	group = udm.create_group(users=user[0], wait_for=True)[0]
	utils.verify_ldap_object(group, {'memberUid': [user[1]], 'uniqueMember': [user[0]]})

	udm.remove_object('users/user', dn=user[0])
	utils.verify_ldap_object(group, {'memberUid': [], 'uniqueMember': []})


@pytest.mark.tags('udm', 'apptest')
@pytest.mark.roles('domaincontroller_master')
@pytest.mark.exposure('careful')
def test_indirect_group_user_memberships(udm):
	"""Test indirect group memberships of users"""

	group = udm.create_group()
	nested_group = udm.create_group(memberOf=group[0])
	user = udm.create_user(groups=nested_group[0])

	for group in grp.getgrall():
		if group.gr_name == group[1]:
			assert user[1] in group.gr_mem, 'User %s is no indirect member of group %s' % (user[1], group[1])
			break


@pytest.mark.tags('udm', 'apptest')
@pytest.mark.roles('domaincontroller_master')
@pytest.mark.exposure('careful')
def test_indirect_group_user_memberships_file_access(udm):
	"""Access file as user of nested group of group of files owner"""
	# TODO: test the opposite, reading is prevented by a user not in those groups

	group = udm.create_group()[0]
	nested_group = udm.create_group(memberOf=group)[0]

	file_owner = udm.create_user(primaryGroup=group)
	another_user = udm.create_user(groups=nested_group)

	utils.wait_for_replication_and_postrun()
	utils.wait_for_replication_and_postrun()

	# create file as user "file_owner" and change permissions to 060 (read/write group only)
	with tempfile.NamedTemporaryFile("w+", dir='/var/tmp') as fd:
		fd.write('foo')
		fd.flush()
		os.remove(fd.name)
		assert not os.path.exists(fd.name)

		subprocess.check_call(['su', file_owner[1], '-c', 'touch %(file)s; chmod 070 %(file)s' % {'file': fd.name}])
		# test reading as "another_user"
		subprocess.check_call(['su', another_user[1], '-c', 'cat %s' % fd.name])

		# test writing as "another_user"
		subprocess.check_call(['su', another_user[1], '-c', 'touch %s' % fd.name])


@pytest.mark.tags('udm')
@pytest.mark.roles('domaincontroller_master')
@pytest.mark.exposure('careful')
def test_group_modification_recursion_set_memberOf_to_self(udm):
	"""groups/group recursion due setting self as memberOf during modification"""
	# bugs: [13008]

	group = udm.create_group()[0]

	with pytest.raises(udm_test.UCSTestUDM_ModifyUDMObjectFailed):
		udm.modify_object('groups/group', dn=group, memberOf=group)


@pytest.mark.tags('udm')
@pytest.mark.roles('domaincontroller_master')
@pytest.mark.exposure('careful')
def test_group_creation_recursion_set_nestedGroup_to_self(udm):
	"""groups/group recursion due setting self as nestedGroup during creation"""
	# bugs: [13008]

	group_name = uts.random_groupname()
	with pytest.raises(udm_test.UCSTestUDM_CreateUDMObjectFailed):
		udm.create_group(name=group_name, nestedGroup='cn=%s,cn=groups,%s' % (group_name, udm.LDAP_BASE))


@pytest.mark.tags('udm')
@pytest.mark.roles('domaincontroller_master')
@pytest.mark.exposure('careful')
def test_group_creation_recursion_set_memberOf_to_self(udm):
	"""groups/group recursion due setting itself as memberOf during creation"""
	# bugs: [13008]

	group_name = uts.random_groupname()
	with pytest.raises(udm_test.UCSTestUDM_CreateUDMObjectFailed):
		udm.create_group(memberOf='cn=%s,cn=groups,%s' % (group_name, udm.LDAP_BASE))


@pytest.mark.tags('udm')
@pytest.mark.roles('domaincontroller_master')
@pytest.mark.exposure('careful')
def test_group_modification_recursion_set_nestedGroup_to_self(udm):
	"""groups/group recursion due setting self as nestedGroup during modification"""
	# bugs: [13008]

	group = udm.create_group()[0]

	with pytest.raises(udm_test.UCSTestUDM_ModifyUDMObjectFailed):
		udm.modify_object('groups/group', dn=group, nestedGroup=group)


@pytest.mark.tags('udm')
@pytest.mark.roles('domaincontroller_master')
@pytest.mark.exposure('careful')
def self_group_modification_recursion_set_nestedGroup_to_group_containing_self(udm):
	"""groups/group recursion due setting group as nestedGroup which already contains self as nested group during modification"""
	# bugs: [13008]

	group = udm.create_group()[0]
	group2 = udm.create_group(nestedGroup=group)[0]

	with pytest.raises(udm_test.UCSTestUDM_ModifyUDMObjectFailed):
		udm.modify_object('groups/group', dn=group, nestedGroup=group2)


@pytest.mark.tags('udm')
@pytest.mark.roles('domaincontroller_master')
@pytest.mark.exposure('careful')
def test_group_modification_recursion_set_memberOf_to_group_which_is_member_of_self(udm):
	"""groups/group recursion due setting self as memberOf in group which already is member of self during modification"""

	group = udm.create_group()[0]
	group2 = udm.create_group(memberOf=group)[0]

	with pytest.raises(udm_test.UCSTestUDM_ModifyUDMObjectFailed):
		udm.modify_object('groups/group', dn=group, memberOf=group2)


@pytest.mark.tags('udm')
@pytest.mark.roles('domaincontroller_master')
@pytest.mark.exposure('careful')
def test_group_removal(udm):
	"""Remove groups/group"""

	group = udm.create_group(wait_for=True)[0]

	udm.remove_object('groups/group', dn=group)
	utils.verify_ldap_object(group, should_exist=False)


@pytest.mark.tags('udm')
@pytest.mark.roles('domaincontroller_master')
@pytest.mark.exposure('careful')
def test_group_posix_only(udm):
	"""Create a group with posix option only"""
	utils.stop_s4connector()
	group = udm.create_group(options=['posix'])[0]
	utils.verify_ldap_object(group, {'objectClass': ['top', 'posixGroup', 'univentionGroup', 'univentionObject']})
	utils.start_s4connector()


@pytest.mark.tags('udm')
@pytest.mark.roles('domaincontroller_master')
@pytest.mark.exposure('careful')
def test_group_different_case(udm):
	"""Check different case in LDAP DN of group modifications"""

	user = udm.create_user()[0]
	nested_group = udm.create_group()[0]
	computer = udm.create_object('computers/windows', name=uts.random_string())

	group = udm.create_group(hosts=computer, users=user, nestedGroup=nested_group, wait_for=True)[0]
	utils.verify_ldap_object(group, {'uniqueMember': [user, nested_group, computer]})

	def changed_cases(members):
		def mixed_case(attr):
			return attr[0].lower() + attr[1:].upper()
		variants = []
		for transform in (str.lower, str.upper, mixed_case):
			result = {}
			for key, dn in members.items():
				dn = str2dn(dn)
				rdn = dn.pop(0)
				rdn = [tuple([transform(str(rdn[0][0]))] + list(rdn[0][1:]))]
				dn.insert(0, rdn)
				result[key] = [dn2str(dn)]
			variants.append(result)
		return variants

	for members in changed_cases(dict(hosts=computer, users=user, nestedGroup=nested_group)):
		print('Modifying group with changed members: %r' % (members,))
		udm.modify_object('groups/group', dn=group, remove=dict(hosts=[computer], users=[user], nestedGroup=[nested_group]), wait_for=True)
		# FIXME: Bug #43286: udm.modify_object('groups/group', dn=group, remove=members)
		utils.verify_ldap_object(group, {'uniqueMember': []})

		udm.modify_object('groups/group', dn=group, append=members, wait_for=True)
		utils.verify_ldap_object(group, {'uniqueMember': [user, nested_group, computer]})


@pytest.mark.tags('udm', 'apptest')
@pytest.mark.roles('domaincontroller_master')
@pytest.mark.exposure('careful')
def test_group_univention_last_used_value(ucr, udm):
	"""Create groups/group and check univentionLastUsedValue"""

	luv_dn = 'cn=gidNumber,cn=temporary,cn=univention,%s' % (ucr.get('ldap/base'),)
	lo = univention.uldap.getAdminConnection()

	lastUsedValue_old = lo.get(luv_dn).get('univentionLastUsedValue', [-1])[0]
	group_dn = udm.create_group()[0]
	utils.verify_ldap_object(group_dn)
	lastUsedValue_new = lo.get(luv_dn).get('univentionLastUsedValue', [-1])[0]
	assert lastUsedValue_old != lastUsedValue_new, 'Create group with automatic gidNumber: univentionLastUsedValue did not change, but it should!'

	lastUsedValue_old = lo.get(luv_dn).get('univentionLastUsedValue', [-1])[0]
	gidNumber = str(random.randint(100000, 200000))
	group_dn = udm.create_group(gidNumber=gidNumber)[0]
	utils.verify_ldap_object(group_dn, expected_attr={'gidNumber': [gidNumber]})
	lastUsedValue_new = lo.get(luv_dn).get('univentionLastUsedValue', [-1])[0]
	assert lastUsedValue_old == lastUsedValue_new, 'Create group with specified gidNumber: univentionLastUsedValue did change, but it should not!'

	# Please note: modification of gidNumber is not allowed according to groups/group.py --> not tested here
