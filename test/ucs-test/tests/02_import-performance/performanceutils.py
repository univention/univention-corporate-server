import subprocess
import sys
import time

import os
import string
import sqlite3

import univention.testing.utils as utils
import univention.testing.udm as udm_test
import univention.testing.strings as uts

import univention.uldap

def import_users(file):
	subprocess.call('/usr/share/ucs-school-import/scripts/ucs-school-import %s' % file, shell=True)

def _start_time():
	return time.time()

def _stop_time(startTime):
	return time.time() - startTime

def wait_for_s4connector():
	conn = sqlite3.connect('/etc/univention/connector/s4internal.sqlite')
	c = conn.cursor()

	static_count = 0
	cache_S4_rejects = None
	t_last_feedback = t_1 = t_0 = time.time()

	highestCommittedUSN = -1
	lastUSN = -1
	while static_count < 2:
		time.sleep(5)

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
		c.execute('select value from S4 where key=="lastUSN"')
		conn.commit()
		lastUSN = c.fetchone()[0]

		if not ( lastUSN == highestCommittedUSN and lastUSN == previous_lastUSN and highestCommittedUSN == previous_highestCommittedUSN ):
			static_count = 0
			print 'Reset counter'
		else:
			static_count = static_count + 1
		print 'Counter: %d' % static_count

	conn.close()
	return True

def test_umc_admin_auth():
	result = subprocess.call('umc-command  -U Administrator -P univention udm/get -f users/user -l -o "uid=Administrator,cn=users,$(ucr get ldap/base)"', shell=True)
	return result

def s4_user_auth(username, password):
	result = subprocess.call('smbclient -U %s //localhost/sysvol -c ls %s' % (username, password), shell=True)
	return result
	
def reset_passwords(user_dns):
	for dn in user_dns:
		subprocess.call('udm users/user modify --dn "%s" --set password="Univention.991"' %  dn, shell=True)
	wait_for_s4connector()

def get_user_dn_list(CSV_IMPORT_FILE):
	user_dns = []

	lo = univention.uldap.getMachineConnection()

	for line in open(CSV_IMPORT_FILE).readlines():
		if len(user_dns) >= 40:
			break
		username = line.split('\t')[1]
		dn = lo.searchDn('(&(uid=%s)(objectClass=sambaSamAccount))' % username)
		user_dns.append(dn[0])

	return user_dns

def create_test_user():
	udm = udm_test.UCSTestUDM()
	username = udm.create_user()[1]
	wait_for_s4connector()

def execute_timing(description, allowedTime, callback, *args):
	print 'Starting %s' % description

	startTime = _start_time()
	result = callback(*args)
	duration = _stop_time(startTime)
	
	print 'INFO: %s took %ld (allowed time: %ld)' % (description, duration, allowedTime)

	if result != 0:
		print 'Error: callback returned: %d' % result
		return False

	if duration > allowedTime:
		print 'ERROR: %s took too long' % description
		return False

	return True

