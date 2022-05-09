from __future__ import print_function

import contextlib
import re
import socket
import sqlite3
import subprocess
import time
from typing import Any, Dict, Iterator, List, Optional, Union  # noqa: F401

import ldap
import six

import univention.config_registry as config_registry
from univention.testing.utils import package_installed

if not six.PY2:
	import ldb
	from samba.auth import system_session
	from samba.samdb import SamDB
	from samba.param import LoadParm
else:
	class ldb(object):
		LdbError = None
		SCOPE_SUBTREE = 2
		ERR_NO_SUCH_OBJECT = 32
		ERR_INVALID_DN_SYNTAX = 34


class DRSReplicationFailed(Exception):
	pass


class WaitForS4ConnectorTimeout(Exception):
	pass


@contextlib.contextmanager
def password_policy(complexity=False, minimum_password_age=0, maximum_password_age=3):
	# type: (bool, int, int) -> Iterator[None]
	if not package_installed('univention-samba4'):
		print('skipping samba password policy adjustment')
		yield
		return
	min_pwd_age = subprocess.check_output('samba-tool domain passwordsettings show | grep "Minimum password age" | sed s/[^0-9]*/""/', shell=True).strip()
	max_pwd_age = subprocess.check_output('samba-tool domain passwordsettings show | grep "Maximum password age" | sed s/[^0-9]*/""/', shell=True).strip()
	pwd_complexity = subprocess.check_output('samba-tool domain passwordsettings show | grep complexity | sed "s/Password complexity: //"', shell=True).strip()
	if complexity != pwd_complexity or str(minimum_password_age) != min_pwd_age or str(maximum_password_age) != max_pwd_age:
		subprocess.call(['samba-tool', 'domain', 'passwordsettings', 'set', '--min-pwd-age', str(minimum_password_age), '--max-pwd-age', str(maximum_password_age), '--complexity', 'on' if complexity else 'off'])
	yield
	if complexity != pwd_complexity or str(minimum_password_age) != min_pwd_age:
		subprocess.call(['samba-tool', 'domain', 'passwordsettings', 'set', '--min-pwd-age', min_pwd_age, '--max-pwd-age', max_pwd_age, '--complexity', pwd_complexity])


def wait_for_drs_replication(*args, **kwargs):
	# type: (*Any, **Any) -> None
	if six.PY2:
		process = subprocess.Popen(['/usr/bin/python3', '-'], stdin=subprocess.PIPE)
		stdout, stderr = process.communicate(b'''
import ldb
import sys
from univention.testing.ucs_samba import wait_for_drs_replication, DRSReplicationFailed
try:
	wait_for_drs_replication(*%s, **%s)
except DRSReplicationFailed as exc:
	print(repr(exc), file=sys.stderr)
	sys.exit(2)
except ldb.LdbError as exc:
	print(repr(exc), file=sys.stderr)
	sys.exit(3)
		''' % (repr(args).encode('UTF-8'), repr(kwargs).encode('UTF-8')))
		if process.returncode == 2:
			raise DRSReplicationFailed((stderr or b'').decode('UTF-8', 'replace'))
		elif process.returncode:
			raise Exception((stderr or b'').decode('UTF-8', 'replace'))
		return
	return _wait_for_drs_replication(*args, **kwargs)


def _wait_for_drs_replication(ldap_filter, attrs=None, base=None, scope=ldb.SCOPE_SUBTREE, lp=None, timeout=360, delta_t=1, verbose=True, should_exist=True, controls=None):
	# type: (str, Union[List[str], None, str], Optional[str], int, Optional[LoadParm], int, int, bool, bool, Optional[List[str]]) -> None
	if not package_installed('univention-samba4'):
		if package_installed('univention-samba'):
			time.sleep(15)
			print('Sleeping 15 seconds as a workaround for http://forge.univention.org/bugzilla/show_bug.cgi?id=52145')
		elif verbose:
			print('wait_for_drs_replication(): skip, univention-samba4 not installed.')
		return
	if not attrs:
		attrs = ['dn']
	elif not isinstance(attrs, list):
		attrs = [attrs]

	if not lp:
		lp = LoadParm()
		lp.load('/etc/samba/smb.conf')
	samdb = SamDB("tdb://%s" % lp.private_path("sam.ldb"), session_info=system_session(lp), lp=lp)
	if not controls:
		controls = ["domain_scope:0"]
	if base is None:
		ucr = config_registry.ConfigRegistry()
		ucr.load()
		base = ucr['samba4/ldap/base']
	else:
		if len(ldap.dn.str2dn(base)[0]) > 1:
			if verbose:
				print('wait_for_drs_replication(): skip, multiple RDNs are not supported')
			return
	if not base:
		if verbose:
			print('wait_for_drs_replication(): skip, no samba domain found')
		return

	if verbose:
		print("Waiting for DRS replication, filter: %r, base: %r, scope: %r, should_exist: %r" % (ldap_filter, base, scope, should_exist), end=' ')
	t = t0 = time.time()
	while t < t0 + timeout:
		try:
			res = samdb.search(base=base, scope=scope, expression=ldap_filter, attrs=attrs, controls=controls)
			if bool(res) is bool(should_exist):
				if verbose:
					print("\nDRS replication took %d seconds" % (t - t0, ))
				return  # res
		except ldb.LdbError as exc:
			(_num, msg) = exc.args
			if _num == ldb.ERR_INVALID_DN_SYNTAX:
				raise
			if _num == ldb.ERR_NO_SUCH_OBJECT and not should_exist:
				if verbose:
					print("\nDRS replication took %d seconds" % (t - t0, ))
				return
			print("Error during samdb.search: %s" % (msg, ))

		print('.', end=' ')
		time.sleep(delta_t)
		t = time.time()
	raise DRSReplicationFailed("DRS replication for filter: %r failed due to timeout after %d sec." % (ldap_filter, t - t0))


def get_available_s4connector_dc():
	# type: () -> str
	cmd = ("/usr/bin/univention-ldapsearch", "-LLL", "(univentionService=S4 Connector)", "uid")
	p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
	stdout, _stderr = p.communicate()
	if not stdout:
		print("WARNING: Automatic S4 Connector host detection failed")
		return ""
	matches = re.compile(r'^uid: (.*)\$$', re.M).findall(stdout.decode('utf-8', 'replace'))
	if len(matches) == 1:
		return matches[0]
	elif len(matches) == 0:
		print("WARNING: Automatic S4 Connector host detection failed")
		return ""

	# check if this is UCS@school
	cmd = ("/usr/bin/univention-ldapsearch", "-LLL", "(univentionService=UCS@school)", "dn")
	p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
	stdout, _stderr = p.communicate()
	if not stdout:
		print("ERROR: Automatic S4 Connector host detection failed: Found %s S4 Connector services" % len(matches))
		return ""
	# Look for replicating DCs
	dcs_replicating_with_this_one = []
	for s4c in matches:
		cmd = ("/usr/bin/samba-tool", "drs", "showrepl", s4c)
		p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		stdout, _stderr = p.communicate()
		if p.returncode != 0:
			continue
		dcs_replicating_with_this_one.append(s4c)
	if len(dcs_replicating_with_this_one) == 1:
		return dcs_replicating_with_this_one[0]
	else:
		print("ERROR: Automatic S4 Connector host detection failed: Replicating with %s S4 Connector services" % len(dcs_replicating_with_this_one))
		return ""


def force_drs_replication(source_dc=None, destination_dc=None, partition_dn=None, direction="in"):
	# type: (Optional[str], Optional[str], Optional[str], str) -> int
	if not package_installed('univention-samba4'):
		print('force_drs_replication(): skip, univention-samba4 not installed.')
		return 0

	src = source_dc or get_available_s4connector_dc()
	if not src:
		return 1

	dst = destination_dc or socket.gethostname()
	if src == dst:
		return 0

	if not partition_dn:
		ucr = config_registry.ConfigRegistry()
		ucr.load()
		partition_dn = str(ucr.get('samba4/ldap/base'))
		print("USING partition_dn:", partition_dn)

	cmd = ("/usr/bin/samba-tool", "drs", "replicate", dst, src, partition_dn)
	return subprocess.call(cmd)


def _ldap_replication_complete(verbose=True):
	# type: (bool) -> bool
	kwargs = {}  # type: Dict[str, Any]
	if not verbose:
		kwargs = {'stdout': open('/dev/null', 'w'), 'stderr': subprocess.STDOUT}
	return subprocess.call('/usr/lib/nagios/plugins/check_univention_replication', **kwargs) == 0


def wait_for_s4connector(timeout=360, delta_t=1, s4cooldown_t=5):
	# type: (int, int, int) -> int
	ucr = config_registry.ConfigRegistry()
	ucr.load()

	if not package_installed('univention-s4-connector'):
		print('wait_for_s4connector(): skip, univention-s4-connector not installed.')
		return 0
	if ucr.is_false('connector/s4/autostart'):
		print('wait_for_s4connector(): skip, connector/s4/autostart is set to false.')
		return 0
	conn = sqlite3.connect('/etc/univention/connector/s4internal.sqlite')
	c = conn.cursor()

	static_count = 0

	replication_complete = False
	highestCommittedUSN = -1
	lastUSN = -1
	t = t0 = time.time()
	while t < t0 + timeout:
		time.sleep(delta_t)

		if not _ldap_replication_complete(verbose=False):
			continue
		else:
			if not replication_complete:
				print('Start waiting for S4-Connector replication')
			replication_complete = True

		previous_highestCommittedUSN = highestCommittedUSN
		ldbresult = subprocess.Popen([
			'ldbsearch',
			'--url', '/var/lib/samba/private/sam.ldb',
			'--scope', 'base',
			'--basedn', '',
			'highestCommittedUSN',
		], stdout=subprocess.PIPE)
		assert ldbresult.stdout
		for chunk in ldbresult.stdout:
			line = chunk.decode('utf-8').strip()
			if line.startswith('highestCommittedUSN: '):
				highestCommittedUSN = int(line[len('highestCommittedUSN: '):])
				break
		else:
			raise KeyError('No highestCommittedUSN in ldbsearch')

		previous_lastUSN = lastUSN
		c.execute('select value from S4 where key=="lastUSN"')
		lastUSN = int(c.fetchone()[0])

		if not (lastUSN == highestCommittedUSN and lastUSN == previous_lastUSN and highestCommittedUSN == previous_highestCommittedUSN):
			static_count = 0
			print('Reset counter')
		else:
			static_count += 1

		print('Counter: {}; highestCommittedUSN: {!r}; lastUSN: {!r}'.format(static_count, highestCommittedUSN, lastUSN))

		if static_count * delta_t >= s4cooldown_t:
			return 0
		t = time.time()

	conn.close()
	raise WaitForS4ConnectorTimeout()


def append_dot(verify_list):
	# type: (List[str]) -> List[str]
	"""The S4-Connector appends dots to various dns records. Helper function to adjust a list."""
	if not package_installed('univention-s4-connector'):
		return verify_list
	return ['%s.' % (x,) for x in verify_list]
