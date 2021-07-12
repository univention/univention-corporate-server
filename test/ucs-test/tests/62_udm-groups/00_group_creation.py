#!/usr/share/ucs-test/runner pytest-3
## desc: Create groups/group
## tags: [udm,apptest]
## roles: [domaincontroller_master]
## exposure: careful
## packages:
##   - univention-config
##   - univention-directory-manager-tools


import pytest
import univention.testing.utils as utils


@pytest.mark.tags('udm', 'apptest')
@pytest.mark.roles('domaincontroller_master')
@pytest.mark.exposure('careful')
def test_group_creation(udm):
	"""Create groups/group"""
	# packages:
	#   - univention-config
	#   - univention-directory-manager-tools
	group = udm.create_group()[0]
	utils.verify_ldap_object(group)
