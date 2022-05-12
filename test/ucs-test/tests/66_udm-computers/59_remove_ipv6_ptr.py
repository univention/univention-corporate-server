#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: Removing one of multiple DNS PTR RR works
## tags: [udm-computers]
## roles: [domaincontroller_master]
## bugs: [53213]
## exposure: careful
## packages:
##   - univention-config
##   - univention-directory-manager-tools

import pytest

from univention.testing.strings import random_string

IP4 = '10.20.40.40'
IP6 = '2001:0db8:0001:0002:0000:0000:0000:000f'


@pytest.mark.tags('udm-computers')
@pytest.mark.roles('domaincontroller_master')
@pytest.mark.exposure('careful')
def test_remove_ipv4_ptr(udm, verify_ldap_object):
		"""Removing one of multiple DNS PTR RR works"""
		# bugs: [53213]
		domainname = '%s.%s' % (random_string(numeric=False), random_string(numeric=False))
		computerName = random_string()

		dnsZone = udm.create_object('dns/forward_zone', zone=domainname, nameserver='univention')

		rdnsZone4 = udm.create_object('dns/reverse_zone', subnet='10.20', nameserver='univention')
		rdnsZone6 = udm.create_object('dns/reverse_zone', subnet='2001:0db8:0001:0002', nameserver='univention')

		computer = udm.create_object(
			'computers/ipmanagedclient',
			name=computerName,
			ip=[IP4, IP6],
			dnsEntryZoneForward=['%s %s' % (dnsZone, ip) for ip in (IP4, IP6)],
			dnsEntryZoneReverse=['%s %s' % (zone, ip) for (zone, ip) in ((rdnsZone4, IP4), (rdnsZone6, IP6))],
		)
		udm.modify_object('computers/ipmanagedclient', dn=computer, remove={'ip': [IP6]})

		ptr_record = 'relativeDomainName=f.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0,%s' % (rdnsZone6,)
		verify_ldap_object(ptr_record, should_exist=False)
