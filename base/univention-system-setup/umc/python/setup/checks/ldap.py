#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: system setup
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2018-2022 Univention GmbH
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

from __future__ import absolute_import

from pipes import quote
from subprocess import PIPE, Popen

from ldap.filter import filter_format

from univention.management.console.modules.setup.util import _temporary_password_file
from univention.management.console.log import MODULE


def check_if_uid_is_available(uid, role, address, username, password):
	"""check if either the UID it not yet taken at all
		or it is already taken (by our previous self) and still matches the server role
	"""
	# type: (str, str, str, str, str) -> bool
	filter_s = filter_format("(&(objectClass=person)(uid=%s)(!(univentionServerRole=%s)))", [uid, role])
	rcmd = 'univention-ldapsearch -LLL %s 1.1' % (quote(filter_s),)
	with _temporary_password_file(password) as password_file:
		cmd = [
			"univention-ssh", "--no-split",
			password_file,
			'%s@%s' % (username, address),
			rcmd
		]
		MODULE.info("Running %s" % " ".join(quote(arg) for arg in cmd))
		process = Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE)
		stdout, stderr = process.communicate()
		if process.wait() or stderr:
			MODULE.error("Failed checking uid=%s role=%s: %s" % (uid, role, stderr))
	return not stdout.strip()
