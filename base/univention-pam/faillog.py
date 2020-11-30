#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Univention PAM
#  Listener module for faillog
#
# Copyright 2001-2021 Univention GmbH
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

import listener
import univention.debug as ud
from univention.admin.handlers.users.user import unmapLocked

name = 'faillog'
description = 'The listener module resets the faillog count'
filter = '(objectClass=shadowAccount)'
attributes = []


def __login_is_locked(attrs):
	# type: (dict) -> bool
	return unmapLocked(attrs) == '1'


def handler(dn, new, old):
	# type: (str, dict, dict) -> None
	if new and old:
		if __login_is_locked(old) and not __login_is_locked(new):
			# reset local bad password count
			ud.debug(ud.LISTENER, ud.PROCESS, 'Reset faillog for user %s' % new['uid'][0].decode('UTF-8'))
			listener.setuid(0)
			try:
				listener.run('/sbin/pam_tally', ['pam_tally', '--user', new['uid'][0].decode('UTF-8'), '--reset'])
			finally:
				listener.unsetuid()
