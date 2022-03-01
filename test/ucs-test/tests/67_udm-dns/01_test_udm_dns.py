#!/usr/share/ucs-test/runner pytest-3 -s
## desc: Check UDM integratoin of all DNS record and zone types
## tags: [udm]
## roles: [domaincontroller_master]
## exposure: careful
## packages:
##   - univention-config
##   - univention-directory-manager-tools
## versions:
##  3.1-1: skip
##  3.2-0: fixed

import pytest

import univention.testing.strings as uts
import univention.testing.udm as udm_test
import univention.testing.utils as utils


class Test_DNSForwardZone(object):

	def test_dns_forward_zone_check_soa_record(self, udm):
		"""Check dns/forward_zone SOA record"""
		forward_zone_properties = {
			'zone': '%s.%s' % (uts.random_name(), uts.random_dns_record()),
			'nameserver': "%s.%s" % (uts.random_name(), uts.random_dns_record()),
			'contact': '%s@%s.%s' % (uts.random_name(), uts.random_name(), uts.random_name()),
			'serial': '1',
			'zonettl': '128',
			'refresh': '64',
			'expire': '32',
			'ttl': '16',
			'retry': '8'
		}

		forward_zone = udm.create_object('dns/forward_zone', **forward_zone_properties)
		# Note: UDM automatically appends a dot
		utils.verify_ldap_object(forward_zone, {'sOARecord': ['%s %s. %s %s %s %s %s' % (
			forward_zone_properties['nameserver'],
			forward_zone_properties['contact'].replace('@', '.'),
			forward_zone_properties['serial'],
			forward_zone_properties['refresh'],
			forward_zone_properties['retry'],
			forward_zone_properties['expire'],
			forward_zone_properties['ttl'])]
		})

	def test_dns_forward_zone_removal(self, udm):
		"""Remove dns/forward_zone"""
		forward_zone = udm.create_object('dns/forward_zone', zone='%s.%s' % (uts.random_name(), uts.random_dns_record()), nameserver=uts.random_dns_record())

		udm.remove_object('dns/forward_zone', dn=forward_zone)
		utils.verify_ldap_object(forward_zone, should_exist=False)

	def test_dns_forward_zone_check_soa_serial_incrementation(self, udm):
		"""Check dns/forward_zone SOA record serial number incrementation"""
		forward_zone_properties = {
			'zone': '%s.%s' % (uts.random_name(), uts.random_dns_record()),
			'nameserver': uts.random_dns_record(),
			'contact': '%s@%s.%s' % (uts.random_name(), uts.random_name(), uts.random_name()),
			'serial': '1',
			'zonettl': '128',
			'refresh': '64',
			'expire': '32',
			'ttl': '16',
			'retry': '8'
		}

		forward_zone = udm.create_object('dns/forward_zone', wait_for=True, **forward_zone_properties)
		new_ttl = '12'
		udm.modify_object('dns/forward_zone', dn=forward_zone, ttl=new_ttl, wait_for=True)

		utils.verify_ldap_object(forward_zone, {'sOARecord': ['%s %s. %s %s %s %s %s' % (
			forward_zone_properties['nameserver'],
			forward_zone_properties['contact'].replace('@', '.'),
			'2',
			forward_zone_properties['refresh'],
			forward_zone_properties['retry'],
			forward_zone_properties['expire'],
			new_ttl)]
		})

	def test_dns_forward_zone_creation_set_nameserver(self, udm):
		"""Set nameserver during dns/forward_zone creation"""
		# bugs: [15654]
		ns_record = uts.random_dns_record()

		forward_zone = udm.create_object('dns/forward_zone', zone='%s.%s' % (uts.random_name(), uts.random_dns_record()), nameserver=ns_record)
		utils.verify_ldap_object(forward_zone, {'nSRecord': ['%s' % ns_record]})

	def test_dns_forward_zone_modification_set_nameserver(self, udm):
		"""Set nameserver during dns/forward_zone modification"""
		# bugs: [15654]
		forward_zone = udm.create_object('dns/forward_zone', zone='%s.%s' % (uts.random_name(), uts.random_dns_record()), nameserver=uts.random_dns_record(), wait_for=True)

		ns_record = uts.random_dns_record()
		udm.modify_object('dns/forward_zone', dn=forward_zone, nameserver=ns_record, wait_for=True)
		utils.verify_ldap_object(forward_zone, {'nSRecord': ['%s' % ns_record]})

	def test_dns_forward_zone_creation_append_nameservers(self, udm):
		"""Append nameservers during dns/forward_zone creation"""
		# bugs: [15654]
		ns_records = [uts.random_dns_record(), uts.random_dns_record()]

		forward_zone = udm.create_object('dns/forward_zone', zone='%s.%s' % (uts.random_name(), uts.random_dns_record()), append={'nameserver': ns_records})
		utils.verify_ldap_object(forward_zone, {'nSRecord': ['%s' % ns_record for ns_record in ns_records]})

	def test_dns_forward_zone_modification_append_nameservers(self, udm):
		"""Append nameservers during dns/forward_zone modification"""
		# bugs: [15654]
		ns_records = [uts.random_dns_record(), uts.random_dns_record(), uts.random_dns_record()]

		forward_zone = udm.create_object('dns/forward_zone', zone='%s.%s' % (uts.random_name(), uts.random_dns_record()), nameserver=ns_records[0], wait_for=True)

		udm.modify_object('dns/forward_zone', dn=forward_zone, append={'nameserver': ns_records[1:]}, wait_for=True)
		utils.verify_ldap_object(forward_zone, {'nSRecord': ['%s' % ns_record for ns_record in ns_records]})

	def test_dns_forward_zone_creation_set_mx(self, udm):
		"""Set MX during dns/forward_zone creation"""
		# bugs: [15654]
		mx_record = '40 %s' % uts.random_dns_record()

		forward_zone = udm.create_object('dns/forward_zone', zone='%s.%s' % (uts.random_name(), uts.random_dns_record()), mx=mx_record, nameserver=uts.random_dns_record())
		utils.verify_ldap_object(forward_zone, {'mXRecord': [mx_record]})

	def test_dns_forward_zone_modification_set_mx(self, udm):
		"""Set MX during dns/forward_zone modification"""
		# bugs: [15654]
		forward_zone = udm.create_object('dns/forward_zone', zone='%s.%s' % (uts.random_name(), uts.random_dns_record()), nameserver=uts.random_dns_record(), wait_for=True)

		mx_record = '40 %s' % (uts.random_dns_record(),)
		udm.modify_object('dns/forward_zone', dn=forward_zone, mx=mx_record, wait_for=True)
		utils.verify_ldap_object(forward_zone, {'mXRecord': [mx_record]})

	def test_dns_forward_zone_creation_append_mx(self, udm):
		"""Append MX during dns/forward_zone creation"""
		# bugs: [15654]
		mx_records = ['40 %s' % uts.random_dns_record(), '50 %s' % uts.random_dns_record()]

		forward_zone = udm.create_object('dns/forward_zone', zone='%s.%s' % (uts.random_name(), uts.random_dns_record()), append={'mx': mx_records}, nameserver=uts.random_dns_record())
		utils.verify_ldap_object(forward_zone, {'mXRecord': mx_records})

	def test_dns_forward_zone_modification_append_mx(self, udm):
		"""Append MX during dns/forward_zone modification"""
		# bugs: [15654]
		forward_zone = udm.create_object('dns/forward_zone', zone='%s.%s' % (uts.random_name(), uts.random_dns_record()), nameserver=uts.random_dns_record(), wait_for=True)

		mx_records = ['40 %s' % uts.random_dns_record(), '50 %s' % uts.random_dns_record()]
		udm.modify_object('dns/forward_zone', dn=forward_zone, append={'mx': mx_records}, wait_for=True)
		utils.verify_ldap_object(forward_zone, {'mXRecord': mx_records})

	def test_dns_forward_zone_creation_set_txt(self, udm):
		"""Set TXT during dns/forward_zone creation"""
		txt_record = uts.random_string()

		forward_zone = udm.create_object('dns/forward_zone', zone='%s.%s' % (uts.random_name(), uts.random_dns_record()), txt=txt_record, nameserver=uts.random_dns_record())
		utils.verify_ldap_object(forward_zone, {'tXTRecord': [txt_record]})

	def test_dns_forward_zone_modification_set_txt(self, udm):
		"""Set TXT during dns/forward_zone modification"""
		forward_zone = udm.create_object('dns/forward_zone', zone='%s.%s' % (uts.random_name(), uts.random_dns_record()), nameserver=uts.random_dns_record(), wait_for=True)

		txt_record = uts.random_string()
		udm.modify_object('dns/forward_zone', dn=forward_zone, txt=txt_record, wait_for=True)
		utils.verify_ldap_object(forward_zone, {'tXTRecord': [txt_record]})

	def test_dns_forward_zone_creation_append_txt(self, udm):
		"""Append TXT during dns/forward_zone creation"""
		txt_records = [uts.random_string(), uts.random_string()]

		forward_zone = udm.create_object('dns/forward_zone', zone='%s.%s' % (uts.random_name(), uts.random_dns_record()), append={'txt': txt_records}, nameserver=uts.random_dns_record())
		utils.verify_ldap_object(forward_zone, {'tXTRecord': txt_records})

	def test_dns_forward_zone_modification_append_txt(self, udm):
		"""Append TXT during dns/forward_zone modification"""
		forward_zone = udm.create_object('dns/forward_zone', zone='%s.%s' % (uts.random_name(), uts.random_dns_record()), nameserver=uts.random_dns_record(), wait_for=True)

		txt_records = [uts.random_dns_record(), uts.random_dns_record()]
		udm.modify_object('dns/forward_zone', dn=forward_zone, append={'txt': txt_records}, wait_for=True)
		utils.verify_ldap_object(forward_zone, {'tXTRecord': txt_records})

	def test_dns_forward_zone_modification_remove_txt(self, udm):
		"""Remove TXT during dns/forward_zone modification"""
		# bugs: [15654]
		txt_records = [uts.random_string(), uts.random_string(), uts.random_string(), uts.random_string()]
		forward_zone = udm.create_object('dns/forward_zone', zone='%s.%s' % (uts.random_name(), uts.random_name()), append={'txt': txt_records}, nameserver=uts.random_dns_record(), wait_for=True)

		udm.modify_object('dns/forward_zone', dn=forward_zone, remove={'txt': txt_records[2:]}, wait_for=True)
		utils.verify_ldap_object(forward_zone, {'tXTRecord': txt_records[:2]})

	def test_dns_forward_zone_modification_remove_nameserver(self, udm):
		"""Remove nameserver during dns/forward_zone modification"""
		ns_records = [uts.random_dns_record(), uts.random_dns_record(), uts.random_dns_record(), uts.random_dns_record()]
		forward_zone = udm.create_object('dns/forward_zone', zone='%s.%s' % (uts.random_name(), uts.random_name()), append={'nameserver': ns_records}, wait_for=True)

		udm.modify_object('dns/forward_zone', dn=forward_zone, remove={'nameserver': ns_records[2:]}, wait_for=True)
		utils.verify_ldap_object(forward_zone, {'nSRecord': ['%s' % ns_record for ns_record in ns_records[:2]]})

	def test_dns_forward_zone_modification_remove_mx(self, udm):
		"""Remove MX during dns/forward_zone modification"""
		mx_records = ['40 %s' % uts.random_dns_record(), '50 %s' % uts.random_dns_record(), '60 %s' % uts.random_dns_record(), '70 %s' % uts.random_dns_record()]
		forward_zone = udm.create_object('dns/forward_zone', zone='%s.%s' % (uts.random_name(), uts.random_name()), nameserver=uts.random_dns_record(), append={'mx': mx_records}, wait_for=True)

		udm.modify_object('dns/forward_zone', dn=forward_zone, remove={'mx': mx_records[:2]}, wait_for=True)
		utils.verify_ldap_object(forward_zone, {'mXRecord': mx_records[2:]})


class Test_DNSServiceRecord(object):

	def test_dns_srv_record_creation_with_all_attributes(self, udm):
		"""Create dns/srv_record with all attributes set"""
		forward_zone = udm.create_object('dns/forward_zone', zone='%s.%s' % (uts.random_name(), uts.random_name()), nameserver=uts.random_dns_record())

		srv_record_proprties = {
			'name': '%s tcp %s' % (uts.random_string(), uts.random_string()),
			'location': '0 1 2 %s.%s' % (uts.random_name(), uts.random_dns_record()),
			'zonettl': '128'
		}

		srv_record = udm.create_object('dns/srv_record', superordinate=forward_zone, **srv_record_proprties)

		utils.verify_ldap_object(srv_record, {
			'sRVRecord': [srv_record_proprties['location']],
			'dNSTTL': [srv_record_proprties['zonettl']],
		})

	def test_dns_srv_record_creation_set_location(self, udm):
		"""Set location during dns/srv_record creation"""
		forward_zone = udm.create_object('dns/forward_zone', zone='%s.%s' % (uts.random_name(), uts.random_name()), nameserver=uts.random_dns_record())

		location = '0 1 2 %s.%s' % (uts.random_name(), uts.random_dns_record())
		srv_record = udm.create_object('dns/srv_record', superordinate=forward_zone, name='%s tcp %s' % (uts.random_string(), uts.random_string()), location=location)
		utils.verify_ldap_object(srv_record, {'sRVRecord': [location]})

	def test_dns_srv_record_modification_set_location(self, udm):
		"""Set location during dns/srv_record modification"""
		forward_zone = udm.create_object('dns/forward_zone', zone='%s.%s' % (uts.random_name(), uts.random_name()), nameserver=uts.random_dns_record())

		srv_record = udm.create_object('dns/srv_record', superordinate=forward_zone, name='%s tcp %s' % (uts.random_string(), uts.random_string()), location='3 4 5 %s.%s' % (uts.random_string(), uts.random_string()), wait_for=True)

		location = '0 1 2 %s.%s' % (uts.random_name(), uts.random_dns_record())
		udm.modify_object('dns/srv_record', dn=srv_record, superordinate=forward_zone, location=location, wait_for=True)
		utils.verify_ldap_object(srv_record, {'sRVRecord': [location]})

	def test_dns_srv_record_creation_append_locations(self, udm):
		"""Append locations during dns/srv_record creation"""
		forward_zone = udm.create_object('dns/forward_zone', zone='%s.%s' % (uts.random_name(), uts.random_name()), nameserver=uts.random_dns_record())

		locations = ['0 1 2 %s.%s' % (uts.random_name(), uts.random_dns_record()), '5 3 9 %s.%s' % (uts.random_name(), uts.random_dns_record())]
		srv_record = udm.create_object('dns/srv_record', superordinate=forward_zone, name='%s tcp %s' % (uts.random_string(), uts.random_string()), append={'location': locations})
		utils.verify_ldap_object(srv_record, {'sRVRecord': locations})

	def test_dns_srv_record_modification_append_locations(self, udm):
		"""Append locations during dns/srv_record modification"""
		forward_zone = udm.create_object('dns/forward_zone', zone='%s.%s' % (uts.random_name(), uts.random_name()), nameserver=uts.random_dns_record())

		locations = ['0 1 2 %s.%s' % (uts.random_name(), uts.random_dns_record()), '9 3 5 %s.%s' % (uts.random_name(), uts.random_dns_record()), '6 2 4 %s.%s' % (uts.random_name(), uts.random_dns_record())]
		srv_record = udm.create_object('dns/srv_record', superordinate=forward_zone, name='%s tcp %s' % (uts.random_string(), uts.random_string()), location=locations[0], wait_for=True)

		udm.modify_object('dns/srv_record', dn=srv_record, superordinate=forward_zone, append={'location': locations[1:]}, wait_for=True)
		utils.verify_ldap_object(srv_record, {'sRVRecord': locations})

	def test_dns_srv_record_removal(self, udm):
		"""Remove dns/srv_record"""
		forward_zone = udm.create_object('dns/forward_zone', zone='%s.%s' % (uts.random_name(), uts.random_name()), nameserver=uts.random_dns_record())

		srv_record = udm.create_object('dns/srv_record', superordinate=forward_zone, name='%s tcp %s' % (uts.random_string(), uts.random_string()), location='0 1 2 %s.%s' % (uts.random_name(), uts.random_dns_record()))

		udm.remove_object('dns/srv_record', dn=srv_record, superordinate=forward_zone)
		utils.verify_ldap_object(srv_record, should_exist=False)

	def test_dns_srv_record_modification_remove_locations(self, udm):
		"""Remove locations during dns/srv_record modification"""
		forward_zone = udm.create_object('dns/forward_zone', zone='%s.%s' % (uts.random_name(), uts.random_name()), nameserver=uts.random_dns_record())

		locations = [
			'0 1 2 %s.%s' % (uts.random_name(), uts.random_dns_record()),
			'3 5 6 %s.%s' % (uts.random_name(), uts.random_dns_record()),
			'1 4 9 %s.%s' % (uts.random_name(), uts.random_dns_record()),
			'4 8 2 %s.%s' % (uts.random_name(), uts.random_dns_record())
		]
		srv_record = udm.create_object('dns/srv_record', superordinate=forward_zone, name='%s tcp %s' % (uts.random_string(), uts.random_string()), append={'location': locations}, wait_for=True)

		udm.modify_object('dns/srv_record', dn=srv_record, superordinate=forward_zone, remove={'location': locations[:2]}, wait_for=True)
		utils.verify_ldap_object(srv_record, {'sRVRecord': locations[2:]})


class Test_DNSHostRecord(object):

	def test_dns_host_record_creation(self, udm):
		"""Create dns/host"""
		forward_zone = udm.create_object('dns/forward_zone', zone='%s.%s' % (uts.random_name(), uts.random_dns_record()), nameserver=uts.random_dns_record())

		host_record = udm.create_object('dns/host_record', superordinate=forward_zone, name=uts.random_name())
		utils.verify_ldap_object(host_record)

	@pytest.mark.parametrize('record_attr,ip', [
		('aRecord', '10.20.30.40'),
		('aAAARecord', '2011:06f8:13dc:0002:19b7:d592:09dd:1041'),
	])
	def test_dns_host_record_creation_with_all_attributes(self, udm, record_attr, ip):
		"""Create dns/host with all attributes set"""
		forward_zone = udm.create_object('dns/forward_zone', zone='%s.%s' % (uts.random_name(), uts.random_name()), nameserver=uts.random_dns_record())

		host_record_properties = {
			'name': uts.random_name(),
			'zonettl': '128',
			'a': ip,
			'mx': '50 %s' % uts.random_string(),
			'txt': uts.random_string()
		}
		host_record = udm.create_object('dns/host_record', superordinate=forward_zone, **host_record_properties)
		utils.verify_ldap_object(host_record, {
			'dNSTTL': [host_record_properties['zonettl']],
			record_attr: [host_record_properties['a']],
			'tXTRecord': [host_record_properties['txt']],
			'mXRecord': [host_record_properties['mx']]
		})

	def test_dns_host_record_removal(self, udm):
		"""Remove dns/host"""
		forward_zone = udm.create_object('dns/forward_zone', zone='%s.%s' % (uts.random_name(), uts.random_name()), nameserver=uts.random_dns_record())

		host_record = udm.create_object('dns/host_record', superordinate=forward_zone, name=uts.random_name())

		udm.remove_object('dns/host_record', dn=host_record, superordinate=forward_zone)
		utils.verify_ldap_object(host_record, should_exist=False)

	@pytest.mark.parametrize('record_attr,ip', [
		('aRecord', '10.20.30.40'),
		('aAAARecord', '2011:06f8:13dc:0002:19b7:d592:09dd:1041'),
	])
	def test_dns_host_record_creation_set_a_aaaa(self, udm, record_attr, ip):
		"""Set A and AAAA during dns/host creation"""
		forward_zone = udm.create_object('dns/forward_zone', zone='%s.%s' % (uts.random_name(), uts.random_name()), nameserver=uts.random_dns_record())

		host_record = udm.create_object('dns/host_record', superordinate=forward_zone, name=uts.random_name(), a=ip)
		utils.verify_ldap_object(host_record, {record_attr: [ip]})

	@pytest.mark.parametrize('record_attr,ip', [
		('aRecord', '10.20.30.40'),
		('aAAARecord', '2011:06f8:13dc:0002:19b7:d592:09dd:1041'),
	])
	def test_dns_host_record_modification_set_a_aaaa(self, udm, record_attr, ip):
		"""Set A and AAAA during dns/host modification"""
		forward_zone = udm.create_object('dns/forward_zone', zone='%s.%s' % (uts.random_name(), uts.random_name()), nameserver=uts.random_dns_record())

		host_record = udm.create_object('dns/host_record', superordinate=forward_zone, name=uts.random_name(), wait_for=True)

		udm.modify_object('dns/host_record', dn=host_record, superordinate=forward_zone, a=ip, wait_for=True)
		utils.verify_ldap_object(host_record, {record_attr: [ip]})

	@pytest.mark.parametrize('record_attr,ips', [
		('aRecord', ['10.20.30.40', '10.20.30.41']),
		('aAAARecord', ['2011:06f8:13dc:0002:19b7:d592:09dd:1041', '2011:06f8:13dc:0002:19b7:d592:09dd:1042']),
	])
	def test_dns_host_record_creation_append_a_aaaa(self, udm, record_attr, ips):
		"""Append A and AAAA during dns/host creation"""
		forward_zone = udm.create_object('dns/forward_zone', zone='%s.%s' % (uts.random_name(), uts.random_name()), nameserver=uts.random_dns_record())

		host_record = udm.create_object('dns/host_record', superordinate=forward_zone, name=uts.random_name(), append={'a': ips})
		utils.verify_ldap_object(host_record, {record_attr: ips})

	@pytest.mark.parametrize('record_attr,ips', [
		('aRecord', ['10.20.30.40', '10.20.30.41']),
		('aAAARecord', ['2011:06f8:13dc:0002:19b7:d592:09dd:1041', '2011:06f8:13dc:0002:19b7:d592:09dd:1042']),
	])
	def test_dns_host_record_modification_append_a_aaaa(self, udm, record_attr, ips):
		"""Append A and AAAA during dns/host modification"""
		forward_zone = udm.create_object('dns/forward_zone', zone='%s.%s' % (uts.random_name(), uts.random_name()), nameserver=uts.random_dns_record())

		host_record = udm.create_object('dns/host_record', superordinate=forward_zone, name=uts.random_name(), wait_for=True)

		udm.modify_object('dns/host_record', dn=host_record, superordinate=forward_zone, append={'a': ips}, wait_for=True)
		utils.verify_ldap_object(host_record, {record_attr: ips})

	def test_dns_host_record_creation_set_mx(self, udm):
		"""Set MX during dns/host creation"""
		forward_zone = udm.create_object('dns/forward_zone', zone='%s.%s' % (uts.random_name(), uts.random_dns_record()), nameserver=uts.random_dns_record())

		mx_record = '40 %s' % uts.random_dns_record()
		host_record = udm.create_object('dns/host_record', superordinate=forward_zone, name=uts.random_name(), mx=mx_record)
		utils.verify_ldap_object(host_record, {'mXRecord': [mx_record]})

	def test_dns_host_record_modification_set_mx(self, udm):
		"""Set MX during dns/host modification"""
		forward_zone = udm.create_object('dns/forward_zone', zone='%s.%s' % (uts.random_name(), uts.random_name()), nameserver=uts.random_dns_record())

		host_record = udm.create_object('dns/host_record', superordinate=forward_zone, name=uts.random_name(), wait_for=True)

		mx_record = '40 %s' % uts.random_dns_record()
		udm.modify_object('dns/host_record', dn=host_record, superordinate=forward_zone, mx=mx_record, wait_for=True)
		utils.verify_ldap_object(host_record, {'mXRecord': [mx_record]})

	def test_dns_host_record_creation_append_mx(self, udm):
		"""Append MX during dns/host creation"""
		forward_zone = udm.create_object('dns/forward_zone', zone='%s.%s' % (uts.random_name(), uts.random_name()), nameserver=uts.random_dns_record())

		mx_records = ['40 %s' % uts.random_dns_record(), '50 %s' % uts.random_dns_record()]
		host_record = udm.create_object('dns/host_record', superordinate=forward_zone, name=uts.random_name(), append={'mx': mx_records})
		utils.verify_ldap_object(host_record, {'mXRecord': mx_records})

	def test_dns_host_record_modification_append_mx(self, udm):
		"""Append MX during dns/host modification"""
		forward_zone = udm.create_object('dns/forward_zone', zone='%s.%s' % (uts.random_name(), uts.random_name()), nameserver=uts.random_dns_record())

		host_record = udm.create_object('dns/host_record', superordinate=forward_zone, name=uts.random_name(), wait_for=True)

		mx_records = ['40 %s' % uts.random_dns_record(), '50 %s' % uts.random_dns_record()]
		udm.modify_object('dns/host_record', dn=host_record, superordinate=forward_zone, append={'mx': mx_records}, wait_for=True)
		utils.verify_ldap_object(host_record, {'mXRecord': mx_records})

	def test_dns_host_record_creation_set_txt(self, udm):
		"""Set TXT during dns/host creation"""
		forward_zone = udm.create_object('dns/forward_zone', zone='%s.%s' % (uts.random_name(), uts.random_name()), nameserver=uts.random_dns_record())

		txt_record = uts.random_string()
		host_record = udm.create_object('dns/host_record', superordinate=forward_zone, name=uts.random_name(), txt=txt_record)
		utils.verify_ldap_object(host_record, {'tXTRecord': [txt_record]})

	def test_dns_host_record_modification_set_txt(self, udm):
		"""Set TXT during dns/host modification"""
		forward_zone = udm.create_object('dns/forward_zone', zone='%s.%s' % (uts.random_name(), uts.random_name()), nameserver=uts.random_dns_record())

		host_record = udm.create_object('dns/host_record', superordinate=forward_zone, name=uts.random_name(), wait_for=True)

		txt_record = uts.random_string()
		udm.modify_object('dns/host_record', dn=host_record, superordinate=forward_zone, txt=txt_record, wait_for=True)
		utils.verify_ldap_object(host_record, {'tXTRecord': [txt_record]})

	def test_dns_host_record_creation_append_txt(self, udm):
		"""Append TXT during dns/host creation"""
		forward_zone = udm.create_object('dns/forward_zone', zone='%s.%s' % (uts.random_name(), uts.random_name()), nameserver=uts.random_dns_record())

		txt_records = ['%s' % uts.random_string(), '%s' % uts.random_string()]
		host_record = udm.create_object('dns/host_record', superordinate=forward_zone, name=uts.random_name(), append={'txt': txt_records})
		utils.verify_ldap_object(host_record, {'tXTRecord': txt_records})

	def test_dns_host_record_modification_append_txt(self, udm):
		"""Append TXT during dns/host modification"""
		forward_zone = udm.create_object('dns/forward_zone', zone='%s.%s' % (uts.random_name(), uts.random_name()), nameserver=uts.random_dns_record())

		host_record = udm.create_object('dns/host_record', superordinate=forward_zone, name=uts.random_name(), wait_for=True)

		txt_records = ['%s' % uts.random_string(), '%s' % uts.random_string()]
		udm.modify_object('dns/host_record', dn=host_record, superordinate=forward_zone, append={'txt': txt_records}, wait_for=True)
		utils.verify_ldap_object(host_record, {'tXTRecord': txt_records})

	@pytest.mark.parametrize('record_attr,ips', [
		('aRecord', ['10.20.30.40', '10.20.30.41', '10.20.30.42', '10.20.30.43']),
		('aAAARecord', ['2011:06f8:13dc:0002:19b7:d592:09dd:1041', '2011:06f8:13dc:0002:19b7:d592:09dd:1042', '2011:06f8:13dc:0002:19b7:d592:09dd:1043', '2011:06f8:13dc:0002:19b7:d592:09dd:1044']),
	])
	def test_dns_host_record_modification_remove_a_aaaa(self, udm, record_attr, ips):
		"""Remove A and AAAA during dns/host record modification"""
		forward_zone = udm.create_object('dns/forward_zone', zone='%s.%s' % (uts.random_name(), uts.random_name()), nameserver=uts.random_dns_record())

		host_record = udm.create_object('dns/host_record', superordinate=forward_zone, name=uts.random_name(), append={'a': ips}, wait_for=True)

		udm.modify_object('dns/host_record', dn=host_record, superordinate=forward_zone, remove={'a': ips[:2]}, wait_for=True)
		utils.verify_ldap_object(host_record, {record_attr: ips[2:]})

	def test_dns_host_record_modification_remove_mx(self, udm):
		"""Remove MX during dns/host record modification"""
		forward_zone = udm.create_object('dns/forward_zone', zone='%s.%s' % (uts.random_name(), uts.random_name()), nameserver=uts.random_dns_record())

		mx_records = ['40 %s' % uts.random_name(), '50 %s' % uts.random_name(), '60 %s' % uts.random_name(), '70 %s' % uts.random_name()]
		host_record = udm.create_object('dns/host_record', superordinate=forward_zone, name=uts.random_name(), append={'mx': mx_records}, wait_for=True)

		udm.modify_object('dns/host_record', dn=host_record, superordinate=forward_zone, remove={'mx': mx_records[:2]}, wait_for=True)
		utils.verify_ldap_object(host_record, {'mXRecord': mx_records[2:]})

	def test_dns_host_record_modification_remove_txt(self, udm):
		"""Remove TXT during dns/host record modification"""
		forward_zone = udm.create_object('dns/forward_zone', zone='%s.%s' % (uts.random_name(), uts.random_name()), nameserver=uts.random_dns_record())

		txt_records = [uts.random_string(), uts.random_string(), uts.random_string(), uts.random_string()]
		host_record = udm.create_object('dns/host_record', superordinate=forward_zone, name=uts.random_name(), append={'txt': txt_records}, wait_for=True)

		udm.modify_object('dns/host_record', dn=host_record, superordinate=forward_zone, remove={'txt': txt_records[:2]}, wait_for=True)
		utils.verify_ldap_object(host_record, {'tXTRecord': txt_records[2:]})


class Test_DNSAliasRecord(object):

	def test_dns_alias_creation(self, udm):
		"""Create dns/alias"""
		forward_zone = udm.create_object('dns/forward_zone', zone='%s.%s' % (uts.random_name(), uts.random_name()), nameserver=uts.random_dns_record())

		cname = uts.random_name()
		dns_alias = udm.create_object('dns/alias', superordinate=forward_zone, name=uts.random_name(), cname=cname)
		utils.verify_ldap_object(dns_alias, {'cNAMERecord': [cname]})

	def test_dns_alias_removal(self, udm):
		"""Remove dns/alias"""
		forward_zone = udm.create_object('dns/forward_zone', zone='%s.%s' % (uts.random_name(), uts.random_name()), nameserver=uts.random_dns_record())

		dns_alias = udm.create_object('dns/alias', superordinate=forward_zone, name=uts.random_name(), cname=uts.random_name())

		udm.remove_object('dns/alias', dn=dns_alias, superordinate=forward_zone)
		utils.verify_ldap_object(dns_alias, should_exist=False)

	def test_dns_alias_creation_set_zonettl(self, udm):
		"""Set zonettl during dns/alias creation"""
		forward_zone = udm.create_object('dns/forward_zone', zone='%s.%s' % (uts.random_name(), uts.random_name()), nameserver=uts.random_dns_record())

		zonettl = '128'
		dns_alias = udm.create_object('dns/alias', superordinate=forward_zone, name=uts.random_name(), cname=uts.random_name(), zonettl=zonettl)
		utils.verify_ldap_object(dns_alias, {'dNSTTL': [zonettl]})

	def test_dns_alias_modification_set_zonettl(self, udm):
		"""Set zonettl during dns/alias modification"""
		forward_zone = udm.create_object('dns/forward_zone', zone='%s.%s' % (uts.random_name(), uts.random_name()), nameserver=uts.random_dns_record())

		dns_alias = udm.create_object('dns/alias', superordinate=forward_zone, name=uts.random_name(), cname=uts.random_name(), wait_for=True)

		zonettl = '128'
		udm.modify_object('dns/alias', dn=dns_alias, superordinate=forward_zone, zonettl=zonettl, wait_for=True)
		utils.verify_ldap_object(dns_alias, {'dNSTTL': [zonettl]})


class Test_DNSReverseZone(object):

	@pytest.mark.parametrize('ip', [
		uts.random_subnet(),
		uts.random_ipv6_subnet(),
	])
	def test_dns_reverse_zone_check_soa_record(self, udm, ip):
		"""Check dns/reverse_zone SOA record"""
		reverse_zone_properties = {
			'subnet': ip,
			'nameserver': uts.random_dns_record(),
			'contact': '%s@%s.%s' % (uts.random_name(), uts.random_name(), uts.random_name()),
			'serial': '1',
			'zonettl': '128',
			'refresh': '64',
			'expire': '32',
			'ttl': '16',
			'retry': '8'
		}

		reverse_zone = udm.create_object('dns/reverse_zone', **reverse_zone_properties)
		utils.verify_ldap_object(reverse_zone, {'sOARecord': ['%s %s. %s %s %s %s %s' % (
			reverse_zone_properties['nameserver'],
			reverse_zone_properties['contact'].replace('@', '.'),
			reverse_zone_properties['serial'],
			reverse_zone_properties['refresh'],
			reverse_zone_properties['retry'],
			reverse_zone_properties['expire'],
			reverse_zone_properties['ttl']
		)]})

	@pytest.mark.parametrize('ip', [
		uts.random_subnet(),
		uts.random_ipv6_subnet(),
	])
	def test_dns_reverse_zone_check_soa_record_serial_incrementation(self, udm, ip):
		"""Check dns/reverse_zone SOA record serial number incrementation"""
		import ldap.dn
		import ldap.filter
		reverse_zone_properties = {
			'subnet': ip,
			'nameserver': uts.random_dns_record(),
			'contact': '%s@%s.%s' % (uts.random_name(), uts.random_name(), uts.random_name()),
			'serial': '1',
			'zonettl': '128',
			'refresh': '64',
			'expire': '32',
			'ttl': '16',
			'retry': '8'
		}
		reverse_zone = udm.create_object('dns/reverse_zone', wait_for=True, **reverse_zone_properties)

		reverse_zone_properties['ttl'] = '12'
		udm.modify_object('dns/reverse_zone', dn=reverse_zone, ttl=reverse_zone_properties['ttl'], wait_for=':' in ip)
		utils.wait_for_replication_from_master_openldap_to_local_samba(ldap_filter=ldap.filter.filter_format('DC=%s', [ldap.dn.str2dn(reverse_zone)[0][0][1]]))
		utils.verify_ldap_object(reverse_zone, {'sOARecord': ['%s %s. %s %s %s %s %s' % (
			reverse_zone_properties['nameserver'],
			reverse_zone_properties['contact'].replace('@', '.'),
			'2',
			reverse_zone_properties['refresh'],
			reverse_zone_properties['retry'],
			reverse_zone_properties['expire'],
			reverse_zone_properties['ttl']
		)]})

	@pytest.mark.parametrize('ip', [
		uts.random_subnet(),
		uts.random_ipv6_subnet(),
	])
	def test_dns_reverse_zone_removal(self, udm, ip):
		"""Remove dns/reverse_zone"""
		reverse_zone = udm.create_object('dns/reverse_zone', subnet=ip, nameserver=uts.random_dns_record())

		udm.remove_object('dns/reverse_zone', dn=reverse_zone)
		utils.verify_ldap_object(reverse_zone, should_exist=False)

	@pytest.mark.parametrize('ip', [
		uts.random_subnet(),
		uts.random_ipv6_subnet(),
	])
	def test_dns_reverse_zone_creation_set_nameserver(self, udm, ip):
		"""Set nameserver during dns/reverse_zone creation"""
		ns_record = uts.random_dns_record()

		reverse_zone = udm.create_object('dns/reverse_zone', subnet=ip, nameserver=ns_record)

		utils.verify_ldap_object(reverse_zone, {'nSRecord': ['%s' % ns_record]})

	@pytest.mark.parametrize('ip', [
		uts.random_subnet(),
		uts.random_ipv6_subnet(),
	])
	def test_dns_reverse_zone_modification_set_nameserver(self, udm, ip):
		"""Set nameserver during dns/reverse_zone modification"""
		ns_record = uts.random_dns_record()

		reverse_zone = udm.create_object('dns/reverse_zone', subnet=uts.random_subnet(), nameserver=uts.random_dns_record(), wait_for=True)

		udm.modify_object('dns/reverse_zone', dn=reverse_zone, nameserver=ns_record, wait_for=True)
		utils.verify_ldap_object(reverse_zone, {'nSRecord': ['%s' % ns_record]})

	@pytest.mark.parametrize('ip', [
		uts.random_subnet(),
		uts.random_ipv6_subnet(),
	])
	def test_dns_reverse_zone_creation_append_nameserver(self, udm, ip):
		"""Append nameserver during dns/reverse_zone creation"""
		ns_records = [uts.random_dns_record(), uts.random_dns_record()]

		reverse_zone = udm.create_object('dns/reverse_zone', subnet=ip, append={'nameserver': ns_records})

		utils.verify_ldap_object(reverse_zone, {'nSRecord': ['%s' % ns_record for ns_record in ns_records]})

	@pytest.mark.parametrize('ip', [
		uts.random_subnet(),
		uts.random_ipv6_subnet(),
	])
	def test_dns_reverse_zone_modification_append_nameserver(self, udm, ip):
		"""Append nameserver during dns/reverse_zone modification"""
		ns_records = [uts.random_dns_record(), uts.random_dns_record(), uts.random_dns_record()]

		reverse_zone = udm.create_object('dns/reverse_zone', subnet=ip, nameserver=ns_records[0], wait_for=True)

		udm.modify_object('dns/reverse_zone', dn=reverse_zone, append={'nameserver': ns_records[1:]}, wait_for=True)
		utils.verify_ldap_object(reverse_zone, {'nSRecord': ['%s' % ns_record for ns_record in ns_records]})

	@pytest.mark.parametrize('ip', [
		uts.random_subnet(),
		uts.random_ipv6_subnet(),
	])
	def test_dns_reverse_zone_modification_remove_nameserver(self, udm, ip):
		"""Remove nameserver during dns/reverse_zone modification"""
		ns_records = [uts.random_dns_record(), uts.random_dns_record(), uts.random_dns_record(), uts.random_dns_record()]
		reverse_zone = udm.create_object('dns/reverse_zone', subnet=ip, append={'nameserver': ns_records}, wait_for=True)

		udm.modify_object('dns/reverse_zone', dn=reverse_zone, remove={'nameserver': ns_records[2:]}, wait_for=True)
		utils.verify_ldap_object(reverse_zone, {'nSRecord': ['%s' % ns_record for ns_record in ns_records[:2]]})


class Test_DNSPointerRecord(object):

	@pytest.mark.parametrize('ip', [
		uts.random_subnet(),
		uts.random_ipv6_subnet(),
	])
	def test_dns_ptr_removal(self, udm, ip):
		"""Remove DNS PTR"""
		reverse_zone = udm.create_object('dns/reverse_zone', subnet=ip, nameserver=uts.random_dns_record())

		ptr_record = uts.random_dns_record()
		ptr = udm.create_object('dns/ptr_record', address='2', superordinate=reverse_zone, ptr_record=ptr_record)

		udm.remove_object('dns/ptr_record', dn=ptr, superordinate=reverse_zone)
		utils.verify_ldap_object(ptr, should_exist=False)

	@pytest.mark.parametrize('ip', [
		uts.random_subnet(),
		uts.random_ipv6_subnet(),
	])
	def test_dns_ptr_creation_set_record(self, udm, ip):
		"""Set ptr_record during dns/ptr_record creation"""
		reverse_zone = udm.create_object('dns/reverse_zone', subnet=ip, nameserver=uts.random_dns_record())

		ptr_record = uts.random_dns_record()
		ptr = udm.create_object('dns/ptr_record', address='2', superordinate=reverse_zone, ptr_record=ptr_record)
		utils.verify_ldap_object(ptr, {'pTRRecord': [ptr_record]})

	@pytest.mark.parametrize('ip', [
		uts.random_subnet(),
		uts.random_ipv6_subnet(),
	])
	def test_dns_ptr_modification_set_record(self, udm, ip):
		"""Set ptr_record during dns/ptr_record modification"""
		reverse_zone = udm.create_object('dns/reverse_zone', subnet=ip, nameserver=uts.random_dns_record())

		ptr_record = uts.random_dns_record()
		ptr = udm.create_object('dns/ptr_record', address='2', superordinate=reverse_zone, ptr_record=ptr_record, wait_for=True)

		ptr_record = uts.random_dns_record()
		udm.modify_object('dns/ptr_record', dn=ptr, superordinate=reverse_zone, ptr_record=ptr_record, wait_for=True)
		utils.verify_ldap_object(ptr, {'pTRRecord': [ptr_record]})

	@pytest.mark.parametrize('ip', [
		uts.random_subnet(),
		uts.random_ipv6_subnet(),
	])
	def test_dns_ptr_modification_append_records(self, udm, ip):
		"""Append ptr_records during dns/ptr_record modification"""
		reverse_zone = udm.create_object('dns/reverse_zone', subnet=ip, nameserver=uts.random_dns_record())

		ptr_record = uts.random_dns_record()
		ptr = udm.create_object('dns/ptr_record', address='2', superordinate=reverse_zone, ptr_record=ptr_record, wait_for=True)

		ptr_records = [uts.random_dns_record(), uts.random_dns_record()]
		udm.modify_object('dns/ptr_record', dn=ptr, superordinate=reverse_zone, append={'ptr_record': ptr_records}, wait_for=True)
		utils.verify_ldap_object(ptr, {'pTRRecord': ptr_records + [ptr_record]})

	@pytest.mark.parametrize('ip', [
		uts.random_subnet(),
		uts.random_ipv6_subnet(),
	])
	def test_dns_ptr_creation_append_records(self, udm, ip):
		"""Append ptr_records during dns/ptr_record creation"""
		reverse_zone = udm.create_object('dns/reverse_zone', subnet=ip, nameserver=uts.random_dns_record())

		ptr_records = [uts.random_dns_record(), uts.random_dns_record()]
		ptr = udm.create_object('dns/ptr_record', address='2', superordinate=reverse_zone, append={'ptr_record': ptr_records})

		utils.verify_ldap_object(ptr, {'pTRRecord': ptr_records})

	@pytest.mark.parametrize('ip', [
		uts.random_subnet(),
		uts.random_ipv6_subnet(),
	])
	def test_dns_ptr_modification_remove_records(self, udm, ip):
		"""Remove ptr_records during dns/ptr_record modification"""
		reverse_zone = udm.create_object('dns/reverse_zone', subnet=ip, nameserver=uts.random_dns_record())

		ptr_records = [uts.random_dns_record(), uts.random_dns_record(), uts.random_dns_record(), uts.random_dns_record()]
		ptr = udm.create_object('dns/ptr_record', address='2', superordinate=reverse_zone, append={'ptr_record': ptr_records}, wait_for=True)

		udm.modify_object('dns/ptr_record', dn=ptr, superordinate=reverse_zone, remove={'ptr_record': ptr_records[:2]}, wait_for=True)
		utils.verify_ldap_object(ptr, {'pTRRecord': ptr_records[2:]})


class Test_DNSWrongSuperordinate(object):

	def test_dns_ptr_creation_with_wrong_superordinate(self, udm):
		"""Create dns/ptr_record with wrong object type as superordinate"""
		# bugs: [15660]
		forward_zone = udm.create_object('dns/forward_zone', nameserver=uts.random_dns_record(), zone='%s.%s' % (uts.random_name(), uts.random_name()))

		with pytest.raises(udm_test.UCSTestUDM_CreateUDMObjectFailed):
			udm.create_object('dns/ptr_record', address='40', superordinate=forward_zone)

	@pytest.mark.parametrize('module', [
		'dns/host_record',
		'dns/alias',
	])
	@pytest.mark.parametrize('ip', [
		uts.random_subnet(),
		uts.random_ipv6_subnet(),
	])
	def test_dns_forward_record_creation_with_wrong_superordinate(self, udm, module, ip):
		"""Create dns/host record with wrong object type as superordinate"""
		# bugs: [15660]
		reverse_zone = udm.create_object('dns/reverse_zone', nameserver=uts.random_dns_record(), subnet=ip)
		with pytest.raises(udm_test.UCSTestUDM_CreateUDMObjectFailed):
			udm.create_object('dns/host_record', name=uts.random_dns_record(), superordinate=reverse_zone)

	@pytest.mark.parametrize('ip', [
		uts.random_subnet(),
		uts.random_ipv6_subnet(),
	])
	def test_dns_srv_record_creation_with_wrong_superordinate(self, udm, ip):
		reverse_zone = udm.create_object('dns/reverse_zone', nameserver=uts.random_dns_record(), subnet=ip)
		with pytest.raises(udm_test.UCSTestUDM_CreateUDMObjectFailed):
			udm.create_object('dns/srv_record', name='%s tcp' % uts.random_name(), location='1 2 3 %s' % uts.random_name(), superordinate=reverse_zone)


class Test_RFC1123(object):

	def test_rfc1123_alias(self, udm):
		forward_zone = udm.create_object('dns/forward_zone', zone='365.ucs', nameserver=uts.random_dns_record())

		cname = uts.random_name()
		dns_alias = udm.create_object('dns/alias', superordinate=forward_zone, name='www', cname=cname)
		utils.verify_ldap_object(dns_alias, {'relativeDomainName': ['www']})
		dns_alias = udm.create_object('dns/alias', superordinate=forward_zone, name='www.sub', cname=cname)
		utils.verify_ldap_object(dns_alias, {'relativeDomainName': ['www.sub']})
		dns_alias = udm.create_object('dns/alias', superordinate=forward_zone, name='ftp.', cname=cname)
		utils.verify_ldap_object(dns_alias, {'relativeDomainName': ['ftp']})

	def test_rfc1123_mail(self, udm):
		mail_domain = udm.create_object('mail/domain', name='123.456.')
		utils.verify_ldap_object(mail_domain, {'cn': ['123.456']})

	def test_rfc1123_mx(self, udm):
		"""Create dns/zone with mx=IP"""
		# Mail server must be a FQHN!
		with pytest.raises(udm_test.UCSTestUDM_CreateUDMObjectFailed):
			udm.create_object('dns/forward_zone', zone='365.ucs', nameserver=uts.random_dns_record(), mx='127.0.0.1')

	def test_rfc1123_ns(self, udm):
		"""Create dns/zone with ns=IP"""
		# Name server must be a FQHN!
		with pytest.raises(udm_test.UCSTestUDM_CreateUDMObjectFailed):
			udm.create_object('dns/forward_zone', zone='365.ucs', nameserver='127.0.0.1')

	def test_rfc1123_numeric(self, udm):
		# All-numeric-FQHNs should not be allowed!'
		with pytest.raises(udm_test.UCSTestUDM_CreateUDMObjectFailed):
			udm.create_object('dns/forward_zone', zone='654.321', nameserver='987.654.321')
