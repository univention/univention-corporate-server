#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: Check if modifying the DNS forward zone of a computer only affects PTR records related to him
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
def test_modify_dns_forward_zone_ptr_record(udm, lo):
	"""Check if modifying the DNS forward zone of a computer only affects PTR records related to him"""
	dnsZone = udm.create_object('dns/forward_zone', zone='%s.%s' % (random_string(numeric=False), random_string(numeric=False)), nameserver='univention')
	dnsZone2 = udm.create_object('dns/forward_zone', zone='%s.%s' % (random_string(numeric=False), random_string(numeric=False)), nameserver='univention')

	rdnsZone = udm.create_object('dns/reverse_zone', subnet='10.20.30', nameserver='univention')
	rdnsZone2 = udm.create_object('dns/reverse_zone', subnet='10.20', nameserver='univention')

	ptrRecordEntry = '%s.%s.%s.' % (random_string(numeric=False), random_string(numeric=False), random_string(numeric=False))
	udm.create_object('dns/ptr_record', superordinate=rdnsZone, address='40', ptr_record=ptrRecordEntry)

	computerName = random_string()
	computer = udm.create_object('computers/windows', name=computerName, ip='10.20.40.40', dnsEntryZoneForward='%s 10.20.40.40' % dnsZone, dnsEntryZoneReverse='%s 10.20.40.40' % rdnsZone2)
	udm.modify_object('computers/windows', dn=computer, dnsEntryZoneForward='%s 10.20.40.40' % dnsZone2)

	ptr = lo.search(filter='(&(relativeDomainName=40)(pTRRecord=%s))' % ptrRecordEntry)[0][1]['pTRRecord']
	for entry in ptr:
		assert not entry.startswith(computerName.encode('UTF-8')), 'Found entry of the modified computer in the PTR record. PTR: %r' % ptr
