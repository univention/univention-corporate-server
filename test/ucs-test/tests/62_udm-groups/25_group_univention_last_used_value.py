#!/usr/share/ucs-test/runner pytest-3
## desc: Create groups/group and check univentionLastUsedValue
## tags: [udm,apptest]
## roles: [domaincontroller_master]
## exposure: careful
## packages:
##   - univention-config
##   - univention-directory-manager-tools


import pytest
import random
import univention.uldap
import univention.testing.utils as utils


@pytest.mark.tags('udm', 'apptest')
@pytest.mark.roles('domaincontroller_master')
@pytest.mark.exposure('careful')
def test_group_univention_last_used_value(ucr, udm):
	"""Create groups/group and check univentionLastUsedValue"""
	# packages:
	#   - univention-config
	#   - univention-directory-manager-tools
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
