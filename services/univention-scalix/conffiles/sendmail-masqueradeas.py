# -*- coding: utf-8 -*-
#
# Univention Baseconfig
#  set MASQUERADEAS in sendmail.cf
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

import os, re

mcfile = '/etc/mail/sendmail.mc'
cffile = '/etc/mail/sendmail.cf'

def handler(baseConfig, changes):
	patMasqueradeAs = re.compile("MASQUERADE_AS\(`[^']*'\)dnl")

	fh=open(mcfile, 'r')
	lines = fh.read().splitlines()
	fh.close()

	sendmail_masqueradeas = False
	if baseConfig.get('mail/sendmail/masqueradeas', '__DISABLED__') != '__DISABLED__' :
		strMasqueradeAs = "MASQUERADE_AS(`%s')dnl" % baseConfig['mail/sendmail/masqueradeas']
		sendmail_masqueradeas = True

	changed = False
	strMasqueradeAs_found = False
	mailer_index = 0

	for idx in range(len(lines)):
		if patMasqueradeAs.match(lines[idx]):
			match_idx=idx
			strMasqueradeAs_found = True

	if strMasqueradeAs_found:
		lines.remove(lines[match_idx])
		changed = True

	for idx in range(len(lines)):
		# save the index of the first mailer entry
		if mailer_index == 0 and lines[idx].startswith('MAILER'):
			mailer_index = idx
			break

	if sendmail_masqueradeas and mailer_index > 0:
		lines.insert(mailer_index,strMasqueradeAs)
		changed = True
		#
	if changed:
		fh=open(mcfile, 'w')
		fh.write( '\n'.join(lines) + '\n')
		fh.close()

		os.system('m4 %s > %s' % (mcfile, cffile))
		os.system('/etc/init.d/sendmail restart')
