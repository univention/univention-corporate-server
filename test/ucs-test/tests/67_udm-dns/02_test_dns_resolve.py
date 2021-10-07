#!/usr/share/ucs-test/runner /usr/bin/pytest-3 -s
## desc: Check DNS resolving of all DNS record and zone types
## bugs: [39269]
## roles:
##  - domaincontroller_master
## packages:
##   - univention-config
##   - univention-directory-manager-tools
## tags:
##  - skip_admember
## exposure: careful

from ipaddress import ip_address
import pytest
import re
import subprocess
import time

import dns.resolver as resolver
from dns.exception import Timeout
from dns.resolver import NXDOMAIN
from dns.resolver import NoNameservers

import univention.testing.strings as uts
import univention.testing.utils as utils


def resolve_dns_entry(zoneName, resourceRecord, timeout=120, tries=3):
	start = time.time()

	while True:
		try:
			answers = resolver.query(zoneName, resourceRecord)
			return answers
		except Timeout:
			tries -= 1
			if tries < 0:
				raise
		except (NXDOMAIN, NoNameservers):
			diff = time.time() - start
			if diff > timeout:
				raise

		time.sleep(1)


class Test_DNSResolve(object):

	def test__dns_forward_zone_check_resolve(self, udm):
		"""Creates DNS forward zone entry and try to resolve it"""
		zone = '%s.%s.' % (uts.random_name(), uts.random_name())
		pos = 'cn=dns,%s' % (udm.LDAP_BASE,)

		forward_zone_properties = {
			'zone': zone,
			'nameserver': udm.FQHN,
			'contact': '%s@%s.%s' % (uts.random_name(), uts.random_name(), uts.random_name()),
			'serial': '%s' % (uts.random_int()),
			'zonettl': '%s' % (uts.random_int(bottom_end=100, top_end=999)),
			'refresh': '%s' % (uts.random_int(bottom_end=10, top_end=99)),
			'expire': '%s' % (uts.random_int(bottom_end=10, top_end=99)),
			'ttl': '%s' % (uts.random_int(bottom_end=10, top_end=99)),
			'retry': '%s' % (uts.random_int()),
			'a': ['%s' % (uts.random_ip())]
		}
		udm.create_object('dns/forward_zone', position=pos, **forward_zone_properties)
		time.sleep(5)
		answers = resolve_dns_entry(zone, 'SOA')
		answer = answers.qname.to_text()
		assert answer == zone, 'resolved name "%s" != created ldap-object "%s"' % (answer, zone)

	def test__dns_reverse_zone_check_resolve(self, udm):
		"""Creates DNS reverse zone entry and try to resolve it"""
		pos = 'cn=dns,%s' % (udm.LDAP_BASE,)

		# IPv4
		ipv4 = uts.random_ip().split('.')
		subnet = ipv4[:3]
		reverse_zone_properties = {
			'subnet': '.'.join(subnet),
			'nameserver': udm.FQHN,
			'contact': '%s@%s.%s' % (uts.random_name(), uts.random_name(), uts.random_name()),
			'serial': '%s' % (uts.random_int()),
			'zonettl': '%s' % (uts.random_int(bottom_end=100, top_end=999)),
			'refresh': '%s' % (uts.random_int(bottom_end=10, top_end=99)),
			'expire': '%s' % (uts.random_int(bottom_end=10, top_end=99)),
			'ttl': '%s' % (uts.random_int(bottom_end=10, top_end=99)),
			'retry': '%s' % (uts.random_int()),
		}
		udm.create_object('dns/reverse_zone', position=pos, **reverse_zone_properties)
		zoneName = '.'.join(
			list(reversed(subnet)) + ['in-addr', 'arpa', '']
		)
		time.sleep(5)
		answers = resolve_dns_entry(zoneName, 'SOA')
		answer = answers.qname.to_text()
		assert answer == zoneName, 'IPv4: resolved name "%s" != created ldap-object "%s"' % (answer, zoneName)

		# IPv6
		ipv6 = '2011:06f8:13dc:0002:19b7:d592:09dd:1041'.split(':')  # create uts.random_ipV6()?
		subnet = ipv6[:7]
		reverse_zone_properties.update({
			'subnet': ':'.join(subnet),
		})
		udm.create_object('dns/reverse_zone', position=pos, **reverse_zone_properties)
		zoneName = '.'.join(
			list(reversed([nibble for block in subnet for nibble in block])) + ['ip6', 'arpa', '']
		)
		time.sleep(5)
		answers = resolve_dns_entry(zoneName, 'SOA')
		answer = answers.qname.to_text()
		assert answer == zoneName, 'IPv6: resolved name "%s" != created ldap-object "%s"' % (answer, zoneName)

	def test__dns_host_record_check_resolve(self, udm):
		"""Creates DNS host record entry and try to resolve it"""
		zone = '%s.%s.' % (uts.random_name(), uts.random_name())
		pos = 'cn=dns,%s' % (udm.LDAP_BASE,)

		forward_zone_properties = {
			'zone': zone,
			'nameserver': udm.FQHN,
			'contact': '%s@%s.%s' % (uts.random_name(), uts.random_name(), uts.random_name()),
			'serial': '%s' % (uts.random_int()),
			'zonettl': '%s' % (uts.random_int(bottom_end=100, top_end=999)),
			'refresh': '%s' % (uts.random_int(bottom_end=10, top_end=99)),
			'expire': '%s' % (uts.random_int(bottom_end=10, top_end=99)),
			'ttl': '%s' % (uts.random_int(bottom_end=10, top_end=99)),
			'retry': '%s' % (uts.random_int()),
		}
		forward_zone = udm.create_object('dns/forward_zone', position=pos, **forward_zone_properties)

		# IPv4
		ip = uts.random_ip()
		host = uts.random_name()
		host_record_properties = {
			'name': host,
			'zonettl': '%s' % (uts.random_int(bottom_end=100, top_end=999)),
			'a': ip,
			'mx': '50 %s' % uts.random_string(),
			'txt': uts.random_string()
		}
		udm.create_object('dns/host_record', superordinate=forward_zone, **host_record_properties)

		qname = '%s.%s' % (host, zone)
		answers = resolve_dns_entry(qname, 'A')
		answer = [ip_address(u'%s' % (rdata.address,)) for rdata in answers]
		assert answer == [ip_address(u'%s' % (ip,))], 'resolved name "%s" != created ldap-object "%s"' % (answer, [ip])

		# IPv6
		ip = '2011:06f8:13dc:0002:19b7:d592:09dd:1041'  # create random_ipv6()-method?
		host = uts.random_name()
		host_record_properties.update({
			'name': host,
			'a': ip,
		})
		udm.create_object('dns/host_record', superordinate=forward_zone, **host_record_properties)

		qname = '%s.%s' % (host, zone)
		time.sleep(5)
		answers = resolve_dns_entry(qname, 'AAAA')
		answer = [ip_address(u'%s' % (rdata.address,)) for rdata in answers]
		assert answer == [ip_address(u'%s' % (ip,))], 'resolved name "%s" != created ldap-object "%s"' % (answer, [ip])

	def test__dns_alias_record_check_resolve(self, udm):
		"""Creates DNS alias record and tries to resolve it"""
		zone = '%s.%s.' % (uts.random_name(), uts.random_name())
		pos = 'cn=dns,%s' % (udm.LDAP_BASE,)

		forward_zone_properties = {
			'zone': zone,
			'nameserver': udm.FQHN,
			'contact': '%s@%s.%s' % (uts.random_name(), uts.random_name(), uts.random_name()),
			'serial': '%s' % (uts.random_int()),
			'zonettl': '%s' % (uts.random_int(bottom_end=100, top_end=999)),
			'refresh': '%s' % (uts.random_int(bottom_end=10, top_end=99)),
			'expire': '%s' % (uts.random_int(bottom_end=10, top_end=99)),
			'ttl': '%s' % (uts.random_int(bottom_end=10, top_end=99)),
			'retry': '%s' % (uts.random_int()),
		}
		forward_zone = udm.create_object('dns/forward_zone', position=pos, **forward_zone_properties)

		# IPv4 / IPv6
		host = uts.random_name()
		ipv4 = uts.random_ip()
		ipv6 = '2011:06f8:13dc:0002:19b7:d592:09dd:1041'  # create random_ipv6()-method?
		host_record_properties = {
			'name': host,
			'zonettl': '%s' % (uts.random_int(bottom_end=100, top_end=999)),
			'a': [ipv4, ipv6],
			'mx': '50 %s' % uts.random_string(),
			'txt': uts.random_string()
		}
		udm.create_object('dns/host_record', superordinate=forward_zone, **host_record_properties)

		alias_name = uts.random_name()
		fqhn = '%s.%s' % (host, zone)
		udm.create_object('dns/alias', superordinate=forward_zone, name=alias_name, cname=fqhn)

		qname = '%s.%s' % (alias_name, zone)
		time.sleep(5)
		answers = resolve_dns_entry(qname, 'CNAME')
		answer = [rdata.target.to_text() for rdata in answers]
		assert answer == [fqhn], 'resolved name "%s" != created ldap-object "%s"' % (answer, [fqhn])

	def test__dns_srv_record_check_resolve(self, udm):
		"""Creates DNS srv record and try to resolve it"""
		zone = '%s.%s.' % (uts.random_name(), uts.random_name())
		pos = 'cn=dns,%s' % (udm.LDAP_BASE,)

		forward_zone_properties = {
			'zone': zone,
			'nameserver': udm.FQHN,
			'contact': '%s@%s.%s' % (uts.random_name(), uts.random_name(), uts.random_name()),
			'serial': '%s' % (uts.random_int()),
			'zonettl': '%s' % (uts.random_int(bottom_end=100, top_end=999)),
			'refresh': '%s' % (uts.random_int(bottom_end=10, top_end=99)),
			'expire': '%s' % (uts.random_int(bottom_end=10, top_end=99)),
			'ttl': '%s' % (uts.random_int(bottom_end=10, top_end=99)),
			'retry': '%s' % (uts.random_int()),
		}
		forward_zone = udm.create_object('dns/forward_zone', position=pos, **forward_zone_properties)

		# IPv4 / IPv6
		host = uts.random_name()
		ipv4 = uts.random_ip()
		ipv6 = '2011:06f8:13dc:0002:19b7:d592:09dd:1041'  # create random_ipv6()-method?
		host_record_properties = {
			'name': host,
			'zonettl': '%s' % (uts.random_int(bottom_end=100, top_end=999)),
			'a': [ipv4, ipv6],
			'mx': '50 %s' % uts.random_string(),
			'txt': uts.random_string()
		}
		udm.create_object('dns/host_record', superordinate=forward_zone, **host_record_properties)

		service = uts.random_string()
		protocol = 'tcp'
		extension = uts.random_string()
		priority = 1
		weight = 100
		port = uts.random_int(top_end=65535)
		fqhn = '%s.%s' % (host, zone)
		srv_record_properties = {
			'name': '%s %s %s' % (service, protocol, extension),
			'location': '%d %d %s %s' % (priority, weight, port, fqhn),
			'zonettl': '128'
		}
		udm.create_object('dns/srv_record', superordinate=forward_zone, **srv_record_properties)

		zoneName = '_%s._%s.%s.%s' % (service, protocol, extension, zone)
		answers = resolve_dns_entry(zoneName, 'SRV')
		answer = [rdata.target.to_text() for rdata in answers]
		assert answer == [fqhn], 'resolved name "%s" != created ldap-object "%s"' % (answer, [fqhn])

	def test__dns_pointer_record_check_resolve(self, udm):
		"""Creates DNS pointer record entry and try to resolve it"""
		pos = 'cn=dns,%s' % (udm.LDAP_BASE,)

		ptr_record = '%s.%s.' % (uts.random_name(), uts.random_name())

		# IPv4
		ipv4 = uts.random_ip().split('.')
		subnet = ipv4[:3]
		reverse_zone_properties = {
			'subnet': '.'.join(subnet),
			'nameserver': udm.FQHN,
			'contact': '%s@%s.%s' % (uts.random_name(), uts.random_name(), uts.random_name()),
			'serial': '%s' % (uts.random_int()),
			'zonettl': '%s' % (uts.random_int(bottom_end=100, top_end=999)),
			'refresh': '%s' % (uts.random_int(bottom_end=10, top_end=99)),
			'expire': '%s' % (uts.random_int(bottom_end=10, top_end=99)),
			'ttl': '%s' % (uts.random_int(bottom_end=10, top_end=99)),
			'retry': '%s' % (uts.random_int()),
		}
		reverse_zone = udm.create_object('dns/reverse_zone', position=pos, **reverse_zone_properties)

		udm.create_object('dns/ptr_record', address=ipv4[3], superordinate=reverse_zone, ptr_record=ptr_record)

		zoneName = '.'.join(
			list(reversed(ipv4)) + ['in-addr', 'arpa', '']
		)
		time.sleep(5)
		answers = resolve_dns_entry(zoneName, 'PTR')
		answer = [rdata.to_text() for rdata in answers]
		assert answer == [ptr_record], 'resolved name "%s" != created ldap-object "%s"' % (answer, [ptr_record])

		# IPv6
		ipv6 = '2011:06f8:13dc:0002:19b7:d592:09dd:1041'.split(':')  # create uts.random_ipV6()?
		subnet = ipv6[:7]
		reverse_zone_properties.update({
			'subnet': ':'.join(subnet),
		})
		reverse_zone = udm.create_object('dns/reverse_zone', position=pos, **reverse_zone_properties)

		addr = '.'.join(reversed(ipv6[7]))
		udm.create_object('dns/ptr_record', address=addr, superordinate=reverse_zone, ptr_record=ptr_record)

		zoneName = '.'.join(
			list(reversed([nibble for block in ipv6 for nibble in block])) + ['ip6', 'arpa', '']
		)
		time.sleep(5)
		answers = resolve_dns_entry(zoneName, 'PTR')
		answer = [rdata.to_text() for rdata in answers]
		assert answer == [ptr_record], 'resolved name "%s" != created ldap-object "%s"' % (answer, [ptr_record])

	def test__dns_txt_record_check_resolve(self, udm):
		"""Creates DNS pointer record entry and try to resolve it"""
		zone = '%s.%s.' % (uts.random_name(), uts.random_name())
		pos = 'cn=dns,%s' % (udm.LDAP_BASE,)

		txt = uts.random_string()
		forward_zone_properties = {
			'zone': zone,
			'nameserver': udm.FQHN,
			'contact': '%s@%s.%s' % (uts.random_name(), uts.random_name(), uts.random_name()),
			'serial': '%s' % (uts.random_int()),
			'zonettl': '%s' % (uts.random_int(bottom_end=100, top_end=999)),
			'refresh': '%s' % (uts.random_int(bottom_end=10, top_end=99)),
			'expire': '%s' % (uts.random_int(bottom_end=10, top_end=99)),
			'ttl': '%s' % (uts.random_int(bottom_end=10, top_end=99)),
			'retry': '%s' % (uts.random_int()),
			'txt': txt,
		}
		udm.create_object('dns/forward_zone', position=pos, **forward_zone_properties)
		time.sleep(5)
		answers = resolve_dns_entry(zone, 'TXT')
		# FIXME PMH-2017-01-14: returned TXT data is enclosed in "
		answer = [rdata.to_text().strip('"') for rdata in answers]
		assert answer == [txt], 'resolved name "%s" != created ldap-object "%s"' % (answer, [txt])

	@pytest.mark.skipif(not utils.package_installed('univention-s4-connector'), reason="Univention S4 Connector is not installed.")
	def test__dns_ns_record_check_resolve(self, udm, ucr):
		"""Create DNS NS record and try to resolve it"""
		# bugs: [32626]
		# packages: univention-s4-connector
		partentzone = '%(domainname)s' % ucr
		partentzone = partentzone
		forward_zone = "zoneName=%(domainname)s,cn=dns,%(ldap/base)s" % ucr

		zonename = uts.random_name()
		nameserver1 = ".".join([uts.random_name(), partentzone])
		nameserver2 = ".".join([uts.random_name(), partentzone])
		nameservers = [nameserver1, nameserver2]

		record_properties = {
			'zone': zonename,
			'zonettl': '%s' % (uts.random_int(bottom_end=100, top_end=999)),
			'nameserver': nameservers
		}
		udm.create_object('dns/ns_record', superordinate=forward_zone, **record_properties)

		from univention.testing.ucs_samba import wait_for_s4connector
		wait_for_s4connector()

		zone_fqdn = '%s.%s' % (zonename, partentzone)
		p1 = subprocess.Popen(['dig', '+nocmd', '+noall', '+answer', '@localhost', zone_fqdn, 'ANY'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=True)
		stdout, stderr = p1.communicate()
		stdout = stdout.decode('UTF-8', 'replace')
		assert p1.returncode == 0, "DNS dig query failed"

		found = [x for x in nameservers if re.search("^%s\\.[ \t][0-9]+[ \t]IN\tNS\t%s\\." % (re.escape(zone_fqdn), re.escape(x)), stdout, re.MULTILINE)]

		assert nameservers == found, "Record not found: %s" % ([set(nameservers) - set(found)],)
