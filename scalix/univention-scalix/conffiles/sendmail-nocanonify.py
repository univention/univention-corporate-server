# -*- coding: utf-8 -*-
#
# Univention Baseconfig
#  accept_unresolvable_domains in sendmail.cf
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

import os

mcfile = '/etc/mail/sendmail.mc'
cffile = '/etc/mail/sendmail.cf'

def handler(baseConfig, changes):
	strNocanonify = "FEATURE(`nocanonify')dnl"
	strUnresolvable = "FEATURE(`accept_unresolvable_domains')dnl"
	strSwitch = "define(`confSERVICE_SWITCH_FILE', `/etc/mail/service.switch')dnl"
	strHosts = "define(`confHOSTS_FILE', `/etc/hosts')dnl"

	fh=open(mcfile, 'r')
	lines = fh.read().splitlines()
	fh.close()

	nocanonify = False
	if baseConfig.has_key('mail/sendmail/nocanonify') and baseConfig['mail/sendmail/nocanonify'] in ['yes', 'true']:
		nocanonify = True

	changed = False
	mailer_index = 0

	strNocanonify_found = False
	strUnresolvable_found = False
	strSwitch_found = False
	strHosts_found = False

	for idx in range(len(lines)):
		if lines[idx].startswith(strNocanonify):
			if not nocanonify:
				lines.remove(lines[idx])
				changed = True
				break
			else:
				strNocanonify_found = True

	for idx in range(len(lines)):
		if lines[idx].startswith(strUnresolvable):
			if not nocanonify:
				lines.remove(lines[idx])
				changed = True
				break
			else:
				strUnresolvable_found = True

	for idx in range(len(lines)):
		if lines[idx].startswith(strSwitch):
			if not nocanonify:
				lines.remove(lines[idx])
				changed = True
				break
			else:
				strSwitch_found = True

	for idx in range(len(lines)):
		if lines[idx].startswith(strHosts):
			if not nocanonify:
				lines.remove(lines[idx])
				changed = True
				break
			else:
				strHosts_found = True

	for idx in range(len(lines)):
		# save the index of the first mailer entry
		if mailer_index == 0 and lines[idx].startswith('MAILER'):
			mailer_index = idx
			break

	if nocanonify and mailer_index > 0:
		if not strNocanonify_found:
			lines.insert(mailer_index,strNocanonify)
			changed = True
		if not strUnresolvable_found:
			lines.insert(mailer_index,strUnresolvable)
			changed = True
		if not strSwitch_found:
			lines.insert(mailer_index,strSwitch)
			changed = True
		if not strHosts_found:
			lines.insert(mailer_index,strHosts)
			changed = True
		#
	if changed:
		fh=open(mcfile, 'w')
		fh.write( '\n'.join(lines) + '\n')
		fh.close()

		os.system('m4 %s > %s' % (mcfile, cffile))
		os.system('/etc/init.d/sendmail restart')
