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
# /usr/share/common-licenses/AGPL-3; if not, seG
# <http://www.gnu.org/licenses/>.


from subprocess import Popen, PIPE, STDOUT
from univention.management.console.config import ucr
from univention.management.console.modules.diagnostic import Critical

from univention.lib.i18n import Translation
_ = Translation('univention-management-console-module-diagnostic').translate

title = _('Check for blocked ucr templates')
description = _('No problems found with blocked ucr templates')


def run():
	ucr.load()
	try:
		process = Popen(["univention-check-templates"], stdout=PIPE, stderr=STDOUT)
		stdout, stderr = process.communicate()
		if process.returncode:
			description = _("Calling 'univention-check-templates failed")
			raise Critical("\n".join([
				description,
				"Returncode of process: %s" % (process.returncode),
				"stderr: %s" % (stderr)
			]))
		if stdout == "":
			return
		else:
			description = _("Error from 'univention-check-templates' returned.")
			raise Critical("\n".join([
				description,
				"Stdout: %s" % (stdout),
				"Stderr: %s" % (stderr)
			]))
	except Critical:
		raise
	except Exception as ex:
		description = _("Unknown problem during check of 'univention-check-templates")
		raise Critical('\n'.join([
			description,
			"Exception-Type: %s" % (ex.__class__),
			"Exception-Message: %s" % (ex.message)
		]))


if __name__ == '__main__':
	from univention.management.console.modules.diagnostic import main
	main()
