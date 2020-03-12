#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

# Copyright 2020 Univention GmbH
#
# https://www.univention.de/
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
# <https://www.gnu.org/licenses/>.

"""
System Diagnosis UMC module to check Spamassassin rules.
"""

import pty
import os
import pwd
import subprocess
from univention.management.console.modules.diagnostic import Warning, ProblemFixed, MODULE
from univention.lib.i18n import Translation
_ = Translation('univention-management-console-module-diagnostic').translate


title = _('Spamassassin Rules Check')
description = _('All spamassassin rules ok')
run_descr = ['Checks spamassassin rule set and configuration files']


def run(_umc_instance, retest=False):
	uid = -1
	gid = -1
	try:
		pw = pwd.getpwnam('debian-spamd')
		uid = pw[2]
		gid = pw[3]
	except KeyError:
		return

	process = subprocess.Popen(['/usr/bin/spamassassin', '--lint'], preexec_fn=demote(uid, gid))
	result = process.wait()
	if result != 0:
		buttons = [{
			'action': 'update_signatures',
			'label': _('Update Signatures'),
		}]
		raise Warning('Errors in configuration files', buttons=buttons)

	if retest:
		raise ProblemFixed(buttons=[])


def update_signatures(_umc_instance):
	MODULE.process('Updating signatures')
	master, slave = pty.openpty() # cron script requires pseudo terminal to skip sleep
	cron_result = subprocess.Popen(['/etc/cron.daily/spamassassin'], stdin=slave).wait()
	os.close(slave)
	MODULE.process('Updating signatures done')

	if cron_result:
		raise Warning('Could not fetch signatures')
	return run(_umc_instance, retest=True)


def demote(user_uid, user_gid):
	def result():
		os.setgid(user_gid)
		os.setuid(user_uid)
	return result


actions = {
	'update_signatures': update_signatures
}

if __name__ == '__main__':
	from univention.management.console.modules.diagnostic import main
	main()
