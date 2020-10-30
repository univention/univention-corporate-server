"""
Common functions used by tests.
"""
# Copyright 2013-2020 Univention GmbH
#
# https://www.univention.de/
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
# <https://www.gnu.org/licenses/>.

from __future__ import print_function

import sys
import functools
import subprocess
import traceback
import ldap
import time
import socket
import os
from enum import IntEnum

import six

import univention.uldap as uldap
from univention.config_registry import ConfigRegistry

try:
	from univention.admin.uldap import access
except ImportError:
	access = None
try:
	from types import TracebackType  # noqa F401
	from typing import Any, Callable, Dict, IO, Iterable, List, NoReturn, Optional, Sequence, Text, Tuple, Type, Union  # noqa F401
except ImportError:
	pass

S4CONNECTOR_INIT_SCRIPT = '/etc/init.d/univention-s4-connector'
FIREWALL_INIT_SCRIPT = '/etc/init.d/univention-firewall'
SLAPD_INIT_SCRIPT = '/etc/init.d/slapd'

UCR = ConfigRegistry()


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

	>>> dummy_ucr = {'ldap/base': 'dc=example,dc=com', 'tests/domainadmin/pwdfile': '/dev/null'}
	>>> account = UCSTestDomainAdminCredentials(ucr=dummy_ucr)
	>>> account.username
	'Administrator'
	>>> account.binddn
	'uid=Administrator,cn=users,dc=example,dc=com'
	>>> account.bindpw
	''
	"""

	def __init__(self, ucr=None):
		# type: (Optional[ConfigRegistry]) -> None
		if ucr is None:
			ucr = UCR
			ucr.load()
		self.binddn = ucr.get('tests/domainadmin/account', 'uid=Administrator,cn=users,%(ldap/base)s' % ucr)
		pwdfile = ucr.get('tests/domainadmin/pwdfile')
		if pwdfile:
			with open(pwdfile, 'r') as f:
				self.bindpw = f.read().strip('\n\r')
		else:
			self.bindpw = ucr.get('tests/domainadmin/pwd', 'univention')
		if self.binddn:
			self.username = uldap.explodeDn(self.binddn, 1)[0]  # type: Optional[Text]
		else:
			self.username = None


def get_ldap_connection(pwdfile=False, start_tls=2, decode_ignorelist=None, admin_uldap=False):
	# type: (bool, int, Optional[List[Text]], bool) -> access
	if decode_ignorelist is None:
		decode_ignorelist = []
	ucr = UCR
	ucr.load()

	port = int(ucr.get('ldap/server/port', 7389))
	binddn = ucr.get('tests/domainadmin/account', 'uid=Administrator,cn=users,%(ldap/base)s' % ucr)
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
			lo = uldap.access(host=ldapServer, port=port, base=ucr['ldap/base'], binddn=binddn, bindpw=bindpw, start_tls=start_tls, decode_ignorelist=decode_ignorelist, follow_referral=True)
			if admin_uldap:
				lo = access(lo=lo)
			return lo
		except ldap.SERVER_DOWN:
			pass
	raise ldap.SERVER_DOWN()


def retry_on_error(func, exceptions=(Exception,), retry_count=20, delay=10):
	# type: (Callable, Tuple[Type[Exception], ...], int, Union[float, int]) -> Any
	"""
	This function calls the given function `func`.
	If one of the specified `exceptions` is caught, `func` is called again until
	the retry count is reached or any unspecified exception is caught. Between
	two calls of `func` retry_on_error waits for `delay` seconds.

	:param func: function to be called
	:param exceptions: tuple of exception classes, that cause a rerun of `func`
	:param retry_count: retry the execution of `func` max `retry_count` times
	:param delay: waiting time in seconds between two calls of `func`
	:returns: return value of `func`
	"""
	for i in range(retry_count + 1):
		try:
			return func()
		except exceptions:
			exc_info = sys.exc_info()
			if i != retry_count:
				print('Exception occurred: %s (%s). Retrying in %.2f seconds (retry %d/%d).' % (exc_info[0], exc_info[1], delay, i, retry_count))
				time.sleep(delay)
			else:
				print('Exception occurred: %s (%s). This was the last retry (retry %d/%d).' % (exc_info[0], exc_info[1], i, retry_count))
		else:
			break
	else:
		six.reraise(*exc_info)


def verify_ldap_object(baseDn, expected_attr=None, strict=True, should_exist=True, retry_count=20, delay=10):
	# type: (str, Optional[Dict[str, str]], bool, bool, int, float) -> None
	ucr = UCR
	ucr.load()
	retry_count = int(ucr.get("tests/verify_ldap_object/retry_count", retry_count))
	delay = int(ucr.get("tests/verify_ldap_object/delay", delay))

	return retry_on_error(
		functools.partial(__verify_ldap_object, baseDn, expected_attr, strict, should_exist),
		(LDAPUnexpectedObjectFound, LDAPObjectNotFound, LDAPObjectValueMissing),
		retry_count,
		delay)


def __verify_ldap_object(baseDn, expected_attr=None, strict=True, should_exist=True):
	# type: (str, Optional[Dict[str, str]], bool, bool) -> None
	if expected_attr is None:
		expected_attr = {}
	try:
		dn, attr = get_ldap_connection().search(
			filter='(objectClass=*)',
			base=baseDn,
			scope=ldap.SCOPE_BASE,
			attr=expected_attr.keys()
		)[0]
	except (ldap.NO_SUCH_OBJECT, IndexError):
		if should_exist:
			raise LDAPObjectNotFound('DN: %s' % baseDn)
		return

	if not should_exist:
		raise LDAPUnexpectedObjectFound('DN: %s' % baseDn)

	values_missing = {}
	unexpected_values = {}
	for attribute, expected_values_ in expected_attr.items():
		found_values = set(attr.get(attribute, []))
		expected_values = set(x if isinstance(x, bytes) else x.encode('UTF-8') for x in expected_values_)

		difference = expected_values - found_values
		if difference:
			values_missing[attribute] = difference

		if strict:
			difference = found_values - expected_values
			if difference:
				unexpected_values[attribute] = difference

	msg = u'DN: %s\n%s\n%s' % (
		baseDn,
		u'\n'.join(
			u"%s: %r, missing   : '%s'" % (
				attribute,
				attr.get(attribute),
				u"', ".join(x.decode('UTF-8', 'replace') for x in difference)
			) for attribute, difference in values_missing.items()),
		u'\n'.join(
			u"%s: %r, unexpected: '%s'" % (
				attribute,
				attr.get(attribute),
				u"', ".join(x.decode('UTF-8', 'replace') for x in difference)
			) for attribute, difference in unexpected_values.items()),
	)

	if values_missing:
		raise LDAPObjectValueMissing(msg)
	if unexpected_values:
		raise LDAPObjectUnexpectedValue(msg)


def s4connector_present():
	# type: () -> bool
	ucr = ConfigRegistry()
	ucr.load()

	if ucr.is_true('directory/manager/samba3/legacy', False):
		return False
	if ucr.is_false('directory/manager/samba3/legacy', False):
		return True

	for dn, attr in get_ldap_connection().search(
		filter='(&(|(objectClass=univentionDomainController)(objectClass=univentionMemberServer))(univentionService=S4 Connector))',
		attr=['aRecord']
	):
		if 'aRecord' in attr:
			return True
	return False


def stop_s4connector():
	# type: () -> None
	subprocess.call((S4CONNECTOR_INIT_SCRIPT, 'stop'))


def start_s4connector():
	# type: () -> None
	subprocess.call((S4CONNECTOR_INIT_SCRIPT, 'start'))


def restart_s4connector():
	# type: () -> None
	stop_s4connector()
	start_s4connector()


def stop_slapd():
	# type: () -> None
	subprocess.call((SLAPD_INIT_SCRIPT, 'stop'))


def start_slapd():
	# type: () -> None
	subprocess.call((SLAPD_INIT_SCRIPT, 'start'))


def restart_slapd():
	# type: () -> None
	subprocess.call((SLAPD_INIT_SCRIPT, 'restart'))


def stop_listener():
	# type: () -> None
	subprocess.call(('systemctl', 'stop', 'univention-directory-listener'))


def start_listener():
	# type: () -> None
	subprocess.call(('systemctl', 'start', 'univention-directory-listener'))


def restart_listener():
	# type: () -> None
	subprocess.call(('systemctl', 'restart', 'univention-directory-listener'))


def restart_firewall():
	# type: () -> None
	subprocess.call((FIREWALL_INIT_SCRIPT, 'restart'))


class AutomaticListenerRestart(object):
	"""
	Automatically restart Univention Directory Listener when leaving the "with" block::

	    with AutomaticListenerRestart() as alr:
	        with ucr_test.UCSTestConfigRegistry() as ucr:
	            # set some ucr variables, that influence the Univention Directory Listener
	            univention.config_registry.handler_set(['foo/bar=ding/dong'])
	"""

	def __enter__(self):
		# type: () -> AutomaticListenerRestart
		return self

	def __exit__(self, exc_type, exc_value, traceback):
		# type: (Optional[Type[BaseException]], Optional[BaseException], Optional[TracebackType]) -> None
		restart_listener()


class AutoCallCommand(object):

	"""
	Automatically call the given commands when entering/leaving the "with" block.
	The keyword arguments enter_cmd and exit_cmd are optional::

	    with AutoCallCommand(
	            enter_cmd=['/etc/init.d/dovecot', 'reload'],
	            exit_cmd=['/etc/init.d/dovecot', 'restart']) as acc:
	        with ucr_test.UCSTestConfigRegistry() as ucr:
	            # set some ucr variables, that influence the Univention Directory Listener
	            univention.config_registry.handler_set(['foo/bar=ding/dong'])

	In case some filedescriptors for stdout/stderr have to be passed to the executed
	command, they may be passed as kwarg::

	    with AutoCallCommand(
	            enter_cmd=['/etc/init.d/dovecot', 'reload'],
	            exit_cmd=['/etc/init.d/dovecot', 'restart'],
	            stderr=open('/dev/zero', 'w')) as acc:
	        pass
	"""

	def __init__(self, enter_cmd=None, exit_cmd=None, stdout=None, stderr=None):
		# type: (Optional[Sequence[str]], Optional[Sequence[str]], IO[str], IO[str]) -> None
		self.enter_cmd = None
		if type(enter_cmd) in (list, tuple):
			self.enter_cmd = enter_cmd
		self.exit_cmd = None
		if type(exit_cmd) in (list, tuple):
			self.exit_cmd = exit_cmd
		self.pipe_stdout = stdout
		self.pipe_stderr = stderr

	def __enter__(self):
		# type: () -> AutoCallCommand
		if self.enter_cmd:
			subprocess.call(self.enter_cmd, stdout=self.pipe_stdout, stderr=self.pipe_stderr)
		return self

	def __exit__(self, exc_type, exc_value, traceback):
		# type: (Optional[Type[BaseException]], Optional[BaseException], Optional[TracebackType]) -> None
		if self.exit_cmd:
			subprocess.call(self.exit_cmd, stdout=self.pipe_stdout, stderr=self.pipe_stderr)


class FollowLogfile(object):

	"""
	Prints the contents of the listed files on exit of the with block if
	an exception occurred.
	Set always=True to also print them without exception.
	You may wish to make the server flush its logs before existing the
	with block. Use AutoCallCommand inside the block for that::

	    with FollowLogfile(logfiles=['/var/log/syslog', '/var/log/mail.log']) as flf:
	        with utils.AutoCallCommand(enter_cmd=['doveadm', 'log', 'reopen'],
	            exit_cmd=['doveadm', 'log', 'reopen']) as acc:
	            pass

	    with FollowLogfile(logfiles=['/var/log/syslog'], always=True) as flf:
	        with utils.AutoCallCommand(enter_cmd=['doveadm', 'log', 'reopen'],
	            exit_cmd=['doveadm', 'log', 'reopen']) as acc:
	            pass
	"""

	def __init__(self, logfiles, always=False):
		# type: (List[str], bool) -> None
		"""
		:param logfiles: list of absolute filenames to read from
		:param always: bool, if True: print logfile change also if no error occurred (default=False)
		"""
		assert isinstance(logfiles, list)
		self.logfiles = logfiles
		assert isinstance(always, bool)
		self.always = always
		self.logfile_pos = dict()  # type: Dict[str, int]

	def __enter__(self):
		# type: () -> FollowLogfile
		for logfile in self.logfiles:
			with open(logfile, "rb") as log:
				log.seek(0, 2)
				self.logfile_pos[logfile] = log.tell()
		return self

	def __exit__(self, exc_type, exc_value, traceback):
		# type: (Optional[Type[BaseException]], Optional[BaseException], Optional[TracebackType]) -> None
		if self.always or exc_type:
			for logfile, pos in self.logfile_pos.items():
				with open(logfile, "r") as log:
					log.seek(pos, 0)
					lim = (79 - len(logfile) - 2) / 2
					lin = "{0} {1} {0}".format("=" * lim, logfile)
					print(lin + "=" * (79 - len(lin)))
					sys.stdout.writelines(log)
					print("=" * 79)


class ReplicationType(IntEnum):
	LISTENER = 1
	POSTRUN = 2
	S4C_FROM_UCS = 3
	S4C_TO_UCS = 4
	DRS = 5


def wait_for_replication_from_master_openldap_to_local_samba(replication_postrun=False, ldap_filter=None, verbose=True):
	# type: (bool, Optional[str], bool) -> None
	"""Wait for all kind of replications"""
	# the order matters!
	conditions = [(ReplicationType.LISTENER, 'postrun' if replication_postrun else True)]  # type: List[Tuple[ReplicationType, Any]]
	ucr = UCR
	ucr.load()
	if ucr.get('samba4/ldap/base'):
		conditions.append((ReplicationType.S4C_FROM_UCS, ldap_filter))
	if ucr.get('server/role') in ('domaincontroller_backup', 'domaincontroller_slave'):
		conditions.append((ReplicationType.DRS, ldap_filter))
	wait_for(conditions, verbose=True)


def wait_for_replication_from_local_samba_to_local_openldap(replication_postrun=False, ldap_filter=None, verbose=True):
	# type: (bool, Optional[str], bool) -> None
	"""Wait for all kind of replications"""
	conditions = []
	# the order matters!
	ucr = UCR
	ucr.load()
	if ucr.get('server/role') in ('domaincontroller_backup', 'domaincontroller_slave'):
		conditions.append((ReplicationType.DRS, ldap_filter))
	if ucr.get('samba4/ldap/base'):
		conditions.append((ReplicationType.S4C_FROM_UCS, ldap_filter))
	if replication_postrun:
		conditions.append((ReplicationType.LISTENER, 'postrun'))
	else:
		conditions.append((ReplicationType.LISTENER, None))
	wait_for(conditions, verbose=True)


def wait_for(conditions=None, verbose=True):
	# type: (Optional[List[Tuple[ReplicationType, Any]]], bool) -> None
	"""Wait for all kind of replications"""
	for replicationtype, detail in conditions or []:
		if replicationtype == ReplicationType.LISTENER:
			if detail == 'postrun':
				wait_for_listener_replication_and_postrun(verbose)
			else:
				wait_for_listener_replication(verbose)
		elif replicationtype == ReplicationType.S4C_FROM_UCS:
			wait_for_s4connector_replication(verbose)
			if detail:
				# TODO: search in Samba/AD with filter=detail
				pass
		elif replicationtype == ReplicationType.S4C_TO_UCS:
			wait_for_s4connector_replication(verbose)
			if detail:
				# TODO: search in OpenLDAP with filter=detail
				pass
		elif replicationtype == ReplicationType.DRS:
			from univention.testing.ucs_samba import wait_for_drs_replication
			if not isinstance(detail, dict):
				detail = {'ldap_filter': detail}
			wait_for_drs_replication(verbose=verbose, **detail)


def wait_for_listener_replication(verbose=True):
	# type: (bool) -> None
	sys.stdout.flush()
	time.sleep(1)  # Give the notifier some time to increase its transaction id
	if verbose:
		print('Waiting for replication...')
	for _ in range(300):
		# The "-c 1" option ensures listener and notifier id are equal.
		# Otherwise the check is successful as long as the listener id changed since the last check.
		cmd = ('/usr/lib/nagios/plugins/check_univention_replication', '-c', '1')
		proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
		stdout, _stderr = proc.communicate()
		if proc.returncode == 0:
			if verbose:
				print('Done: replication complete.')
			return
		print('.', end=' ')
		time.sleep(1)

	print('Error: replication incomplete.')
	raise LDAPReplicationFailed()


def get_lid():
	# type: () -> int
	"""
	get_lid() returns the last processed notifier ID of univention-directory-listener.
	"""
	with open("/var/lib/univention-directory-listener/notifier_id", "r") as notifier_id:
		return int(notifier_id.readline())


def wait_for_listener_replication_and_postrun(verbose=True):
	# type: (bool) -> None
	# Postrun function in listener modules are called after 15 seconds without any events
	wait_for_listener_replication(verbose=verbose)
	if verbose:
		print("Waiting for postrun...")
	lid = get_lid()
	seconds_since_last_change = 0
	for _ in range(300):
		time.sleep(1)
		print('.', end=' ')
		if lid == get_lid():
			seconds_since_last_change += 1
		else:
			seconds_since_last_change = 0
		if seconds_since_last_change > 12:
			# Less than 15 sec because a postrun function can potentially make ldap changes,
			# which would result in a loop here.
			time.sleep(10)  # Give the postrun function some time
			if verbose:
				print("Postrun should have run")
			return
		lid = get_lid()
	print("Postrun was probably never called in the last 300 seconds")
	raise LDAPReplicationFailed


def wait_for_s4connector_replication(verbose=True):
	# type: (bool) -> None
	if verbose:
		print('Waiting for connector replication')
	import univention.testing.ucs_samba
	try:
		univention.testing.ucs_samba.wait_for_s4connector(17)
	except OSError as exc:  # nagios not installed
		if verbose:
			print('Nagios not installed: %s' % (exc,), file=sys.stderr)
		time.sleep(16)
	except univention.testing.ucs_samba.WaitForS4ConnectorTimeout:
		if verbose:
			print('Warning: S4 Connector replication was not finished after 17 seconds', file=sys.stderr)


# backwards compatibility
wait_for_replication = wait_for_listener_replication
wait_for_replication_and_postrun = wait_for_listener_replication_and_postrun
wait_for_connector_replication = wait_for_s4connector_replication


def package_installed(package):
	# type: (str) -> bool
	sys.stdout.flush()
	with open('/dev/null', 'w') as null:
		return (subprocess.call("dpkg-query -W -f '${Status}' %s | grep -q ^install" % package, stderr=null, shell=True) == 0)


def fail(log_message=None, returncode=1):
	# type: (Optional[str], int) -> NoReturn
	print('### FAIL ###')
	if log_message:
		print('%s\n###      ###' % log_message)
		if sys.exc_info()[-1]:
			print(traceback.format_exc(), file=sys.stderr)
	sys.exit(returncode)


def uppercase_in_ldap_base():
	# type: () -> bool
	ucr = ConfigRegistry()
	ucr.load()
	return not ucr.get('ldap/base').islower()


def is_udp_port_open(port, ip=None):
	# type: (int, Optional[str]) -> bool
	if ip is None:
		ip = '127.0.0.1'
	try:
		udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		udp_sock.connect((ip, int(port)))
		os.write(udp_sock.fileno(), 'X')
		os.write(udp_sock.fileno(), 'X')
		os.write(udp_sock.fileno(), 'X')
		return True
	except OSError as ex:
		print('is_udp_port_open({0}) failed: {1}'.format(port, ex))
	return False


def is_port_open(port, hosts=None, timeout=60):
	# type: (int, Optional[Iterable[str]], int) -> bool
	'''
	check if port is open, if host == None check
	hostname and 127.0.0.1

	:param int port: TCP port number
	:param hosts: list of hostnames or localhost if hosts is None.
	:type hosts: list[str] or None
	:return: True if at least on host is reachable, False otherwise.
	:rtype: boolean
	'''
	if hosts is None:
		hosts = (socket.gethostname(), '127.0.0.1', '::1')
	for host in hosts:
		address = (host, int(port))
		try:
			connection = socket.create_connection(address, timeout)
			connection.close()
			return True
		except EnvironmentError as ex:
			print('is_port_open({0}) failed: {1}'.format(port, ex))
	return False


if __name__ == '__main__':
	import doctest
	doctest.testmod()

# vim: set fileencoding=utf-8 ft=python sw=4 ts=4 :
