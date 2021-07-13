#!/usr/share/ucs-test/runner python3
## desc: Create groups/group with single letter name
## tags: [udm,apptest]
## roles: [domaincontroller_master]
## exposure: careful
## packages:
##   - univention-config
##   - univention-directory-manager-tools


import pytest
import univention.testing.strings as uts
import univention.testing.utils as utils


@pytest.mark.tags('udm', 'apptest')
@pytest.mark.roles('domaincontroller_master')
@pytest.mark.exposure('careful')
def test_group_creation_with_single_letter_name(udm):
	"""Create groups/group with single letter name"""
	# packages:
	#   - univention-config
	#   - univention-directory-manager-tools
	group = udm.create_group(name=uts.random_groupname(1))[0]
	utils.verify_ldap_object(group)
