#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: Check if nameservers in forward/reverse DNS zones are updated when deleting the nameserver
## tags: [udm-computers]
## roles: [domaincontroller_master]
## exposure: careful
## packages:
##   - univention-config
##   - univention-directory-manager-tools

import pytest

import univention.testing.udm as udm_test
from univention.testing import utils

COMPUTER_MODULES = udm_test.UCSTestUDM.COMPUTER_MODULES


@pytest.mark.tags('udm-computers')
@pytest.mark.roles('domaincontroller_master')
@pytest.mark.exposure('careful')
@pytest.mark.parametrize('role', COMPUTER_MODULES)
def test_nameserver_update_in_zone_on_delete(udm, verify_ldap_object, role):
		"""Check if nameservers in forward/reverse DNS zones are updated when deleting the nameserver"""
		# create zones and computer
		server_name = 'qwertzu'
		domain = 'asdfgh'
		fqdn_dot = server_name + '.' + domain + '.'
		forward = udm.create_object('dns/forward_zone', zone=domain, nameserver='aaa.aa.')
		reverse = udm.create_object('dns/reverse_zone', subnet='10.20.30', nameserver='aaa.aa.')
		computer = udm.create_object(role, set={
			'ip': '10.20.30.3',
			'name': server_name,
			'dnsEntryZoneForward': forward,
			'dnsEntryZoneReverse': reverse,
			'domain': domain,
		})
		udm.modify_object('dns/forward_zone', dn=forward, nameserver=[fqdn_dot], wait_for_replication=False)
		udm.modify_object('dns/reverse_zone', dn=reverse, nameserver=[fqdn_dot], wait_for=True)
		utils.wait_for_connector_replication()
		verify_ldap_object(forward, {'nSRecord': ['aaa.aa.', fqdn_dot]})
		verify_ldap_object(reverse, {'nSRecord': ['aaa.aa.', fqdn_dot]})

		# delete computer and check new name in zones
		udm.remove_object(role, dn=computer, wait_for=True)
		utils.wait_for_connector_replication()
		verify_ldap_object(forward, {'nSRecord': ['aaa.aa.', ]})
		verify_ldap_object(reverse, {'nSRecord': ['aaa.aa.', ]})
