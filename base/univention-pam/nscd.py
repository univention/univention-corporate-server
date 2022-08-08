#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Univention nscd Updater
#  Univention Listener Module
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2001-2022 Univention GmbH
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
from univention.config_registry import ConfigRegistry
import univention.debug as ud

name = 'nscd_update'
description = 'Invalidate the NSCD group cache whenever a group membership has been modified.'
filter = '(objectClass=univentionGroup)'
attributes = ['uniqueMember', 'cn']


def handler(dn, new, old):
	# type: (str, dict, dict) -> None
	pass


def postrun():
	# type: () -> None
	configRegistry = ConfigRegistry()  # TODO: why not listener.configRegistry?
	configRegistry.load()

	if configRegistry.is_true('nscd/group/invalidate_cache_on_changes', False) and configRegistry.is_false('nss/group/cachefile', True):
		listener.setuid(0)
		try:
			ud.debug(ud.LISTENER, ud.INFO, "calling 'nscd -i group'")
			listener.run('/usr/sbin/nscd', ['nscd', '-i', 'group'], uid=0)
		except Exception:
			ud.debug(ud.LISTENER, ud.ERROR, "nscd -i group was not successful")
		finally:
			listener.unsetuid()
