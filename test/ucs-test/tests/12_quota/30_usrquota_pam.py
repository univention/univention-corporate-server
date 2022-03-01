#!/usr/share/ucs-test/runner pytest-3 -svvv
## desc: Test setting the quota through pam with usrquota
## roles-not: [basesystem]
## exposure: dangerous
## packages:
##   - univention-quota

from quota_test import QuotaCheck


def test_quota_pam():
	for fs_type in ['ext4', 'xfs']:
		print("Now checking fs type: {}".format(fs_type))
		quotaCheck = QuotaCheck(quota_type="usrquota", fs_type=fs_type)
		quotaCheck.test_quota_pam()


def test_quota_pam_policy_removal():
	for fs_type in ['ext4', 'xfs']:
		print("Now checking fs type: {}".format(fs_type))
		quotaCheck = QuotaCheck(quota_type="usrquota", fs_type=fs_type)
		quotaCheck.test_quota_pam_policy_removal()
