#!/usr/share/ucs-test/runner /usr/bin/py.test -s
## desc: Creates DNS forward zone entries with invalid names
## bugs: [41005]
## roles:
##  - domaincontroller_master
## packages:
##   - univention-config
##   - univention-directory-manager-tools
## tags:
##  - skip_admember
##  - SKIP
## exposure: dangerous

from __future__ import print_function

import os.path

import pytest
import ldap.dn
import subprocess

import univention.testing.udm as udm_test
from essential.dns_helper import resolveDnsEntry, NXDOMAIN
from univention.testing import ucr as _ucr, utils

NAMED_CACHE_DIR = "/var/cache/bind"
NAMED_CONF_DIR = "/etc/bind/univention.conf.d"
PROXY_CACHE_DIR = "/var/cache/univention-bind-proxy"


@pytest.mark.parametrize('zone', [
	'.proxy',
	'.zone',
	'foo.proxy',
	'foo.zone',
	'.',
	'..',
	'../../../../etc/passwd2',
	'/etc/passwd3',
	'0.in-addr.arpa',
	'127.in-addr.arpa',
	'255.in-addr.arpa',
	'fo"o',
])
def test_invalid_zone_names(zone):
	lo = utils.get_ldap_connection()
	with udm_test.UCSTestUDM() as udm, _ucr.UCSTestConfigRegistry() as ucr:
		pos = 'cn=dns,%s' % (udm.LDAP_BASE,)
		dn = 'zoneName=%s,%s' % (ldap.dn.escape_dn_chars(zone), pos)
		attrs = {
			'nSRecord': ['%(hostname)s.%(domainname)s.'],
			'objectClass': ['dNSZone', 'top'],
			'dNSTTL': ['10800'],
			'relativeDomainName': ['@'],
			'zoneName': [zone],
			'sOARecord': ['%(hostname)s.%(domainname)s. root.%(domainname)s. 9 28800 7200 604800 10800'],
		}
		al = [(key, [v % dict(ucr) for v in val]) for key, val in attrs.items()]
		print(('Creating', dn))
		lo.add(dn, al)
		try:
			utils.wait_for_replication_and_postrun()
			check(zone)

			lo.modify(dn, [('dNSTTL', '10800', '10900')])
			utils.wait_for_replication_and_postrun()
			check(zone)
		finally:
			lo.delete(dn)

		utils.wait_for_replication_and_postrun()
		check(zone, True)


def check(zone, removed=False, valid=False):
	assert valid == os.path.exists(os.path.join(NAMED_CONF_DIR, zone))
	assert valid == os.path.exists(os.path.join(NAMED_CONF_DIR, zone + '.proxy'))
	#assert valid == os.path.exists(os.path.join(PROXY_CACHE_DIR, "%s.zone" % (zone,)))

	# make sure bind9 is still running
	subprocess.check_call(['service', 'bind9', 'status'])

	if valid:
		resolveDnsEntry(zone, 'SOA', 5)
	else:
		with pytest.raises(NXDOMAIN):
			resolveDnsEntry(zone, 'SOA', 5)

	# TODO: add checks that zoen is not included in /etc/bind/univention.conf
