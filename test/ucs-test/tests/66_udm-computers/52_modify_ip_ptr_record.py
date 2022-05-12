#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: Check if changing IP address of a computer does only result in removing the related PTR record if his entry was the last in it
## tags: [udm-computers,apptest]
## roles: [domaincontroller_master]
## exposure: careful
## packages:
##   - univention-config
##   - univention-directory-manager-tools

import pytest

from univention.testing.strings import random_string


@pytest.mark.tags('udm-computers', 'apptest')
@pytest.mark.roles('domaincontroller_master')
@pytest.mark.exposure('careful')
def test_modify_ip_ptr_record(udm, lo):
	"""Check if modifying the DNS forward zone of a computer only affects PTR records related to him"""
	dnsZone = udm.create_object('dns/forward_zone', zone='%s.%s' % (random_string(numeric=False), random_string(numeric=False)), nameserver='univention')
	rdnsZone = udm.create_object('dns/reverse_zone', subnet='10.20.30', nameserver='univention')

	ptrRecordEntry = '%s.%s.%s.' % (random_string(numeric=False), random_string(numeric=False), random_string(numeric=False))
	udm.create_object('dns/ptr_record', superordinate=rdnsZone, address='50', ptr_record=ptrRecordEntry)

	computer = udm.create_object('computers/windows', name=random_string(), ip='10.20.30.60', dnsEntryZoneForward='%s 10.20.30.60' % dnsZone, dnsEntryZoneReverse='%s 10.20.30.60' % rdnsZone)
	udm.modify_object('computers/windows', dn=computer, ip='10.20.30.50')

	ptr = lo.search(filter='(&(relativeDomainName=50)(pTRRecord=%s))' % ptrRecordEntry)
	assert len(ptr) >= 1, 'Test FAILED. Could not find PTR record created anymore after modifying computers IP'
