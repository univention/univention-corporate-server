#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention Management Console module server-overview
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

import univention.admin.modules as udm_modules
from univention.management.console.config import ucr
from univention.management.console.base import Base
from univention.management.console.modules.decorators import simple_response
from univention.management.console.ldap import get_machine_connection


class Instance(Base):

	@simple_response
	def query(self):
		udm_modules.update()
		lo, po = get_machine_connection()
		servers = udm_modules.lookup('computers/computer', None, lo, filter='(&(|(objectClass=univentionDomainController)(objectClass=univentionMemberServer))(!(univentionObjectFlag=docker)))', base=ucr['ldap/base'], scope='sub')

		result = [dict(
			dn=i.dn,
			hostname=i.info.get('name'),
			domain=i.info.get('domain'),
			ip=i.info.get('ip'),
			version=i.info.get('operatingSystemVersion'),
			serverRole=i.info.get('serverRole'),
		) for i in servers]
		return result
