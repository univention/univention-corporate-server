#!/usr/share/ucs-test/runner /usr/bin/py.test -s
# coding: utf-8
## desc: "Test the UCS<->AD sync in {read,write,sync} mode for dns objects."
## exposure: dangerous
## packages:
## - univention-s4-connector
## bugs:
##  - 39060
## tags:
##  - s4c_dns

import ldap
import pytest

from univention.testing.udm import UCSTestUDM
import univention.testing.connector_common as tcommon
import univention.testing.strings as tstring

import s4connector
from s4connector import (connector_running_on_this_host, connector_setup)
import dnstests


def build_s4_host_dn(host, zone, domain):
	first = [
		[("DC", host, ldap.AVA_STRING)],
		[("DC", zone, ldap.AVA_STRING)],
		[("CN", "MicrosoftDNS", ldap.AVA_STRING)],
		[("DC", "DomainDnsZones", ldap.AVA_STRING)],
	]
	return ldap.dn.dn2str(first + ldap.dn.str2dn(domain))


@pytest.mark.parametrize("sync_mode", ["write", "sync"])
@pytest.mark.skipif(not connector_running_on_this_host(),
	reason="Univention S4 Connector not configured.")
def test_attribute_sync_from_udm_to_s4(sync_mode):
	with connector_setup(sync_mode) as s4, UCSTestUDM() as udm:
		base = dnstests.ucr.get('ldap/base')
		ip = dnstests.make_random_ip()
		random_zone = dnstests.random_zone()
		random_host_a = tstring.random_name()
		random_host_b = tstring.random_name()
		nameserver = dnstests.get_hostname_of_ldap_master()

		print 'Creating objects..\n'
		zone_dn = udm.create_object('dns/forward_zone', zone=random_zone, nameserver=nameserver)
		host_dn = udm.create_object('dns/host_record', name=random_host_a, a=ip, superordinate=zone_dn)
		s4connector.wait_for_sync()
		s4_host_dn = build_s4_host_dn(random_host_a, random_zone, base)
		s4.verify_object(s4_host_dn, {"name": random_host_a, "dc": random_host_a})
		tcommon.verify_udm_object("dns/host_record", host_dn, {"name": random_host_a, "a": ip})

		print 'Modifying host record..\n'
		new_host_dn = udm.modify_object('dns/host_record', dn=host_dn, name=random_host_b)
		# XXX after a modify, the old DN is _wrongly_ returned: see bug #41694
		if new_host_dn == host_dn:
			new_host_dn = ldap.dn.dn2str([[("relativeDomainName", random_host_b, ldap.AVA_STRING)]] +
				ldap.dn.str2dn(host_dn)[1:])
			if host_dn in udm._cleanup.get('dns/host_record', []):
				udm._cleanup.setdefault('dns/host_record', []).append(new_host_dn)
				udm._cleanup['dns/host_record'].remove(host_dn)
		# XXX end of workarround for bug #41694

		s4connector.wait_for_sync()
		s4_new_host_dn = build_s4_host_dn(random_host_b, random_zone, base)
		s4.verify_object(s4_host_dn, None)
		tcommon.verify_udm_object("dns/host_record", host_dn, None)
		s4.verify_object(s4_new_host_dn, {"name": random_host_b, "dc": random_host_b})
		tcommon.verify_udm_object("dns/host_record", new_host_dn, {"name": random_host_b, "a": ip})

		print 'Cleaning up..\n'
		udm.remove_object('dns/host_record', dn=new_host_dn)
		udm.remove_object('dns/forward_zone', dn=zone_dn)

		s4connector.wait_for_sync()
		s4.verify_object(s4_new_host_dn, None)
		tcommon.verify_udm_object("dns/host_record", new_host_dn, None)
