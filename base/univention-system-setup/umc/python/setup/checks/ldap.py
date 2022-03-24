from pipes import quote
from subprocess import PIPE, Popen

from ldap.filter import filter_format

from univention.management.console.modules.setup.util import _temporary_password_file
from univention.management.console.log import MODULE


def check_if_uid_is_available(uid, role, address, username, password):
	"""check if either the UID it not yet taken at all
		or it is already taken (by our previous self) and still matches the server role
	"""
	# type: (str, str, str, str, str) -> bool
	filter_s = filter_format("(&(objectClass=person)(uid=%s)(!(univentionServerRole=%s)))", [uid, role])
	rcmd = 'univention-ldapsearch -LLL %s 1.1' % (quote(filter_s),)
	with _temporary_password_file(password) as password_file:
		cmd = [
			"univention-ssh", "--no-split",
			password_file,
			'%s@%s' % (username, address),
			rcmd
		]
		MODULE.info("Running %s" % " ".join(quote(arg) for arg in cmd))
		process = Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE)
		stdout, stderr = process.communicate()
		if process.wait() or stderr:
			MODULE.error("Failed checking uid=%s role=%s: %s" % (uid, role, stderr))
	return not stdout.strip()
