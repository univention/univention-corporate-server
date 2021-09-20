import subprocess

from ldap.filter import filter_format

from univention.management.console.modules.setup.util import _temporary_password_file

# do we need to keep this backwards compatible with UCS 4.4?
_SCRIPT = '''#!/usr/bin/python2.7
from univention.uldap import getAdminConnection
connection = getAdminConnection()
results = connection.search(filter="(&(objectClass=person)(uid=%%s))")
if len(results) == 0:
	exit(0)
elif len(results) == 1:
	role = results[0][1]["univentionServerRole"][0].decode("UTF-8")
	if role in "%s":
		exit(0)
exit(1)
'''


def check_if_uid_is_available(uid, role, address, username, password):
	with _temporary_password_file(password) as password_file:
		process = subprocess.Popen([
			'univention-ssh', password_file, '%s@%s' % (username, address),
			'/usr/bin/python2.7', '-'
		], stdin=subprocess.PIPE)
		process.communicate((filter_format(_SCRIPT % (role,), [uid])).encode('UTF-8'))
		if process.wait() != 0:
			return False
	return True
