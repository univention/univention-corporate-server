# -*- coding: utf-8 -*-
#
# Univention Software-Monitor
#  listener module that watches the availability of the software monitor service
#
# Copyright 2010 Univention GmbH
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

import listener
import univention.config_registry as ucr
import univention.pkgdb

name='pkgdb-watch'
description='watches the availability of the software monitor service'
filter='(|(objectClass=univentionDomainController)(objectClass=univentionMemberServer))'
attributes=['univentionService']

def handler( dn, new, old ):
	if new and 'Software Monitor' in new.get( 'univentionService', () ):
		listener.setuid( 0 )
		ucr.handler_set( ( 'pkgdb/scan?yes', ) )
		listener.unsetuid()

