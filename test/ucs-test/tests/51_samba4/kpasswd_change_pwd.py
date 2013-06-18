#!/usr/bin/python 
# -*- coding: utf-8 -*
import pexpect
import sys
import univention.config_registry
from optparse import OptionParser

if __name__ == "__main__":
	parser = OptionParser()
	parser.add_option("-u", "--username", dest="username")
	parser.add_option("-p", "--password", dest="password")
	parser.add_option("-n", "--newpassword", dest="newpassword")
	(optionen, args) = parser.parse_args()
	username=optionen.username
	password=optionen.password
	newpassword=optionen.newpassword

	ucr = univention.config_registry.ConfigRegistry()
	ucr.load()

	kpasswd = pexpect.spawn('kpasswd', [username], timeout=20) # logfile=sys.stdout
	status = kpasswd.expect([pexpect.TIMEOUT, "%s@%s's Password: " % (username, ucr['kerberos/realm']),])
	if status == 0: # timeout
		print 'kpasswd behaved unexpectedly! Output:\n\t%r' % (kpasswd.before,)
		sys.exit(120)
	assert (status == 1), "password prompt"
	kpasswd.sendline(password)
	status = kpasswd.expect([pexpect.TIMEOUT, 'New password for %s@%s:' % (username, ucr['kerberos/realm']), "kpasswd: krb5_get_init_creds: Preauthentication failed", ])
	if status == 0: # timeout
		print 'kpasswd behaved unexpectedly! Output:\n\t%r' % (kpasswd.before,)
		sys.exit(120)
	elif status == 2: # timeout
		print 'Preauthentication failed!'
		sys.exit(120)
	kpasswd.sendline(newpassword)
	status = kpasswd.expect([pexpect.TIMEOUT, 'Verify password - New password for %s@%s:' % (username, ucr['kerberos/realm']),])
	kpasswd.sendline(newpassword)
	status = kpasswd.expect(['Success : Password changed', pexpect.TIMEOUT,])
	if status != 0:
		sys.exit(1)
	else:
		print 'Password changed for %s to %s' % (username, newpassword)
