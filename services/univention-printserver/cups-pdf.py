#
# Univention Print Server
#  listener module: management of CUPS printers
#
# SPDX-FileCopyrightText: 2004-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from __future__ import annotations

import univention.config_registry
import univention.debug as ud

import listener


description = 'Manage Samba share for CUPS pdf printer'
filter = '(objectClass=univentionShareSamba)'
attributes = ['cn', 'univentionSharePath']

sharename = "pdfPrinterShare"

# set two ucr variables (template cups-pdf) if the share for
# the pdf pseudo printer is changed


def handler(dn: str, new: dict[str, list[bytes]], old: dict[str, list[bytes]]) -> None:
    if new.get('cn', [b''])[0].decode('UTF-8') == sharename and new.get('univentionSharePath') and new.get('univentionShareHost'):
        path = new['univentionSharePath'][0].decode('UTF-8')
        server = new['univentionShareHost'][0].decode('ASCII')
        me = listener.configRegistry.get('hostname') + "." + listener.configRegistry.get('domainname')

        if me == server:
            ud.debug(ud.LISTENER, ud.INFO, "cups-pdf: setting cups-pdf path to %s according to sharepath in %s on %s" % (path, sharename, server))
            list_ = []
            list_.append('cups/cups-pdf/directory=%s' % (path,))
            list_.append('cups/cups-pdf/anonymous=%s' % (path,))
            listener.setuid(0)
            try:
                univention.config_registry.handler_set(list_)
            finally:
                listener.unsetuid()
