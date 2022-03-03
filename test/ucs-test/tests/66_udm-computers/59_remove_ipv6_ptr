#!/usr/share/ucs-test/runner python3
## desc: Removing one of multiple DNS PTR RR works
## tags: [udm-computers]
## roles: [domaincontroller_master]
## bugs: [53213]
## exposure: careful
## packages:
##   - univention-config
##   - univention-directory-manager-tools

import univention.testing.strings as uts
import univention.testing.udm as udm_test
import univention.testing.utils as utils

IP4 = '10.20.40.40'
IP6 = '2001:0db8:0001:0002:0000:0000:0000:000f'


if __name__ == '__main__':
	domainname = '%s.%s' % (uts.random_string(numeric=False), uts.random_string(numeric=False))
	computerName = uts.random_string()

	with udm_test.UCSTestUDM() as udm:
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
		utils.verify_ldap_object(ptr_record, should_exist=False)
