# -*- coding: utf-8 -*-
#
# Univention Software-Monitor
#  listener module that watches the availability of the software monitor service
#
# Copyright (C) 2010 Univention GmbH
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
import univention.config_registry as ucr
import univention.pkgdb

name='pkgdb-watch'
description='watches the availability of the software monitor service'
filter='(|(objectClass=univentionDomainController)(objectClass=univentionMemberServer))'
attributes=['univentionService']

def handler( dn, new, old ):
	if univention.pkgdb.is_service_available():
		listener.setuid( 0 )
		ucr.handler_set( ( 'pkgdb/scan?yes', ) )
		listener.unsetuid()

