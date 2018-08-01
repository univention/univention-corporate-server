from univention.management.console.modules.setup.util import _temporary_password_file

import subprocess

def check_if_uid_is_available(uid, nameserver, username, password):
	with _temporary_password_file(password) as password_file:
		process = subprocess.Popen([
			'univention-ssh', password_file, '%s@%s' % (username, nameserver),
			'python', '-'
		], stdin=subprocess.PIPE)
		process.communicate(
			'from univention.uldap import getAdminConnection; ' +
			'connection = getAdminConnection(); ' +
			'result = connection.search(filter="uid=%s"); ' % (uid,) +
			'exit(1) if result else exit(0);'
		)
		if process.wait() != 0:
			return False
	return True
