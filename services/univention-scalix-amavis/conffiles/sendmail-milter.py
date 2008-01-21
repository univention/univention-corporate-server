#
# Univention Baseconfig
#  enable/disable milter in sendmail cfg
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
	strA = "define(`MILTER', 1)dnl"
	strAfull = strA
	strB = "INPUT_MAIL_FILTER(`milter-amavis', `S=local:"
	strBfull = "INPUT_MAIL_FILTER(`milter-amavis', `S=local:/var/lib/amavis/amavisd-milter.sock, F=T, T=S:10m;R:10m;E:10m')dnl"

	addmilter = False
	if baseConfig.has_key('mail/sendmail/milter') and baseConfig['mail/sendmail/milter'].lower() in ['yes', 'true']:
		addmilter = True

	fh=open(mcfile, 'r')
	lines = fh.read().splitlines()
	fh.close()

	changed = False
	found = False

	for idx in range(len(lines)):
		for key in [ strA, strB ]:
			pos = lines[idx].find(key)
			if (pos == 0) or (pos == 1) or (pos == 6):
				# found?
				if lines[idx][0:1]=='#' or lines[idx][0:6]=='dnl # ' or pos == 0:
					found = True

				if addmilter and ( (pos == 1) or (pos == 6) ) and ( (lines[idx][0:1] == '#') or (lines[idx][0:6] == 'dnl # ') ):
					if pos == 6:
						lines[idx] = lines[idx][6:]
					elif pos == 1:
						lines[idx] = lines[idx][1:]
					changed = True

				if not addmilter and pos == 0:
					lines[idx] = 'dnl # ' + lines[idx]
					changed = True

	if addmilter and not changed and not found:
		lines.append('')
		lines.append(strAfull)
		lines.append(strBfull)
		lines.append('')
		changed = True

	if changed:
		fh=open(mcfile, 'w')
		fh.write( '\n'.join(lines) )
		fh.close()

		os.system('m4 %s > %s' % (mcfile, cffile))
		os.system('PATH=$PATH:/opt/scalix/bin/ omsendin')
