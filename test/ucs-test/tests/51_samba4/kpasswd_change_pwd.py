#!/usr/bin/python
# -*- coding: utf-8 -*-
import pexpect
import sys
import univention.config_registry
from optparse import OptionParser

if __name__ == "__main__":
	parser = OptionParser()
	parser.add_option("-u", "--username", dest="username")
	parser.add_option("-p", "--password", dest="password")
	parser.add_option("-n", "--newpassword", dest="newpassword")
	parser.add_option("-a", "--adminname", dest="adminname")
	parser.add_option("-m", "--adminpassword", dest="adminpassword")

	(opts, args) = parser.parse_args()
	if not opts.username or not opts.password or not opts.newpassword:
		parser.print_help()
		sys.exit(1)

	ucr = univention.config_registry.ConfigRegistry()
	ucr.load()

	cmd = 'kpasswd'
	if opts.adminname:
		cmd += ' --admin-principal=%s' % (opts.adminname,)
		authusername = opts.adminname
		authpassword = opts.adminpassword
	else:
		authusername = opts.username
		authpassword = opts.password
	cmd += ' %s' % (opts.username,)

	kpasswd = pexpect.spawn(cmd, timeout=20)  # logfile=sys.stdout
	status = kpasswd.expect([pexpect.TIMEOUT, "%s@%s's Password: " % (authusername, ucr['kerberos/realm']), ])
	if status == 0:  # timeout
		print 'kpasswd behaved unexpectedly! Output:\n\t%r' % (kpasswd.before,)
		sys.exit(120)

	assert (status == 1), "password prompt"

	kpasswd.sendline(authpassword)

	status = kpasswd.expect([pexpect.TIMEOUT, 'New password for %s@%s:' % (opts.username, ucr['kerberos/realm']), "kpasswd: krb5_get_init_creds: Preauthentication failed", ])
	if status == 0:  # timeout
		print 'kpasswd behaved unexpectedly! Output:\n\t%r' % (kpasswd.before,)
		sys.exit(120)
	elif status == 2:  # timeout
		print 'Preauthentication failed!'
		sys.exit(120)
	kpasswd.sendline(opts.newpassword)
	status = kpasswd.expect([pexpect.TIMEOUT, 'Verify password - New password for %s@%s:' % (opts.username, ucr['kerberos/realm']), ])
	kpasswd.sendline(opts.newpassword)
	status = kpasswd.expect(['Success : Password changed', pexpect.TIMEOUT, ])
	if status != 0:
		sys.exit(1)
	else:
		print 'Password changed for %s to %s' % (opts.username, opts.newpassword)
