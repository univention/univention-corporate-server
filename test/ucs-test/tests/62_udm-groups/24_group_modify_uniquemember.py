#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: Test the allowed groupType changes
## tags: [udm,apptest, SKIP-UCSSCHOOL]
## roles: [domaincontroller_master]
## packages:
##   - univention-config
##   - univention-directory-manager-tools

import univention.testing.strings as uts


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
