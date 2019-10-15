from univention.management.console.modules.setup.util import _temporary_password_file

import subprocess


def check_if_uid_is_available(uid, role, address, username, password):
	with _temporary_password_file(password) as password_file:
		process = subprocess.Popen([
			'univention-ssh', password_file, '%s@%s' % (username, address),
			'python', '-'
		], stdin=subprocess.PIPE)
		process.communicate(
			'from univention.uldap import getAdminConnection\n' +
			'connection = getAdminConnection()\n' +
			'results = connection.search(filter="uid=%s")\n' % (uid,) +
			'if len(results) == 0:\n' +
			'    exit(0)\n' +
			'elif len(results) == 1:\n' +
			'    role = results[0][1]["univentionServerRole"][0]\n' +
			'    if role in "%s":\n' % (role,) +
			'        exit(0)\n' +
			'exit(1)\n'
		)
		if process.wait() != 0:
			return False
	return True
