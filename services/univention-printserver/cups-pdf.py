# -*- coding: utf-8 -*-
#
# Univention Print Server
#  listener module: management of CUPS printers
#
# Copyright 2004-2019 Univention GmbH
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
import univention.config_registry

name = 'cups-pdf'
description = 'Manage Samba share for CUPS pdf printer'
filter = '(objectClass=univentionShareSamba)'
attributes = ['cn', 'univentionSharePath']
sharename = "pdfPrinterShare"

# set two ucr variables (template cups-pdf) if the share for
# the pdf pseudo printer is changed


def handler(dn, new, old):

	if new.get('cn', ('',))[0] == sharename:
		if new.get('univentionSharePath') and new.get('univentionShareHost'):
			path = new['univentionSharePath'][0]
			server = new['univentionShareHost'][0]
			me = listener.baseConfig.get('hostname') + "." + listener.baseConfig.get('domainname')

			if me == server:
				ud.debug(ud.LISTENER, ud.INFO, "cups-pdf: setting cups-pdf path to %s according to sharepath in %s on %s" % (path, sharename, server))
				list = []
				list.append('cups/cups-pdf/directory=%s' % (path))
				list.append('cups/cups-pdf/anonymous=%s' % (path))
				listener.setuid(0)
				try:
					univention.config_registry.handler_set(list)
				finally:
					listener.unsetuid()
