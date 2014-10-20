import univention.config_registry
import subprocess
from samba.auth import system_session
from samba.samdb import SamDB
from samba.param import LoadParm
import ldb
import time
import socket
import re
import os


def wait_for_drs_replication(ldap_filter, attrs=None, base=None, scope=ldb.SCOPE_SUBTREE, lp=None, timeout=360, delta_t=1):
	if not lp:
		lp = LoadParm()
		lp.load('/etc/samba/smb.conf')
	if not attrs:
		attrs = ['dn']
	elif type(attrs) != type([]):
		attrs = [attrs]

	if not lp.get("server role") == "active directory domain controller":
		print "No Samba4 DC, no need to wait for DRS replication"
		return

	samdb = SamDB("tdb://%s" % lp.private_path("sam.ldb"), session_info=system_session(lp), lp=lp)
	controls = ["domain_scope:0"]

	print "Waiting for DRS replication, filter: '%s'" % (ldap_filter, ),
	t = t0 = time.time()
	while t < t0 + timeout:
		try:
			res = samdb.search(base=samdb.domain_dn(), scope=scope, expression=ldap_filter, attrs=attrs, controls=controls)
			if res:
				print "\nDRS replication took %d seconds" % (t-t0, )
				return res
		except ldb.LdbError, (_num, msg):
			print "Error during samdb.search: %s" % (msg, )

		print '.',
		time.sleep(delta_t)
		t = time.time()


def force_drs_replication(source_dc=None, destination_dc=None, partition_dn=None, direction="in"):
	if not source_dc:
		cmd = ("/usr/bin/univention-ldapsearch", "-xLLL", "(univentionService=S4 Connector)", "uid")
		p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
		stdout, _stderr = p.communicate()
		if stdout:
			matches = re.compile('^uid: (.*)\$$', re.M).findall(stdout)
			if len(matches) == 1:
				source_dc = matches[0]
		else:
			print "WARNING: Automatic S4 Connector host detection failed"
			return 1

	if not destination_dc:
		destination_dc = socket.gethostname()

	if not partition_dn:
		lp = LoadParm()
		lp.load('/etc/samba/smb.conf')
		samdb = SamDB("tdb://%s" % lp.private_path("sam.ldb"), session_info=system_session(lp), lp=lp)
		partition_dn = str(samdb.domain_dn())
		print "USING partition_dn:", partition_dn

	if direction == "in":
		cmd = ("/usr/bin/samba-tool", "drs", "replicate", destination_dc, source_dc, partition_dn)
	else:
		cmd = ("/usr/bin/samba-tool", "drs", "replicate", source_dc, destination_dc, partition_dn)
	return subprocess.call(cmd)

