#!/usr/share/ucs-test/runner python
## desc: Test delayed creation of new mailboxes via cyrus-imapd restart
## tags: [mail]
## bugs: [32099]
## roles: [domaincontroller_master,domaincontroller_backup,domaincontroller_slave]
## exposure: dangerous
## packages:
##   - univention-mail-server
##   - univention-mail-cyrus


import os
import sys
import subprocess
import univention.testing.utils as utils
import univention.testing.udm as udm_test
import univention.testing.strings as ut_strings


def check_mailbox(localpart, domain):
	dirname = '/var/spool/cyrus/mail/domain/%s/%s/%s/user/%s' % (domain[0], domain, localpart[0], localpart)
	return os.path.isdir(dirname)


def main():
	# perform check with stop/start and restart
	for initargs in [['stop', 'start'], ['restart']]:

		# find non-existing mailbox
		ok = False
		while not ok:
			localpart = ut_strings.random_name(length=15)
			domain = '%s.local' % ut_strings.random_name(length=15)
			ok = not check_mailbox(localpart, domain)
			address ='%s@%s' % (localpart, domain, )

		# create trigger file
		print 'Creating trigger file for address %s' % address
		triggerfn = '/var/spool/cyrus/jobs/mailbox/create/user/%s' % address
		fd = open(triggerfn,'w')
		fd.close()

		# run test against locally install cyrus version (2.2 vs. 2.4)
		try:
			for script in ('/etc/init.d/cyrus-imapd', '/etc/init.d/cyrus2.2'):
				if os.path.exists(script):
					# call init script with given arguments
					for initarg in initargs:
						print 'Calling /etc/init.d/%s %s' % (os.path.basename(script), initarg)
						subprocess.call(['/usr/sbin/invoke-rc.d', os.path.basename(script), initarg], shell=False)
					# check if mailbox has been created in filesystem
					if not check_mailbox(localpart, domain):
						utils.fail('Failed to create mailbox for address %s' % address)
					else:
						print 'SUCCESS: Found mailbox for address %s in filesystem' % address
						subprocess.call(['/usr/sbin/univention-cyrus-mailbox-delete', '--user', address], shell=False)
					break
			else:
				utils.fail('Cannot find init.d script for cyrus imapd')
		finally:
			# cleanup
			if os.path.exists(triggerfn):
				os.unlink(triggerfn)

if __name__ == '__main__':
	main()
