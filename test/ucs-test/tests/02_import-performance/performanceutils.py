import subprocess
import time
import re
import json
import os.path
from ucsschool.importer.mass_import import user_import

import sqlite3

import univention.testing.utils as utils
import univention.testing.udm as udm_test
import univention.testing.strings as uts

import univention.uldap

CONNECTOR_WAIT_INTERVAL = 12
CONNECTOR_WAIT_SLEEP = 5
CONNECTOR_WAIT_TIME = CONNECTOR_WAIT_SLEEP * CONNECTOR_WAIT_INTERVAL

lo = None


def import_users(file):
	subprocess.call('/usr/share/ucs-school-import/scripts/ucs-school-import %s' % file, shell=True)
	return 0


def import_users_new(args):
	print('*** import_users_new({!r})'.format(args))
	subprocess.call('/usr/share/ucs-school-import/scripts/ucs-school-testuser-import {}'.format(args), shell=True)
	return 0


def create_ous(names_of_ous):
	res = 0
	for school_name in names_of_ous:
		res += subprocess.call('/usr/share/ucs-school-import/scripts/create_ou {}'.format(school_name), shell=True)
	return res


def remove_ous(names_of_ous):
	res = 0
	for school_name in names_of_ous:
		res += subprocess.call('udm container/ou remove --dn={}'.format(school_name), shell=True)
	return res


def _start_time():
	return time.time()


def _stop_time(startTime):
	return time.time() - startTime


def _ldap_replication_complete():
	return subprocess.call('/usr/lib/nagios/plugins/check_univention_replication') == 0


def wait_for_s4connector():
	conn = sqlite3.connect('/etc/univention/connector/s4internal.sqlite')
	c = conn.cursor()

	static_count = 0
	cache_S4_rejects = None
	t_last_feedback = t_1 = t_0 = time.time()

	highestCommittedUSN = -1
	lastUSN = -1
	while static_count < CONNECTOR_WAIT_INTERVAL:
		time.sleep(CONNECTOR_WAIT_SLEEP)

		if not _ldap_replication_complete():
			continue

		previous_highestCommittedUSN = highestCommittedUSN

		highestCommittedUSN = -1
		ldbsearch = subprocess.Popen("ldbsearch -H /var/lib/samba/private/sam.ldb -s base -b '' highestCommittedUSN", shell=True, stdout=subprocess.PIPE)
		ldbresult = ldbsearch.communicate()
		for line in ldbresult[0].split('\n'):
			line = line.strip()
			if line.startswith('highestCommittedUSN: '):
				highestCommittedUSN = line.replace('highestCommittedUSN: ', '')
				break

		print highestCommittedUSN

		previous_lastUSN = lastUSN
		try:
			c.execute('select value from S4 where key=="lastUSN"')
		except sqlite3.OperationalError as e:
			static_count = 0
			print 'Reset counter: sqlite3.OperationalError: %s' % e
			print 'Counter: %d' % static_count
			continue

		conn.commit()
		lastUSN = c.fetchone()[0]

		if not (lastUSN == highestCommittedUSN and lastUSN == previous_lastUSN and highestCommittedUSN == previous_highestCommittedUSN):
			static_count = 0
			print 'Reset counter'
		else:
			static_count = static_count + 1
		print 'Counter: %d' % static_count

	conn.close()
	return 0


def test_umc_admin_auth():
	result = subprocess.call('umc-command -U Administrator -P univention ucr/get -l -o "apache2/autostart"', shell=True)
	return result


def test_umc_admin_auth_udm_load():
	result = subprocess.call('umc-command -U Administrator -P univention udm/get -f users/user -l -o "uid=Administrator,cn=users,$(ucr get ldap/base)"', shell=True)
	return result


def s4_user_auth(username, password):
	result = subprocess.call('smbclient -U %s //localhost/sysvol -c ls %s' % (username, password), shell=True)
	return result


def reset_passwords(user_dns):
	for dn in user_dns:
		subprocess.call('udm users/user modify --dn "%s" --set password="Univention.991"' % dn, shell=True)
	wait_for_s4connector()
	return 0


def get_user_dn(username):
	global lo
	if not lo:
		lo = univention.uldap.getMachineConnection()
	dn = lo.searchDn('(&(uid=%s)(objectClass=sambaSamAccount))' % username)
	return dn[0]


def get_user_dn_list(CSV_IMPORT_FILE):
	user_dns = []

	for line in open(CSV_IMPORT_FILE).readlines():
		if len(user_dns) >= 40:
			break
		username = line.split('\t')[1]
		user_dns.append(get_user_dn(username))

	return user_dns


def get_user_dn_list_new(CSV_IMPORT_FILE):
	# must import ucsschool.importer.utils.shell *after* creating ~/.import_shell_config
	with open('/usr/share/ucs-school-import/configs/ucs-school-testuser-import.json', 'rb') as fp:
		config = json.load(fp)
	config['input']['filename'] = CSV_IMPORT_FILE
	with open(os.path.expanduser('~/.import_shell_config'), 'wb') as fp:
		json.dump(config, fp)
	from ucsschool.importer.utils.shell import logger  # this will setup a complete import system configuration
	up = user_import.UserImport()
	imported_users = up.read_input()
	user_dns = list()
	for user in imported_users:
		user.make_username()
		if re.match(r'.*\d$', user.name):
			username = user.name[:-1]
		else:
			username = user.name
		try:
			user_dns.append(get_user_dn(username))
		except IndexError:
			# username calculated differently when importing and now, can happen, ignore
			pass
		if len(user_dns) >= 40:
			break
	return user_dns


def create_test_user():
	udm = udm_test.UCSTestUDM()
	username = udm.create_user(wait_for_replication=False)[1]
	wait_for_s4connector()
	return s4_user_auth(username, 'univention')


def execute_timing(description, allowedTime, callback, *args):
	print 'Starting %s' % description

	startTime = _start_time()
	result = callback(*args)
	duration = _stop_time(startTime)

	print 'INFO: %s took %ld seconds (allowed time: %ld seconds)' % (description, duration, allowedTime)

	if result != 0:
		print 'Error: callback returned: %d' % result
		return False

	if duration > allowedTime:
		print 'ERROR: %s took too long' % description
		return False

	return True


def count_ldap_users():
	global lo
	if not lo:
		lo = univention.uldap.getMachineConnection()
	res = lo.search('(&(uid=*)(!(uid=*$))(objectClass=sambaSamAccount))', attr=['dn'])
	print 'INFO: Found %d OpenLDAP users' % len(res)

	return len(res)


def count_samba4_users():
	count = 0

	ldbsearch = subprocess.Popen("ldbsearch -H /var/lib/samba/private/sam.ldb objectClass=user dn", shell=True, stdout=subprocess.PIPE)
	ldbresult = ldbsearch.communicate()
	for line in ldbresult[0].split('\n'):
		line = line.strip()
		if line.startswith('dn: '):
			count += 1

	print 'INFO: Found %d Samba4 users' % count

	return count


def count_users(needed):
	users = count_ldap_users()
	if users < needed:
		print 'ERROR: Not all users were found in OpenLDAP'
		returnCode = False

	users = count_samba4_users()
	if users < needed:
		print 'ERROR: Not all users were found in Samba4'
		returnCode = False

	return True
