#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention Debug
#  debug2-test.py
#
# Copyright 2004-2014 Univention GmbH
#
# http://www.univention.de/
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
# <http://www.gnu.org/licenses/>.

import univention.debug2 as ud

ud.init( '/tmp/univention.debug2.log', 1, 1)
ud.set_level( ud.PROCESS, ud.ERROR )
ud.set_level( ud.LISTENER, ud.WARN )
ud.set_level( ud.NETWORK, ud.PROCESS )
ud.set_level( ud.LDAP, ud.INFO )
ud.set_level( ud.ADMIN, ud.ALL )

for lvl in [ ud.ERROR, ud.WARN, ud.PROCESS, ud.INFO, ud.ALL ]:
	for mod in [ ud.ADMIN, ud.PROCESS, ud.LISTENER, ud.NETWORK, ud.LDAP ]:
		ud.debug( mod, lvl, '==> send msg to %s with level %s' % (mod, lvl) )


ud.set_level( ud.ADMIN, ud.ERROR )
ud.debug( ud.ADMIN, ud.ERROR, '==> admin error' )
ud.debug( ud.ADMIN, ud.WARN, '==> admin warn' )
ud.debug( ud.ADMIN, ud.PROCESS, '==> admin process' )
ud.debug( ud.ADMIN, ud.INFO, '==> admin info' )
ud.debug( ud.ADMIN, ud.ALL, '==> admin all' )

ud.set_level( ud.LDAP, ud.INFO )
ud.debug( ud.LDAP, ud.ERROR, '==> ldap error' )
ud.debug( ud.LDAP, ud.WARN, '==> ldap warn' )
ud.debug( ud.LDAP, ud.PROCESS, '==> ldap process' )
ud.debug( ud.LDAP, ud.INFO, '==> ldap info' )
ud.debug( ud.LDAP, ud.ALL, '==> ldap all' )

ud.debug( ud.ADMIN, ud.ERROR, '==> adding function' )
_d = ud.function(' my new function ')
ud.debug( ud.ADMIN, ud.ERROR, '==> trying to delete function' )
del _d
ud.debug( ud.ADMIN, ud.ERROR, '==> function deleted' )

ud.reopen()

ud.set_level( ud.ADMIN, ud.ALL )
ud.debug( ud.ADMIN, ud.ALL, '==> admin all' )
ud.debug( ud.ADMIN, ud.ERROR, '==> admin error' )
ud.debug( ud.ADMIN, ud.WARN, '==> admin warn' )
ud.debug( ud.ADMIN, ud.PROCESS, '==> admin process' )
ud.debug( ud.ADMIN, ud.INFO, '==> admin info' )

ud.set_level( ud.LDAP, ud.WARN )
ud.debug( ud.LDAP, ud.ALL, '==> ldap all' )
ud.debug( ud.LDAP, ud.ERROR, '==> ldap error' )
ud.debug( ud.LDAP, ud.WARN, '==> ldap warn' )
ud.debug( ud.LDAP, ud.PROCESS, '==> ldap process' )
ud.debug( ud.LDAP, ud.INFO, '==> ldap info' )

ud.set_level( ud.LDAP, 10 )
ud.debug( ud.LDAP, ud.ALL, '==> ldap all' )
ud.set_level( ud.LDAP, -3 )
ud.debug( ud.LDAP, ud.ERROR, '==> ldap error' )


ud.debug( ud.ADMIN, ud.ERROR, '==> adding function' )
_d = ud.function(' my new function ')
ud.debug( ud.ADMIN, ud.ERROR, '==> trying to delete function' )
del _d
ud.debug( ud.ADMIN, ud.ERROR, '==> function deleted' )
