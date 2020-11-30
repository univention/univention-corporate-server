# -*- coding: utf-8 -*-
#
# Univention Mail Stack
#  listener module: mail domain configuration
#
# Copyright 2005-2021 Univention GmbH
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
import re
import univention.debug

name = 'hosteddomains'
description = 'update mail/hosteddomains'
filter = '(objectClass=univentionMailDomainname)'
attributes = []


def handler(dn, new, old):
	# type: (str, dict, dict) -> None
	configRegistry = univention.config_registry.ConfigRegistry()
	configRegistry.load()

	old_hosteddomains = set(re.split('[ ]+', configRegistry.get('mail/hosteddomains', '')))
	hosteddomains = old_hosteddomains.copy()

	# remove old add new
	if old.get('cn'):
		hosteddomains.discard(old['cn'][0].decode('UTF-8'))
		univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, "hosteddomains: removed %r" % old['cn'][0])
	if new.get('cn'):
		hosteddomains.add(new['cn'][0].decode('UTF-8'))
		univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, "hosteddomains: added %r" % new['cn'][0])

	# if something changed then set UCR variable
	if old_hosteddomains != hosteddomains:
		try:
			listener.setuid(0)
			univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, "hosteddomains: %s" % u'mail/hosteddomains=%s' % ' '.join(hosteddomains))
			univention.config_registry.handler_set([u'mail/hosteddomains=%s' % ' '.join(hosteddomains)])
		finally:
			listener.unsetuid()
