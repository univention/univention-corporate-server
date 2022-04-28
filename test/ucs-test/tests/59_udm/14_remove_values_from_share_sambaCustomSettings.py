#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: Test removing values from share
## bugs: [41072]
## roles:
##  - domaincontroller_master
## tags: [apptest]
## exposure: dangerous

import pytest

from univention.testing import utils


@pytest.mark.tags('apptest')
@pytest.mark.roles('domaincontroller_master')
@pytest.mark.exposure('dangerous')
def test_remove_values_from_share_sambaCustomSettings(udm):
	"""Test removing values from share"""
	# bugs: [41072]
	share = udm.create_object('shares/share', name='test', host='localhost', path='/path/', sambaCustomSettings='"follow symlinks" "yes"')
	utils.verify_ldap_object(share, {'univentionShareSambaCustomSetting': ['follow symlinks = yes']})
	udm.modify_object('shares/share', dn=share, remove={'sambaCustomSettings': ['"follow symlinks" "yes"']})
	utils.verify_ldap_object(share, {'univentionShareSambaCustomSetting': []})
