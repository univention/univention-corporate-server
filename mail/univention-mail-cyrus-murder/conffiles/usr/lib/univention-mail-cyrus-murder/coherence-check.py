# -*- coding: utf-8 -*-
#
# Univention Mail Cyrus Murder
#  sanity check script: check coherence of kolabHomeServer and backend mailbox
#
# Copyright (C) 2008 Univention GmbH
#
# http://www.univention.de/
#
# All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# Binary versions of this file provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import os, string, univention.config_registry, tempfile
from pexpect import *
registry = univention.config_registry.ConfigRegistry()
registry.load()

if registry.has_key('mail/cyrus/murder/backend/id') and registry['mail/cyrus/murder/backend/id']:
	emailId = registry['mail/cyrus/murder/backend/id']
	backend = emailId[:emailId.find('@')]

	fqdn = '%s.%s' % (registry['hostname'], registry['domainname'])
	localList = os.popen("ldapsearch -x '(&(objectClass=kolabinetorgperson)(kolabHomeServer=%s))' mailPrimaryAddress | grep 'mailPrimaryAddress: '" % fqdn)
	
	addrlist = [ entry[entry.find(': ')+2 :].strip() for entry in localList ]

	cyrus_user='cyrus'
	f=open('/etc/cyrus.secret')
	password=f.read().strip()
	f.close()

	noticelist=[]
	child = spawn('/usr/bin/cyradm -u %s %s' % (cyrus_user, backend))
	i=0
	while not i == 3:
		i = child.expect(['IMAP Password:', '>', 'cyradm: cannot connect to server', EOF], timeout=60)
		if i == 0:
			child.sendline(password)
		elif i == 1:
			while len(addrlist) != 0:
				addr=addrlist.pop()
				mbox= 'user/%s' % addr
				child.sendline('listmailbox %s' % mbox)
				j = child.expect(["\r\n%s" % mbox, '>'])
				if j != 0:
					noticelist.append(addr)
				else:
					child.expect(['>'])
			child.sendline('disc')
			child.expect(['>'])
			child.sendline('exit')
		elif i == 2:
			sys.exit(1)

	if noticelist:
		emailtext='Report from cron job univention-mail-cyrus-murder running on host %s:\nThe following list of primary mail addresses were not found on the local cyrus backend (%s)\nbut these addresses have selected me (the corresponding cyrus murder frontend) as kolabHomeServer:\n%s\nPlease initiate a manual cyradm rename on this cyrus murder frontend to move the user mailbox(es) to the local cyrus backend.' % ( fqdn, backend, '\n'.join(noticelist) )
		tempfn=tempfile.mktemp()
		fh=open(tempfn,'w')
		fh.write("%s" % emailtext)
		fh.close()
		p = os.popen("/usr/bin/mail root -s 'kolabHomeServer incoherence on host %s' < %s" % (fqdn,tempfn))
		p.close()
		os.unlink(tempfn)

