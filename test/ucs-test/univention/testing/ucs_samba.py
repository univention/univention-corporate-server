from __future__ import print_function
import subprocess
import time
import socket
import re
import contextlib

import sqlite3
import ldb
import ldap
from samba.auth import system_session
from samba.samdb import SamDB
from samba.param import LoadParm

from univention.testing.utils import package_installed
import univention.config_registry as config_registry


class DRSReplicationFailed(Exception):
	pass


class WaitForS4ConnectorTimeout(Exception):
	pass


@contextlib.contextmanager
def password_policy(complexity=False, minimum_password_age=0, maximum_password_age=3):
	if not package_installed('univention-samba4'):
		print('skipping samba password policy adjustment')
		yield
		return
	complexity = 'on' if complexity else 'off'
	minimum_password_age = str(minimum_password_age)
	maximum_password_age = str(maximum_password_age)
	min_pwd_age = subprocess.check_output('samba-tool domain passwordsettings show | grep "Minimum password age" | sed s/[^0-9]*/""/', shell=True).strip()
	max_pwd_age = subprocess.check_output('samba-tool domain passwordsettings show | grep "Maximum password age" | sed s/[^0-9]*/""/', shell=True).strip()
	pwd_complexity = subprocess.check_output('samba-tool domain passwordsettings show | grep complexity | sed "s/Password complexity: //"', shell=True).strip()
	if complexity != pwd_complexity or minimum_password_age != min_pwd_age or maximum_password_age != max_pwd_age:
		subprocess.call(['samba-tool', 'domain', 'passwordsettings', 'set', '--min-pwd-age', minimum_password_age, '--max-pwd-age', maximum_password_age, '--complexity', complexity])
	yield
	if complexity != pwd_complexity or minimum_password_age != min_pwd_age:
		subprocess.call(['samba-tool', 'domain', 'passwordsettings', 'set', '--min-pwd-age', min_pwd_age, '--max-pwd-age', max_pwd_age, '--complexity', pwd_complexity])


def wait_for_drs_replication(ldap_filter, attrs=None, base=None, scope=ldb.SCOPE_SUBTREE, lp=None, timeout=360, delta_t=1, verbose=True, should_exist=True, controls=None):
	if not package_installed('univention-samba4'):
		if verbose:
			print('wait_for_drs_replication(): skip, univention-samba4 not installed.')
		return
	if not lp:
		lp = LoadParm()
		lp.load('/etc/samba/smb.conf')
	if not attrs:
		attrs = ['dn']
	elif not isinstance(attrs, list):
		attrs = [attrs]

	samdb = SamDB("tdb://%s" % lp.private_path("sam.ldb"), session_info=system_session(lp), lp=lp)
	if not controls:
		controls = ["domain_scope:0"]
	if base is None:
		base = samdb.domain_dn()
	else:
		if len(ldap.dn.str2dn(base)[0]) > 1:
			if verbose:
				print('wait_for_drs_replication(): skip, multiple RDNs are not supported')
			return
	if not base or base == 'None':
		if verbose:
			print('wait_for_drs_replication(): skip, no samba domain found')
		return

	if verbose:
		print("Waiting for DRS replication, filter: %r, base: %r, scope: %r, should_exist: %r" % (ldap_filter, base, scope, should_exist), end=' ')
	t = t0 = time.time()
	while t < t0 + timeout:
		try:
			res = samdb.search(base=base, scope=scope, expression=ldap_filter, attrs=attrs, controls=controls)
			if res and should_exist:
				if verbose:
					print("\nDRS replication took %d seconds" % (t - t0, ))
				return res
			if not res and not should_exist:
				if verbose:
					print("\nDRS replication took %d seconds" % (t - t0, ))
				return res
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
	cmd = ("/usr/bin/univention-ldapsearch", "-LLL", "(univentionService=S4 Connector)", "uid")
	p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
	stdout, _stderr = p.communicate()
	if not stdout:
		print("WARNING: Automatic S4 Connector host detection failed")
		return
	matches = re.compile('^uid: (.*)\$$', re.M).findall(stdout)
	if len(matches) == 1:
		return matches[0]
	elif len(matches) == 0:
		print("WARNING: Automatic S4 Connector host detection failed")
		return

	# check if this is UCS@school
	cmd = ("/usr/bin/univention-ldapsearch", "-LLL", "(univentionService=UCS@school)", "dn")
	p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
	stdout, _stderr = p.communicate()
	if not stdout:
		print("ERROR: Automatic S4 Connector host detection failed: Found %s S4 Connector services" % len(matches))
		return
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
		return


def force_drs_replication(source_dc=None, destination_dc=None, partition_dn=None, direction="in"):
	if not package_installed('univention-samba4'):
		print('force_drs_replication(): skip, univention-samba4 not installed.')
		return
	if not source_dc:
		source_dc = get_available_s4connector_dc()
		if not source_dc:
			return 1

	if not destination_dc:
		destination_dc = socket.gethostname()

	if destination_dc == source_dc:
		return

	if not partition_dn:
		lp = LoadParm()
		lp.load('/etc/samba/smb.conf')
		samdb = SamDB("tdb://%s" % lp.private_path("sam.ldb"), session_info=system_session(lp), lp=lp)
		partition_dn = str(samdb.domain_dn())
		print("USING partition_dn:", partition_dn)

	if direction == "in":
		cmd = ("/usr/bin/samba-tool", "drs", "replicate", destination_dc, source_dc, partition_dn)
	else:
		cmd = ("/usr/bin/samba-tool", "drs", "replicate", source_dc, destination_dc, partition_dn)
	return subprocess.call(cmd)


def _ldap_replication_complete(verbose=True):
	kwargs = {}
	if not verbose:
		kwargs = {'stdout': open('/dev/null', 'w'), 'stderr': subprocess.STDOUT}
	return subprocess.call('/usr/lib/nagios/plugins/check_univention_replication', **kwargs) == 0


def wait_for_s4connector(timeout=360, delta_t=1, s4cooldown_t=10):
	ucr = config_registry.ConfigRegistry()
	ucr.load()

	if not package_installed('univention-s4-connector'):
		print('wait_for_s4connector(): skip, univention-s4-connector not installed.')
		return
	if ucr.is_false('connector/s4/autostart'):
		print('wait_for_s4connector(): skip, connector/s4/autostart is set to false.')
		return
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

		highestCommittedUSN = -1
		ldbresult = subprocess.check_output([
			'ldbsearch',
			'--url', '/var/lib/samba/private/sam.ldb',
			'--scope', 'base',
			'--basedn', '',
			'highestCommittedUSN',
		])
		for line in ldbresult.split('\n'):
			line = line.strip()
			if line.startswith('highestCommittedUSN: '):
				highestCommittedUSN = line.replace('highestCommittedUSN: ', '')
				break
		else:
			raise KeyError('No highestCommittedUSN in ldbsearch')

		previous_lastUSN = lastUSN
		c.execute('select value from S4 where key=="lastUSN"')

		lastUSN = c.fetchone()[0]

		if not (lastUSN == highestCommittedUSN and lastUSN == previous_lastUSN and highestCommittedUSN == previous_highestCommittedUSN):
			static_count = 0
			print('Reset counter')
		else:
			static_count = static_count + 1

		print('Counter: {}; highestCommittedUSN: {}; lastUSN: {}'.format(static_count, highestCommittedUSN, lastUSN))

		if static_count * delta_t >= s4cooldown_t:
			return 0
		t = time.time()

	conn.close()
	raise WaitForS4ConnectorTimeout()


def append_dot(verify_list):
	"""The S4-Connector appends dots to various dns records. Helper function to adjust a list."""
	if not package_installed('univention-s4-connector'):
		return verify_list
	return ['%s.' % (x,) for x in verify_list]
