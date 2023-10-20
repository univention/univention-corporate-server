# -*- coding: utf-8 -*-
#
# Univention Software-Monitor
#  listener module that watches the availability of the software monitor service
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2010-2023 Univention GmbH
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

from __future__ import absolute_import, annotations

from typing import Any, Dict, List

import univention.config_registry as ucr
import univention.debug as ud
import univention.pkgdb
import univention.uldap

from listener import SetUID


description = 'watches the availability of the software monitor service'
filter = '(|(objectClass=univentionDomainController)(objectClass=univentionMemberServer))'
attributes = ['univentionService']

ldap_info: Dict[str, Any] = {}


def handler(dn: str, new: Dict[str, List[bytes]], old: Dict[str, List[bytes]],) -> None:
    if new and b'Software Monitor' in new.get('univentionService', (),):
        with SetUID(0):
            ucr.handler_set(('pkgdb/scan=yes', ))
    elif old and b'Software Monitor' in old.get('univentionService', (),):
        if not ldap_info['lo']:
            ldap_reconnect()
        if ldap_info['lo'] and not ldap_info['lo'].search(filter='(&%s(univentionService=Software Monitor))' % filter, attr=['univentionService'],):
            with SetUID(0):
                ucr.handler_set(('pkgdb/scan=no', ))


def ldap_reconnect() -> None:
    ud.debug(ud.LISTENER, ud.INFO, 'pkgdb-watch: ldap reconnect triggered',)
    if 'ldapserver' in ldap_info and 'basedn' in ldap_info and 'binddn' in ldap_info and 'bindpw' in ldap_info:
        try:
            ldap_info['lo'] = univention.uldap.access(host=ldap_info['ldapserver'], base=ldap_info['basedn'], binddn=ldap_info['binddn'], bindpw=ldap_info['bindpw'], start_tls=2,)
        except ValueError as ex:
            ud.debug(ud.LISTENER, ud.ERROR, 'pkgdb-watch: ldap reconnect failed: %s' % (ex,),)
            ldap_info['lo'] = None
        else:
            if ldap_info['lo'] is None:
                ud.debug(ud.LISTENER, ud.ERROR, 'pkgdb-watch: ldap reconnect failed',)


def setdata(key: str, value: str,) -> None:
    if key == 'bindpw':
        ud.debug(ud.LISTENER, ud.INFO, 'pkgdb-watch: listener passed key="%s" value="<HIDDEN>"' % key,)
    else:
        ud.debug(ud.LISTENER, ud.INFO, 'pkgdb-watch: listener passed key="%s" value="%s"' % (key, value),)

    if key in ['ldapserver', 'basedn', 'binddn', 'bindpw']:
        ldap_info[key] = value
    else:
        ud.debug(ud.LISTENER, ud.INFO, 'pkgdb-watch: listener passed unknown data (key="%s" value="%s")' % (key, value),)

    if key == 'ldapserver':
        ud.debug(ud.LISTENER, ud.INFO, 'pkgdb-watch: ldap server changed to %s' % value,)
        ldap_reconnect()
