#!/usr/share/ucs-test/runner pytest-3
## desc: Test the groupType attribute while creating groups
## tags: [udm,apptest, SKIP-UCSSCHOOL]
## roles: [domaincontroller_master]
## exposure: dangerous
## packages:
##   - univention-config
##   - univention-directory-manager-tools

import pytest

import univention.testing.utils as utils


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
