#!/usr/bin/python2.7
# coding: utf-8
#
# Univention Management Console module:
#  System Diagnosis UMC module
#
# Copyright 2016-2019 Univention GmbH
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
import ldap
import socket
import subprocess

import univention
import univention.uldap
import univention.lib.misc
import univention.admin.uldap
import univention.admin.modules as udm_modules
import univention.config_registry
from univention.config_registry import handler_set as ucr_set
from univention.config_registry import handler_unset as ucr_unset
from univention.management.console.modules.diagnostic import Critical, ProblemFixed, MODULE, Success

from univention.lib.i18n import Translation
_ = Translation('univention-management-console-module-diagnostic').translate
run_descr = ["Trying to authenticate with machine password against LDAP  Similar to running: univention-ldapsearch -LLLs base dn"]
title = _('Check if spamassassin rules exist')
description = _('Spamassassin rules exist')
links = [{
}]

def update_and_restart(umc_instance):
        subprocess.check_call(["sa-update"])
        subprocess.check_call(["systemctl", "restart", "amavis.service"])
        run(umc_instance, retest=True)

actions = {
	'update_and_restart': update_and_restart,
}
	

def run(_umc_instance, retest=False):
	buttons = []
	try:
		subprocess.check_call(["dpkg", "-s", "spamassassin"])
	except subprocess.CalledProcessError:
		raise Success('Spamassassin is not installed')

	sa_version =  subprocess.check_output(["spamassassin", "-V"])
	sa_version =  sa_version.split()[2]
	sa_version = sa_version.split('.')
	folder_name = '%s.%03d%03d' % (int(sa_version[0]), int(sa_version[1]), int(sa_version[2]))
	if not os.path.exists("/var/lib/spamassassin/"+folder_name):
		buttons = [{
                        'action': 'update_and_restart',
                        'name': 'update_and_restart',
                        'label': 'update spamassassin rules'
                }]
		raise Critical('spamassassin rules could not be found', buttons=buttons)
	if not os.listdir('/var/lib/spamassassin/'+folder_name):
		buttons = [{
			'action': 'update_and_restart',
			'name': 'update_and_restart',
			'label': 'update spamassassin rules'
		}]
		raise Critical('spamassassin rules could not be found', buttons=buttons)
	if retest: raise ProblemFixed()
	raise Success()

if __name__ == '__main__':
	from univention.management.console.modules.diagnostic import main
	main()
