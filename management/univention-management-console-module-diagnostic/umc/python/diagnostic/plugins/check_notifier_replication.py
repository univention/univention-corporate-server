#!/usr/bin/python2.7
# coding: utf-8
#
# Univention Management Console module:
#  System Diagnosis UMC module
#
# Copyright 2016-2017 Univention GmbH
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

from subprocess import Popen, PIPE, STDOUT
from univention.management.console.modules.diagnostic import Critical

from univention.lib.i18n import Translation
_ = Translation('univention-management-console-module-diagnostic').translate

title = _('Check for problems with ldap replication')
description = _('No problems found with ldap replication')


def run():
	process = Popen(["/usr/share/univention-directory-listener/get_notifier_id.py"], stdout=PIPE, stderr=STDOUT)
	if process.returncode:
		description = _("Calling /usr/share/univention-directory-listener/get_notifier_id.py faield")
		raise Critical("\n".join([
			description,
			"Returncode of process: %s" % (process.returncode)
		]))
	stdout, stderr = process.communicate()
	f = open("/var/lib/univention-directory-listener/notifier_id", "r")
	s = f.read()
	if stdout.rstrip() == s:
		return
	else:
		description = _("Notifier ids are different.")
		raise Critical("\n".join([
			description,
			"Id from Master: %s" % (stdout.rstrip()),
			"Id from local system: %s" % (s)
		]))

if __name__ == '__main__':
	from univention.management.console.modules.diagnostic import main
	main()
