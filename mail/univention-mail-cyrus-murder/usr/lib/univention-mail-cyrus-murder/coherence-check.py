#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention Mail Cyrus Murder
#  sanity check script: check coherence of HomeServer and backend mailbox
#
# Copyright (C) 2008-2013 Univention GmbH
#
# http://www.univention.de/
#
# All rights reserved.
#
# The source code of this program is made available
# under the terms of the GNU Affero General Public License version 3
# (GNU AGPL V3) as published by the Free Software Foundation.
#
# Binary versions of this program provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention and not subject to the GNU AGPL V3.
#
# In the case you use this program under the terms of the GNU AGPL V3,
# the program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <http://www.gnu.org/licenses/>.

import os
import univention.config_registry
import univention.uldap
import sys
import imaplib
import smtplib

registry = univention.config_registry.ConfigRegistry()
registry.load()

fqdn = '%s.%s' % (registry['hostname'], registry['domainname'])

backend = ""
backendInterface = registry.get('mail/cyrus/murder/backend/interface', "")
if backendInterface:
	backend = registry.get('interfaces/%s/address' % backendInterface, "")

isMurder = False
murders = registry.get('mail/cyrus/murder/servers', "")
if registry['hostname'] + "$" in murders.split(" "):
	isMurder = True

password = ""
if os.path.isfile("/etc/cyrus.secret"):
	password = open('/etc/cyrus.secret').read()
	if password[-1] == '\n':
		password = password[0:-1]

if isMurder and backend and password:
	
	# get list of mbox's that belong to this server
	ldap = univention.uldap.getMachineConnection(ldap_master=False)
	filter = '(&(objectClass=inetOrgPerson)(objectClass=univentionMail)(univentionMailHomeServer=%s))' % fqdn
	results = ldap.search(filter=filter, attr=["mailPrimaryAddress"])
	addrlist = []
	for result in results:
		if len(result) > 1:	
			mail = result[1].get("mailPrimaryAddress", [])
			if mail:
				addrlist.append(mail[0])

	
	# imap login
	try:
		imap = imaplib.IMAP4_SSL(backend)
	except Exception, e:
		sys.stderr.write("imap ssl connect to %s failed\n" % backend)
		sys.exit(1)
	try:
		imap.login("cyrus", password)
	except Exception, e:
		sys.stderr.write("imap login to %s failed\n" % backend)
		sys.exit(1)

	# get list of mbox's from server
	result = imap.list() 
	serverlist = []
	if len(result) > 1:
		for res in result[1]:
			tmp = res.split(" ")
			if len(tmp) > 2:
				serverlist.append(tmp[2].replace("user/", ""))

	# compare list's
	noticelist = []
	for i in addrlist:
		if not i in serverlist:
			noticelist.append(i)

	# report incoherence
	if noticelist:

		emailtext  = "Subject: univentionMailHomeServer incoherence on host %s\n" % fqdn
		emailtext += "Report from cron job univention-mail-cyrus-murder\n"
		emailtext += "running on host %s:\n" % fqdn
		emailtext += "The following list of primary mail addresses were\n"
		emailtext += "not found on the local cyrus backend (%s)\n" % backend
		emailtext += "but these addresses have selected me (the corresponding\n"
		emailtext += "cyrus murder frontend) as univentionMailHomeServer:\n"
		emailtext += "%s\n" % '\n'.join(noticelist)
		emailtext += "Please initiate a manual cyradm rename on this cyrus\n"
		emailtext += "murder frontend to move the user mailbox(es) to\n"
		emailtext += "the local cyrus backend."

		try:
			server = smtplib.SMTP("localhost")
			server.sendmail("root", "root", emailtext)
			server.quit()
		except Exception, e:
			sys.stderr.write("could not send incoherence mail on %s (%s).\n" % (fqdn, emailtext))
			sys.exit(1)

sys.exit(0)
