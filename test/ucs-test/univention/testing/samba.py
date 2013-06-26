import os
import sys
import univention.config_registry
import subprocess
from samba.auth import system_session
from samba.samdb import SamDB
from samba.param import LoadParm
import ldb
import time
import socket

def wait_for_drs_replication(ldap_filter, attrs=None, base=None, scope=ldb.SCOPE_SUBTREE, lp=None, timeout=360, delta_t=1):
	if not lp:
		lp = LoadParm()
		lp.load('/etc/samba/smb.conf')
	if not attrs:
		attrs = ['dn']
	elif type(attrs) != type([]):
		attrs = [attrs]

	samdb = SamDB("tdb://%s" % lp.private_path("sam.ldb"), session_info=system_session(lp), lp=lp)
	controls=["domain_scope:0"]

	print "Waiting for DRS replication, filter: '%s'" % (ldap_filter, ),
	t = t0 = time.time()
	while t < t0 + timeout:
		try:
			res = samdb.search(base=samdb.domain_dn(), scope=scope, expression=ldap_filter, attrs=attrs, controls=controls)
		except ldb.LdbError, (num, msg):
			print "Error during samdb.search: %s" % (msg, )

		if res:
			break

		print '.',
		time.sleep(delta_t)
		t = time.time()

	print "\nDRS replication took %d seconds" % (t-t0, )
	return res

def force_drs_replication(source_dc, partition_dn):
	hostname = socket.gethostname()
	p = subprocess.Popen(["/usr/bin/samba-tool", "drs", "replicate", hostname, source_dc, partition_dn])	
	return p.wait()

