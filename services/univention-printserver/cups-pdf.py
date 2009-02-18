# -*- coding: utf-8 -*-
#
# Univention Print Server
#  listener module: management of CUPS printers
#
# Copyright (C) 2004, 2005, 2006 Univention GmbH
#
# http://www.univention.de/
#
# All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# Binary versions of this file provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import listener
import os, string
import univention.debug
import univention_baseconfig

name='cups-pdf'
description='Manage Samba share for CUPS pdf printer'
filter='(objectClass=univentionShareSamba)'
attributes=['cn', 'univentionSharePath']
sharename="pdfPrinterShare"

# set two ucr variables (template cups-pdf) if the share for
# the pdf pseudo printer is changed
def handler(dn, new, old):

	if new.has_key('cn') and new['cn'][0] == sharename:

		if new.has_key('univentionSharePath') and new.has_key('univentionShareHost'):
			path = new['univentionSharePath'][0]
			server = new['univentionShareHost'][0]
			me = listener.baseConfig.get('hostname') + "." + listener.baseConfig.get('domainname')

			if me == server:
				univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, "cups-pdf: setting cups-pdf path to %s according to sharepath in %s on %s" % (path, sharename, server))
				list = []
				list.append('cups/cups-pdf/directory=%s' % (path))
				list.append('cups/cups-pdf/anonymous=%s' % (path))
				listener.setuid(0)
				try:
					univention_baseconfig.handler_set(list)
				finally:
					listener.unsetuid()
