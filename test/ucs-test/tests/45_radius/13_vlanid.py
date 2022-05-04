#!/usr/share/ucs-test/runner pytest-3 -s -vvv
## desc: check if vlan-id is returned correctly in radius response
## tags: [apptest, radius]
## packages:
##   - univention-radius
## join: true
## exposure: dangerous

import pytest
import os
import subprocess
import re
import univention.uldap as uldap
import univention.testing.ucr as ucr_test
from univention.config_registry import handler_set as ucr_set
from univention.config_registry import handler_unset as ucr_unset
from univention.config_registry import handler_get as ucr_get


def test_run_joinscript():
	adm = list(ucr_get(['tests/domainadmin/account']))[0]
	admin = adm[adm.find('uid=')+4:adm.find('cn=')-1]
	pwdfile = list(ucr_get(['tests/domainadmin/pwdfile']))[0]
	ret = subprocess.run([
			'/usr/share/univention-join/univention-run-join-scripts',
			'-dcaccount', admin,
			'-dcpwd', pwdfile,
			'--force',
			'--run-scripts', '80univention-radius.inst',
		], check=True)
	assert ret != 0


@pytest.fixture
def credentials(ucr, lo):
	krb5PrincipalName = lo.search(filter='(&(objectClass=univentionHost)(cn={}))'.format(ucr.get('hostname')))[0][1]['krb5PrincipalName'][0].decode('UTF-8')
	return (krb5PrincipalName, open('/etc/machine.secret').read())


def restart_service(service):
	subprocess.call(['systemctl', 'restart', service])


def default_vlan_id(vlan_id, restart_freeradius):
	if not vlan_id:
		ucr_unset(['freeradius/vlan-id'])
	else:
		ucr_set(['freeradius/vlan-id={}'.format(vlan_id)])
	if restart_freeradius:
		restart_service('freeradius')


def find_vlanid(message):
	vlan_regex = "Tunnel-Private-Group-Id:0 = \"(.*?)\""
	search = re.search(vlan_regex, message)
	if search:
		return search.group(1).strip()


def radius_auth(username, password, user_type, auth_method):
	if user_type == 'computer':
		p = subprocess.run([
			'radtest',
			'-x',
			'-t',
			'mschap',
			username,
			password,
			'127.0.0.1',
			'0',
			'testing123',
		], capture_output=True, text=True, check=True)
	elif user_type == 'user':
		if auth_method in ('pap', 'mschap'):
			p = subprocess.run(['radtest', '-x', '-t', auth_method, username, password, 'localhost', '0', 'testing123'], capture_output=True, text=True, check=True)
		elif auth_method == 'eap':
			credentials = 'user-name={username}, user-password={password}'.format(username=username, password=password)
			echo_username_password = subprocess.Popen(('echo', credentials), stdout=subprocess.PIPE)
			p = subprocess.run(['radeapclient', '-x', 'localhost', 'auth', 'testing123'], stdin=echo_username_password.stdout, capture_output=True,
									text=True, check=True)
			echo_username_password.wait()
		else:
			raise ValueError("Unexpected radius authmethod '{}'".format(auth_method))
	else:
		raise ValueError("Unexpected user_type '{}'".format(user_type))
	return find_vlanid(p.stdout)


@pytest.mark.parametrize('vlan_id_group_one, vlan_id_group_two, ucr_vlan_id, expected_vlan_id, restart_freeradius', [
	('5', None, '8', '5', True),
	(None, '7', '8', '7', False),
	(None, None, '8', '8', False),
	(None, None, None, None, True),
])
def test_user_vlan_id(udm_session, vlan_id_group_one, vlan_id_group_two, ucr_vlan_id, expected_vlan_id, restart_freeradius):
	default_vlan_id(ucr_vlan_id, restart_freeradius)
	userdn, username = udm_session.create_user(set={'networkAccess': 1})
	group_one_set = {
		'networkAccess': 1,
		'users': userdn,
	}
	if vlan_id_group_one:
		group_one_set['vlanId'] = vlan_id_group_one
	groupdn_one, groupname_one = udm_session.create_group(set=group_one_set)
	group_two_set = {
		'networkAccess': 1,
		'users': userdn,
	}
	if vlan_id_group_two:
		group_two_set['vlanId'] = vlan_id_group_two
	groupdn_two, groupname_two = udm_session.create_group(set=group_two_set)
	for auth_method in ('pap', 'mschap', 'eap'):
		assert radius_auth(username, 'univention', 'user', auth_method) == expected_vlan_id


@pytest.mark.parametrize('vlg1, vlg2, ucr_vlan_id, expected_vlan_id, restart_freeradius', [
	('1', '', '2', '1', True),
	('', '3', '2', '3', False),
	('', '', '2', '2', False),
	('', '', '', None, True),
])
def test_host_auth(udm_session, ucr_session, credentials, vlg1, vlg2, ucr_vlan_id, expected_vlan_id, restart_freeradius):
	default_vlan_id(ucr_vlan_id, restart_freeradius)
	hostdn = ucr_session.get('ldap/hostdn')
	group1dn, group1name = udm_session.create_group(set={
		'networkAccess': 1,
		'hosts': hostdn,
		'vlanId': vlg1
	})
	group2dn, group2name = udm_session.create_group(set={
		'networkAccess': 1,
		'hosts': hostdn,
		'vlanId': vlg2
	})
	name, password = credentials
	vlanid = radius_auth(name, password, 'computer', None)
	# Remove group objects manually as existing groups are impacting test results of subsequent runs
	udm_session.remove_object('groups/group', dn=group1dn, wait_for=True)
	udm_session.remove_object('groups/group', dn=group2dn, wait_for=True)
	assert vlanid == expected_vlan_id
