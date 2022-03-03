#!/usr/share/ucs-test/runner pytest-3
## desc: Test the allowed groupType changes
## tags: [udm,apptest, SKIP-UCSSCHOOL]
## roles: [domaincontroller_master]
## packages:
##   - univention-config
##   - univention-directory-manager-tools

from six.moves import range

import univention.testing.strings as uts
import univention.uldap


def _print(capsys, val):
	with capsys.disabled():
		print("\t %s " % (val,))


def _search(lo, val, capsys):
	res = lo.get(str(val)).get('memberUid')
	res1 = lo.get(str(val)).get('uniqueMember')
	strings = ["Group memberuid = ", str(res), " uniquemember  ", str(res1)]
	_print(capsys, ''.join([_f for _f in strings if _f]))
	assert res and res1


def _update_loop(capsys, ucr, udm, group1):
	lo = univention.uldap.getAdminConnection()
	username = uts.random_name()
	for i in range(5):
		user = 'uid=%s,cn=temp_%s,%s' % (username, i, ucr.get('ldap/base'),)
		strings = ["set user = ", user, " to group ", group1]
		_print(capsys, ''.join([_f for _f in strings if _f]))
		group1 = udm.modify_object('groups/group', dn=group1, users=user)
		_search(lo, group1, capsys)


def test_umd_memberUid(udm, ucr, capsys):
	# create
	group1 = udm.create_group(adGroupType="")[0]
	strings = ["create group = ", group1]
	_print(capsys, ''.join([_f for _f in strings if _f]))
	# validate memberuid after update users in group
	_update_loop(capsys, ucr, udm, group1)
	# remove group
	group1 = udm.remove_object('groups/group', dn=group1)
	if not group1:
		_print(capsys, "Remove group successfully  ")
