#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: Test removing values from UCR policy
## bugs: [43562]
## roles:
##  - domaincontroller_master
## exposure: dangerous

import pytest

from univention.testing import utils


@pytest.mark.tags('udm')
@pytest.mark.roles('domaincontroller_master')
@pytest.mark.exposure('careful')
def test_remove_values_from_ucr_policy(udm):
	policy = udm.create_object('policies/registry', name='test', registry=['foo bar', 'bar baz'])
	utils.verify_ldap_object(policy, {'univentionRegistry;entry-hex-666f6f': ['bar'], 'univentionRegistry;entry-hex-626172': ['baz']})
	udm.modify_object('policies/registry', dn=policy, remove={'registry': ['bar baz']})
	utils.verify_ldap_object(policy, {'univentionRegistry;entry-hex-666f6f': ['bar']})
