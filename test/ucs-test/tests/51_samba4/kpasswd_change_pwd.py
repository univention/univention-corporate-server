#!/usr/bin/python3
# -*- coding: utf-8 -*-

from __future__ import print_function

import sys
from argparse import ArgumentParser

import pexpect

import univention.config_registry

if __name__ == "__main__":
	parser = ArgumentParser()
	parser.add_argument("-u", "--username")
	parser.add_argument("-p", "--password")
	parser.add_argument("-n", "--newpassword")
	parser.add_argument("-a", "--adminname")
	parser.add_argument("-m", "--adminpassword")

	opts = parser.parse_args()
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
	status = kpasswd.expect([pexpect.TIMEOUT, b"%s@%s's Password: " % (authusername.encode('UTF-8'), ucr['kerberos/realm'].encode('ASCII')), ])
	if status == 0:  # timeout
		print('kpasswd behaved unexpectedly! Output:\n\t%r' % (kpasswd.before.decode('UTF-8', 'replace'),))
		sys.exit(120)

	assert (status == 1), "password prompt"

	kpasswd.sendline(authpassword.encode('UTF-8'))

	status = kpasswd.expect([pexpect.TIMEOUT, b'New password for %s@%s:' % (opts.username.encode('UTF-8'), ucr['kerberos/realm'].encode('ASCII')), "kpasswd: krb5_get_init_creds: Preauthentication failed", ])
	if status == 0:  # timeout
		print('kpasswd behaved unexpectedly! Output:\n\t%r' % (kpasswd.before.decode('UTF-8', 'replace'),))
		sys.exit(120)
	elif status == 2:  # timeout
		print('Preauthentication failed!')
		sys.exit(120)
	kpasswd.sendline(opts.newpassword.encode('UTF-8'))
	status = kpasswd.expect([pexpect.TIMEOUT, b'Verify password - New password for %s@%s:' % (opts.username.encode('UTF-8'), ucr['kerberos/realm'].encode('ASCII')), ])
	kpasswd.sendline(opts.newpassword.encode('UTF-8'))
	status = kpasswd.expect([b'Success : Password changed', pexpect.TIMEOUT, ])
	if status != 0:
		sys.exit(1)
	else:
		print('Password changed for %s to %s' % (opts.username, opts.newpassword))
