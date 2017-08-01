#!/usr/bin/python2.7
# coding: utf-8
#
# Univention Management Console module:
#  System Diagnosis UMC module
#
# Copyright 2017 Univention GmbH
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

import subprocess

import univention.config_registry
from univention.management.console.modules.diagnostic import Critical

from univention.lib.i18n import Translation
_ = Translation('univention-management-console-module-diagnostic').translate

title = _('Check for Kerberos-authenticated DNS Updates')
description = _('The check for updating DNS-Records with Kerberos Authentication was successful.')


def run():
	config_registry = univention.config_registry.ConfigRegistry()
	config_registry.load()

	pwdpath = config_registry.get("umc/module/diagnostic/umc_password")
	hostname = config_registry.get("umc/module/diagnostic/umc_user")
	domainname = config_registry.get("domainname")
	kerberos_realm = config_registry.get("kerberos/realm")
	process = subprocess.Popen(['testparm', '-sv'], stdout=subprocess.PIPE,
		stderr=subprocess.STDOUT)
	stdout, stderr = process.communicate()
	samba_server_role = utils.get_string_between_strings(stdout, "server role = ", "\n")

	if not samba_server_role == "active directory domain controller":
		return

	kinit = ['kinit', '--password-file=%s' % (pwdpath), '%s@%s' % (hostname, kerberos_realm)]
	process = subprocess.Popen(kinit, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
	if process.returncode:
		description = _('Kinit with machine account failed')
		raise Critical('\n'.join([
			description,
			"Returncode of process: %s" % (process.returncode)
		]))
	stdout, stderr = process.communicate()
	nsupdate_process = subprocess.Popen(['nsupdate', '-g'],
		stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.STDOUT)
	nsupdate_process.stdin.write('prereq yxdomain %s\nsend\nquit\n' % (domainname))
	stdout, stderr = nsupdate_process.communicate()
	if nsupdate_process.returncode != 0:
		description = _('nsupdate -g failed')
		raise Critical('\n'.join([
			description,
			"Returncode of process: %s" % (nsupdate_process.returncode),
			"stdout: %s" % (stdout),
			"stderr: %s" % (stderr)
		]))

if __name__ == '__main__':
	from univention.management.console.modules.diagnostic import main
	main()
