# -*- coding: utf-8 -*-
#
# Univention Baseconfig
#  accept_unresolvable_domains in sendmail.cf
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
		fh.write( '\n'.join(lines) )
		fh.close()

		os.system('m4 %s > %s' % (mcfile, cffile))
		os.system('/etc/init.d/sendmail restart')
