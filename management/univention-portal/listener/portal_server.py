#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Copyright 2019 Univention GmbH
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

import subprocess

import listener
from univention.config_registry import ConfigRegistry
import univention.debug as ud

ucr = ConfigRegistry()
ucr.load()

name = 'portal_server'
description = 'Tell portal server to refresh when something important changed'
filter = '(|(univentionObjectType=settings/portal)(univentionObjectType=settings/portal_category)(univentionObjectType=settings/portal_entry)(&(objectClass=univentionPortalComputer)(cn=%s)))' % ucr.get('hostname')
attributes = []


def handler(dn, new, old):
	listener.setuid(0)
	ud.debug(ud.LISTENER, ud.INFO, 'portal server handler has fired!')
	try:
		with open('/var/cache/univention-portal/refresh_portal', 'w'):
			pass
		ud.debug(ud.LISTENER, ud.INFO, 'refresh_portal file was created.')
	finally:
		listener.unsetuid()


def postrun():
	listener.setuid(0)
	try:
		subprocess.call(['service', 'univention-portal-server', 'reload'])
	finally:
		listener.unsetuid()
