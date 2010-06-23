# -*- coding: utf-8 -*-
#
# Univention Baseconfig
#  set DOMAIN_NAME in sendmail.cf
#
# Copyright 2008-2010 Univention GmbH
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

import os, re

mcfile = '/etc/mail/sendmail.mc'
cffile = '/etc/mail/sendmail.cf'

def handler(baseConfig, changes):
	patDomain = re.compile("define\(`confDOMAIN_NAME', `[^']*'\)dnl")

	fh=open(mcfile, 'r')
	lines = fh.read().splitlines()
	fh.close()

	sendmail_domain = False
	# mail/sendmail/domain is deprecated (Bug #10371),
	# FEATURE(`use_cw_file') should be used instead (i.e. Cw instead of Dj)
	if baseConfig.has_key('mail/sendmail/domain'):
		strDomain = "define(`confDOMAIN_NAME', `%s')dnl" % baseConfig['mail/sendmail/domain']
		sendmail_domain = True

	changed = False
	strDomain_found = False
	mailer_index = 0

	for idx in range(len(lines)):
		if patDomain.match(lines[idx]):
			match_idx=idx
			strDomain_found = True

	if strDomain_found:
		lines.remove(lines[match_idx])
		changed = True

	for idx in range(len(lines)):
		# save the index of the first mailer entry
		if mailer_index == 0 and lines[idx].startswith('MAILER'):
			mailer_index = idx
			break

	if sendmail_domain and mailer_index > 0:
		lines.insert(mailer_index,strDomain)
		changed = True
		#
	if changed:
		fh=open(mcfile, 'w')
		fh.write( '\n'.join(lines) + '\n')
		fh.close()

		os.system('m4 %s > %s' % (mcfile, cffile))
		os.system('/etc/init.d/sendmail restart')
