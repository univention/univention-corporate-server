import subprocess
from pathlib import Path
import random
from time import sleep

from univention.testing.strings import random_username


def test_listener(udm, ucr, base_user, group1, group2):
	wait_for_replication = False
	created_users = []
	for x in range(1, 11):
		if x % 10 == 0:
			wait_for_replication = not wait_for_replication
		new_user = udm.create_object('users/user', position=base_user, username=random_username(), lastname=random_username(),
		                  password=random_username(), wait_for_replication=wait_for_replication)
		created_users.append(new_user)
		wait_for_replication = False
		sleep(1)
		rebuild()
		check_logs()
	cleanup()
	for user in created_users[len(created_users) // 2:]:
		udm.modify_object('groups/group', dn=random.choice([group1, group2]), users=[user], wait_for_replication=True)

	cleanup()
	for user in created_users[:len(created_users) // 2]:
		udm.remove_object('users/user', dn=user, wait_for_replication=True)
		check_logs()
	cleanup()


def rebuild():
	subprocess.call(
		['/usr/share/univention-group-membership-cache/univention-ldap-cache', 'rebuild', 'uniqueMembers'])


def cleanup():
	subprocess.call(
		['/usr/share/univention-group-membership-cache/univention-ldap-cache', 'cleanup'])


def check_logs():
	# look for tracebacks in the log
	print('Looking for tracebacks in the logs')
	for file in Path('/var/log/univention/listener_modules/').rglob('*.log'):
		if file.name.startswith('ldap-cache'):
			with file.open() as f:
				for line in f:
					if 'Traceback' in line:
						print(line)
						raise Exception('Traceback found in listener.log')
			print('No traceback found in %s' % file)