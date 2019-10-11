# -*- coding: utf-8 -*-
#
# Univention LDAP
"""listener script to set umc/self-service/passwordreset/email/webserver_address."""
#
# Copyright 2017-2019 Univention GmbH
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
import univention.config_registry

name = 'selfservice'
description = 'Set umc/self-service/passwordreset/email/webserver_address.'
filter = '(univentionService=univention-self-service)'
attributes = []

UCRV = 'umc/self-service/passwordreset/email/webserver_address'


def handler(dn, new, old):
	if new:
		ucr = univention.config_registry.ConfigRegistry()
		ucr.load()
		if not ucr.get(UCRV):
			fqdn = '%s.%s' % (new['cn'][0], new.get('associatedDomain')[0])
			listener.setuid(0)
			try:
				univention.config_registry.handler_set(['%s=%s' % (UCRV, fqdn)])
			finally:
				listener.unsetuid()
