#!/usr/share/ucs-test/runner pytest-3 -svvv
## desc: Test setting the quota through pam with usrquota
## roles-not: [basesystem]
## exposure: dangerous
## packages:
##   - univention-quota

import pytest

from quota_test import QuotaCheck


@pytest.mark.parametrize("fs_type", ["ext4", "xfs"])
def test_quota_pam(fs_type: str) -> None:
    quotaCheck = QuotaCheck(quota_type="usrquota", fs_type=fs_type)
    quotaCheck.test_quota_pam()


@pytest.mark.parametrize("fs_type", ["ext4", "xfs"])
def test_quota_pam_policy_removal(fs_type: str) -> None:
    quotaCheck = QuotaCheck(quota_type="usrquota", fs_type=fs_type)
    quotaCheck.test_quota_pam_policy_removal()
