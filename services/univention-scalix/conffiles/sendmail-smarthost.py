# -*- coding: utf-8 -*-
#
# Univention Baseconfig
#  set relay host / smarthost in sendmail cfg
#
# Copyright (C) 2007 Univention GmbH
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

import os

mcfile = '/etc/mail/sendmail.mc'
cffile = '/etc/mail/sendmail.cf'

def handler(baseConfig, changes):
	strA = "define(`SMART_HOST',`"
	strAfull = "define(`SMART_HOST',`%s')dnl"
	strB = "define(`confAUTH_MECHANISMS', `EXTERNAL GSSAPI DIGEST-MD5 CRAM-MD5 LOGIN PLAIN')dnl"
	strC = "FEATURE(`authinfo', `hash /etc/mail/auth/client-info')dnl"

	relayhost = ""
	if baseConfig.has_key('mail/sendmail/relayhost'):
		relayhost = baseConfig['mail/sendmail/relayhost']

	relayauth = False
	if baseConfig.has_key('mail/sendmail/relayauth') and baseConfig['mail/sendmail/relayauth'] in ['yes', 'true']:
		relayauth = True

	fh=open(mcfile, 'r')
	lines = fh.read().splitlines()
	fh.close()

	changed = False
	foundHost = False
	foundAuth = False

	for idx in range(len(lines)):
		pos = lines[idx].find(strA)
		if (pos == 0):
			lines[idx] = strAfull % relayhost
			changed = True
			foundHost = True

		for key in [ strB, strC ]:
			pos = lines[idx].find(key)
			if (pos == 0) or (pos == 4):
				# found?
				if lines[idx][0:4]=='dnl ' or pos == 0:
					foundAuth = True

				if relayauth and pos == 4 and lines[idx][0:4] == 'dnl ':
					lines[idx] = lines[idx][4:]
					changed = True

				if not relayauth and pos == 0:
					lines[idx] = 'dnl ' + lines[idx]
					changed = True

	if not foundHost:
		for i in range(len(lines)):
			if lines[i][0:18] == 'MAILER_DEFINITIONS':
				lines.insert(i,'')
				lines.insert(i,strAfull % relayhost)
				lines.insert(i,'')
				changed = True
				break
		else:
			lines.append('')
			lines.append(strAfull % relayhost)
			lines.append('')
			changed = True

	if relayauth and not foundAuth:
		for i in range(len(lines)):
			if lines[i][0:18] == 'MAILER_DEFINITIONS':
				lines.insert(i,'')
				lines.insert(i,strB)
				lines.insert(i,strC)
				lines.insert(i,'')
				changed = True
				break
		else:
			lines.append('')
			lines.append(strB)
			lines.append(strC)
			lines.append('')
			changed = True


	if changed:
		fh=open(mcfile, 'w')
		fh.write( '\n'.join(lines) )
		fh.close()

		os.system('m4 %s > %s' % (mcfile, cffile))
		os.system('PATH=$PATH:/opt/scalix/bin/ omsendin')
