"""
Common functions used by tests.
"""
# Copyright 2013-2015 Univention GmbH
#
# http://www.univention.de/
#
# All rights reserved.
#
# The source code of this program is made available
# under the terms of the GNU Affero General Public License version 3
# (GNU AGPL V3) as published by the Free Software Foundation.
#
# Binary versions of this program provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention and not subject to the GNU AGPL V3.
#
# In the case you use this program under the terms of the GNU AGPL V3,
# the program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <http://www.gnu.org/licenses/>.

import sys
import subprocess
import ldap
import time

import univention.config_registry
import univention.uldap as uldap

S4CONNECTOR_INIT_SCRIPT = '/etc/init.d/univention-s4-connector'
LISTENER_INIT_SCRIPT = '/etc/init.d/univention-directory-listener'


class LDAPError(Exception):
	pass


class LDAPReplicationFailed(LDAPError):
	pass


class LDAPObjectNotFound(LDAPError):
	pass


class LDAPUnexpectedObjectFound(LDAPError):
	pass


class LDAPObjectValueMissing(LDAPError):
	pass


class LDAPObjectUnexpectedValue(LDAPError):
	pass


class UCSTestDomainAdminCredentials(object):
	"""
	This class fetches the username, the LDAP bind DN and the password
	for a domain admin user account from UCR. The account may be used for testing.

	>>> account = UCSTestDomainAdminCredentials()
	>>> account.username
	'Administrator'
	>>> account.binddn
	'uid=Administrator,cn=users,dc=example,dc=com'
	>>> account.bindpw
	'univention'
	"""
	def __init__(self, ucr=None):
		if not ucr:
			ucr = univention.config_registry.ConfigRegistry()
			ucr.load()
		self.binddn = ucr.get('tests/domainadmin/account', 'uid=Administrator,cn=users,%s' % ucr.get('ldap/base'))
		pwdfile = ucr.get('tests/domainadmin/pwdfile')
		if pwdfile:
			with open(pwdfile, 'r') as f:
				self.bindpw = f.read().strip('\n\r')
		else:
			self.bindpw = ucr.get('tests/domainadmin/pwd', 'univention')
		if self.binddn:
			self.username = uldap.explodeDn(self.binddn, 1)[0]
		else:
			self.username = None


def get_ldap_connection(pwdfile = False, start_tls = 2, decode_ignorelist = []):
	ucr = univention.config_registry.ConfigRegistry()
	ucr.load()

	port = int(ucr.get('ldap/server/port', 7389))
	binddn = ucr.get('tests/domainadmin/account', 'uid=Administrator,cn=users,%s' % ucr['ldap/base'])
	bindpw = None
	ldapServers = []
	if ucr['ldap/server/name']:
		ldapServers.append(ucr['ldap/server/name'])
	if ucr['ldap/servers/addition']:
		ldapServers.extend(ucr['ldap/server/addition'].split())

	if pwdfile:
		with open(ucr['tests/domainadmin/pwdfile']) as f:
			bindpw = f.read().strip('\n')
	else:
		bindpw = ucr['tests/domainadmin/pwd']

	for ldapServer in ldapServers:
		try:
			return uldap.access(host=ldapServer, port=port, base=ucr['ldap/base'], binddn=binddn, bindpw=bindpw, start_tls=start_tls, decode_ignorelist=decode_ignorelist)
		except ldap.SERVER_DOWN():
			pass
	raise ldap.SERVER_DOWN()


def verify_ldap_object(baseDn, expected_attr = {}, strict = True, should_exist = True):
	try:
		dn, attr = get_ldap_connection().search(filter = '(objectClass=*)', base = baseDn, scope = ldap.SCOPE_BASE, attr = expected_attr.keys())[0]
	except (ldap.NO_SUCH_OBJECT, IndexError):
		if should_exist:
			raise LDAPObjectNotFound('DN: %s' % baseDn)
		return

	if not should_exist:
		raise LDAPUnexpectedObjectFound('DN: %s' % baseDn)

	for attribute, expected_values in expected_attr.items():
		found_values = set(attr.get(attribute, []))
		expected_values = set(expected_values)

		difference = expected_values - found_values
		if difference:
			raise LDAPObjectValueMissing('DN: %s\n%s: %r, missing: \'%s\'' % (baseDn, attribute, list(found_values), '\', '.join(difference)))

		if strict:
			difference = found_values - expected_values
			if difference:
				raise LDAPObjectUnexpectedValue('DN: %s\n%s: %r, unexpected: \'%s\'' % (baseDn, attribute, list(found_values), '\', '.join(difference)))


def s4connector_present():
	ucr = univention.config_registry.ConfigRegistry()
	ucr.load()

	if ucr.is_true('directory/manager/samba3/legacy', False):
		return False
	if ucr.is_false('directory/manager/samba3/legacy', False):
		return True

	for dn, attr in get_ldap_connection().search(filter = '(&(|(objectClass=univentionDomainController)(objectClass=univentionMemberServer))(univentionService=S4 Connector))', attr = ['aRecord']):
		if 'aRecord' in attr:
			return True
	return False


def stop_s4connector():
	subprocess.call((S4CONNECTOR_INIT_SCRIPT, 'stop'))


def start_s4connector():
	subprocess.call((S4CONNECTOR_INIT_SCRIPT, 'start'))


def stop_listener():
	subprocess.call((LISTENER_INIT_SCRIPT, 'stop'))


def start_listener():
	subprocess.call((LISTENER_INIT_SCRIPT, 'start'))


def restart_listener():
	subprocess.call((LISTENER_INIT_SCRIPT, 'restart'))


class AutomaticListenerRestart(object):
	"""
		Automatically restart Univention Directory Listener when leaving the "with" block.

		with AutomaticListenerRestart() as alr:
			with ucr_test.UCSTestConfigRegistry() as ucr:
				# set some ucr variables, that influence the Univention Directory Listener
				univention.config_registry.handler_set(['foo/bar=ding/dong'])
	"""
	def __enter__(self):
		return self

	def __exit__(self, exc_type, exc_value, traceback):
		restart_listener()


class AutoCallCommand(object):
	"""
		Automatically call the given commands when entering/leaving the "with" block.
		The keyword arguments enter_cmd and exit_cmd are optional.

		with AutoCallCommand(enter_cmd=['/etc/init.d/dovecot', 'reload'],
							 exit_cmd=['/etc/init.d/dovecot', 'restart']) as acc:
			with ucr_test.UCSTestConfigRegistry() as ucr:
				# set some ucr variables, that influence the Univention Directory Listener
				univention.config_registry.handler_set(['foo/bar=ding/dong'])

		In case some filedescriptors for stdout/stderr have to be passed to the executed
		command, they may be passed as kwarg:

		with AutoCallCommand(enter_cmd=['/etc/init.d/dovecot', 'reload'],
							 exit_cmd=['/etc/init.d/dovecot', 'restart'],
							 stderr=open('/dev/zero', 'w')) as acc:
	"""
	def __init__(self, enter_cmd=None, exit_cmd=None, stdout=None, stderr=None):
		self.enter_cmd = None
		if type(enter_cmd) in (list, tuple):
			self.enter_cmd = enter_cmd
		self.exit_cmd = None
		if type(exit_cmd) in (list, tuple):
			self.exit_cmd = exit_cmd
		self.pipe_stdout = stdout
		self.pipe_stderr = stderr

	def __enter__(self):
		if self.enter_cmd:
			subprocess.call(self.enter_cmd, stdout=self.pipe_stdout, stderr=self.pipe_stderr)
		return self

	def __exit__(self, exc_type, exc_value, traceback):
		if self.exit_cmd:
			subprocess.call(self.exit_cmd, stdout=self.pipe_stdout, stderr=self.pipe_stderr)

class FollowLogfile(object):
	"""
		Prints the contents of the listed files on exit of the with block if
		an exception occured.
		Set always=True to also print them without exception.
		You may wish to make the server flush its logs before existing the
		with block. Use AutoCallCommand inside the block for that.

		with FollowLogfile(logfiles=['/var/log/syslog', '/var/log/mail.log']) as flf:
			with utils.AutoCallCommand(enter_cmd=['doveadm', 'log', 'reopen'],
				exit_cmd=['doveadm', 'log', 'reopen']) as acc:
				...

		with FollowLogfile(logfiles=['/var/log/syslog'], always=True) as flf:
			with utils.AutoCallCommand(enter_cmd=['doveadm', 'log', 'reopen'],
				exit_cmd=['doveadm', 'log', 'reopen']) as acc:
				...
	"""
	def __init__(self, logfiles=None, always=False):
		"""
		:param logfiles: list of absolut filenames to read from
		:param always: bool, if True: print logfile change also if no error occurred (default=False)
		"""
		assert isinstance(logfiles, list)
		self.logfiles = logfiles
		assert isinstance(always, bool)
		self.always = always
		self.logfile_pos = dict()

	def __enter__(self):
		for logfile in self.logfiles:
			with open(logfile, "rb") as log:
				log.seek(0, 2)
				self.logfile_pos[logfile] = log.tell()
		return self

	def __exit__(self, exc_type, exc_value, traceback):
		if self.always or exc_type:
			for logfile, pos in self.logfile_pos.items():
				with open(logfile, "r") as log:
					log.seek(pos, 0)
					lim = (79 - len(logfile) - 2) / 2
					lin = "{0} {1} {0}".format("=" * lim, logfile)
					print lin + "=" * (79-len(lin))
					sys.stdout.writelines(log)
					print "=" * 79


def wait_for_replication():
	sys.stdout.flush()
	print 'Waiting for replication:'
	for _ in xrange(300):
		rc = subprocess.call('/usr/lib/nagios/plugins/check_univention_replication')
		if rc == 0:
			print 'Done: replication complete.'
			return
		time.sleep(1)

	print 'Error: replication incomplete.'
	raise LDAPReplicationFailed()


def wait_for_replication_and_postrun ():
	wait_for_replication ()
	print "Waiting for postrun"
	time.sleep(17)


def wait_for_connector_replication():
	print 'Waiting for connector replication'
	time.sleep(17)


def package_installed(package):
	sys.stdout.flush()
	with open('/dev/null', 'w') as null:
		return (subprocess.call(['dpkg-query', '-W', package], stderr=null) == 0)


def fail(log_message = None, returncode = 1):
	print '### FAIL ###'
	if log_message:
		print '%s\n###      ###' % log_message
	sys.exit(returncode)


def uppercase_in_ldap_base():
	ucr = univention.config_registry.ConfigRegistry()
	ucr.load()
	return not ucr.get('ldap/base').islower()


if __name__ == '__main__':
	import doctest
	doctest.testmod()

# vim: set fileencoding=utf-8 ft=python sw=4 ts=4 et :
