#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: Test PTR records are removed when no ptr record would be left over and multiple IP addresses are assigned
## tags: [udm-computers,apptest]
## roles: [domaincontroller_master]
## bugs: [44710, 51736]
## exposure: careful
## packages:
##   - univention-config
##   - univention-directory-manager-tools

import pytest

from univention.testing.strings import random_string


@pytest.mark.tags('udm-computers', 'apptest')
@pytest.mark.roles('domaincontroller_master')
@pytest.mark.exposure('careful')
def test_removal_of_leftover_ptr_record_with_multiple_ip_addresses(udm, verify_ldap_object):
		"""Test PTR records are removed when no ptr record would be left over and multiple IP addresses are assigned"""
		# bugs: [44710, 51736]
		domainname = random_string(numeric=False)
		tld = random_string(numeric=False)
		dnsZone1 = udm.create_object('dns/forward_zone', zone='%s.%s' % (domainname, tld), nameserver='univention')
		dnsZone2 = udm.create_object('dns/forward_zone', zone='%s2.%s' % (domainname, tld), nameserver='univention')
		rdnsZone = udm.create_object('dns/reverse_zone', subnet='10.20.30', nameserver='univention')

		computer_name = random_string()
		computer = udm.create_object('computers/windows', name=computer_name, ip='10.20.30.60', dnsEntryZoneForward='%s 10.20.30.60' % dnsZone1, dnsEntryZoneReverse='%s 10.20.30.60' % rdnsZone)
		udm.modify_object('computers/windows', dn=computer, append={'dnsEntryZoneForward': ['%s 10.20.30.60' % dnsZone2]})

		ptr_record = 'relativeDomainName=60,%s' % (rdnsZone,)
		udm._cleanup.setdefault('dns/ptr_record', []).append(ptr_record)  # Workaround for being able to modify it:
		udm.modify_object('dns/ptr_record', dn=ptr_record, append={'ptr_record': ['%s.%s2.%s.' % (computer_name, domainname, tld)]})

		remove = {
			'dnsEntryZoneForward': ['%s 10.20.30.60' % dnsZone1, '%s 10.20.30.60' % dnsZone2],
			'dnsEntryZoneReverse': ['%s 10.20.30.60' % rdnsZone],
		}
		append = {
			'dnsEntryZoneForward': ['%s 10.20.30.6' % dnsZone1, '%s 10.20.30.6' % dnsZone2],
			'dnsEntryZoneReverse': ['%s 10.20.30.6' % rdnsZone],
		}
		udm.modify_object('computers/windows', dn=computer, ip='10.20.30.6', remove=remove, append=append)
		verify_ldap_object(ptr_record, should_exist=False)
		verify_ldap_object('relativeDomainName=6,%s' % (rdnsZone,), {
			'pTRRecord': [
				('%s.%s.%s.' % (computer_name, domainname, tld)).encode('UTF-8'),
				('%s.%s2.%s.' % (computer_name, domainname, tld)).encode('UTF-8')]
		})
