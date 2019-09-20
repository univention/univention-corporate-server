#
# Univention LDAP
#  restart the slapd server after well-known-sid-name-mapping made UCR changes
#
# Copyright 2014-2019 Univention GmbH
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

import subprocess
import univention.debug

relevant_names = ('Administrator', 'Domain Admins', 'Windows Hosts')


def postrun(modified_default_names=None):
	if not isinstance(modified_default_names, list):
		return

	slapd_restart = False
	for name in modified_default_names:
		if name in relevant_names:
			slapd_restart = True
			break

	if slapd_restart:
		p1 = subprocess.Popen(['invoke-rc.d', 'slapd', 'graceful-restart'],
			close_fds=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
		(stdout, stderr) = p1.communicate()
		if stdout:
			univention.debug.debug(
				univention.debug.LISTENER,
				univention.debug.ERROR,
				"%s: postrun: %s" % ('well-known-sid-name-mapping.d/univention-ldap-server.py', stdout)
			)
