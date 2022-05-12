#!/usr/share/ucs-test/runner pytest-3 -s -l  -vv
## desc: Validate handling of "ntCompatibility" attribute in computers/windows module
## tags: [udm-computers]
## roles: [domaincontroller_master]
## exposure: careful
## packages:
##   - univention-config
##   - univention-directory-manager-tools

import passlib.hash
import pytest

from univention.testing.strings import random_string


@pytest.mark.tags('udm-computers')
@pytest.mark.roles('domaincontroller_master')
@pytest.mark.exposure('careful')
def test_windows_check_ntCompatibility(udm, verify_ldap_object):
	"""Validate handling of "ntCompatibility" attribute in computers/windows module"""
	windowsHostName = random_string()
	verify_ldap_object(udm.create_object('computers/windows', name=windowsHostName, ntCompatibility='1'), {'sambaNTPassword': [passlib.hash.nthash.hash(windowsHostName.lower()).upper()]})
