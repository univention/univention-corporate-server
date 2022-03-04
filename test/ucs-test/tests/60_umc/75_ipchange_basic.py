#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: Check basic ip_change functionality
## roles-not: [basesystem]
## exposure: dangerous

import pytest

import univention.testing.strings as uts
import univention.testing.utils as utils
from univention.testing.umc import Client


@pytest.mark.tags('udm')  # Correct?
@pytest.mark.roles_not('basesystem')
@pytest.mark.exposure('dangerous')
def test_ipchange_basic(udm, ucr):
	"""Check basic ip_change functionality"""
	role = ucr.get('server/role')
	if role == 'domaincontroller_master':
		role = 'domaincontroller_backup'
	computerName = uts.random_string()
	computer = udm.create_object('computers/%s' % role, name=computerName, password='univention', network='cn=default,cn=networks,%s' % ucr.get('ldap/base'))

	lo = utils.get_ldap_connection()
	computer_object = lo.get(computer)
	print(computer_object)
	ip = computer_object['aRecord']
	utils.verify_ldap_object(computer, {'aRecord': ip})

	new_ip = '1.2.3.4'

	iface = ucr.get('interfaces/primary', 'eth0')
	client = Client(ucr.get('ldap/master'), '%s$' % computerName, 'univention')
	client.umc_command('ip/change', {'ip': new_ip, 'oldip': ip[0].decode('UTF-8'), 'netmask': ucr.get('interfaces/%s/netmask' % iface), 'role': role})

	utils.wait_for_replication()
	utils.verify_ldap_object(computer, {'aRecord': [new_ip]}, strict=True)
