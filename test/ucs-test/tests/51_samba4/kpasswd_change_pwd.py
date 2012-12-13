#!/usr/bin/python 
import pexpect
import tempfile
import sys
import atexit
import univention.config_registry
import random
import subprocess
from optparse import OptionParser
ucr = univention.config_registry.ConfigRegistry()
ucr.load()

def create_ssh_session(username, password):
	known_hosts_file = tempfile.NamedTemporaryFile()
	shell = pexpect.spawn('ssh', ['-o', 'UserKnownHostsFile="%s"' % known_hosts_file.name, "%s@localhost" % adminname,], timeout=10) # logfile=sys.stdout
	status = shell.expect([pexpect.TIMEOUT, '[Pp]assword: ', 'Are you sure you want to continue connecting',])
        del known_hosts_file
	if status == 2: # accept public key
		shell.sendline('yes')
		status = shell.expect([pexpect.TIMEOUT, '[Pp]assword: ',])
	if status == 0: # timeout
		raise Exception('ssh behaved unexpectedly! Output:\n\t%r' % (shell.before,))
	assert (status == 1), "password prompt"
	shell.sendline(password)
	status = shell.expect([pexpect.TIMEOUT, '\$ ','Last login',])
	if status == 0: # timeout
		raise Exception('No shell prompt found! Output:\n\t%r' % (shell.before,))
	assert (status == 1 or status ==2), "shell prompt"
	return shell

if __name__ == "__main__":
	parser = OptionParser()
	parser.add_option("-u", "--username", dest="username")
	parser.add_option("-p", "--password", dest="password")
	parser.add_option("-n", "--newpassword", dest="newpassword")
 	parser.add_option("-r", "--adminpassword", dest="adminpassword")
	parser.add_option("-a", "--adminname", dest="adminname")
	(optionen, args) = parser.parse_args()
	username=optionen.username
	password=optionen.password
	newpassword=optionen.newpassword
	adminpassword=optionen.adminpassword
	adminname=optionen.adminname
	try:
		shell = create_ssh_session(adminname, adminpassword)
	except Exception, e:
		print e # print error
		sys.exit(120)

	shell.sendline('kpasswd %s' % username)
	status = shell.expect([pexpect.TIMEOUT, '[Pp]assword:',])
	if status == 0: # timeout
		sys.exit(120)
	shell.sendline(password)
	status = shell.expect([pexpect.TIMEOUT, 'New password:',])
	shell.sendline(newpassword)
	status = shell.expect([pexpect.TIMEOUT, 'New password:',])
	shell.sendline(newpassword)
	status = shell.expect(['(?i)success', '(?i)error', pexpect.TIMEOUT,])
	kpasswd_reported_success = status == 0
	print 'changed password for %s to %s' % (username, newpassword)
	print 'ENDEbefore:%s' % (shell.before,)
	print 'ENDEafter:%s' % (shell.after,)
