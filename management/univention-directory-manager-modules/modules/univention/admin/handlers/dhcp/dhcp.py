# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  admin module for the DHCP objects
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

from univention.admin.layout import Tab
import univention.admin.filter
import univention.admin.localization

import univention.admin.handlers
import univention.admin.handlers.dhcp.host
import univention.admin.handlers.dhcp.pool
import univention.admin.handlers.dhcp.server
import univention.admin.handlers.dhcp.service
import univention.admin.handlers.dhcp.shared
import univention.admin.handlers.dhcp.sharedsubnet
import univention.admin.handlers.dhcp.subnet


translation = univention.admin.localization.translation('univention.admin.handlers.dhcp')
_ = translation.translate


module = 'dhcp/dhcp'

childs = 0
childmodules = ["dhcp/service"]
short_description = _('All DHCP services')
object_name = _('DHCP service')
object_name_plural = _('DHCP services')
long_description = _('Manage the Domain Host Configuration Protocol service.')
operations = ['search']
virtual = 1
options = {}
property_descriptions = {
	'name': univention.admin.property(
		short_description=_('Name'),
		long_description='',
		syntax=univention.admin.syntax.string,
		include_in_default_search=True,
		required=True,
		identifies=True
	)
}

layout = [Tab(_('General'), _('Basic settings'), layout=["name"])]

mapping = univention.admin.mapping.mapping()


class object(univention.admin.handlers.simpleLdap):
	module = module


def lookup(co, lo, filter_s, base='', superordinate=None, scope='sub', unique=False, required=False, timeout=-1, sizelimit=0):
	ret = []
	if superordinate:
		ret += univention.admin.handlers.dhcp.host.lookup(co, lo, filter_s, base, superordinate, scope, unique, required, timeout, sizelimit)
		ret += univention.admin.handlers.dhcp.pool.lookup(co, lo, filter_s, base, superordinate, scope, unique, required, timeout, sizelimit)
		ret += univention.admin.handlers.dhcp.server.lookup(co, lo, filter_s, base, superordinate, scope, unique, required, timeout, sizelimit)
		ret += univention.admin.handlers.dhcp.shared.lookup(co, lo, filter_s, base, superordinate, scope, unique, required, timeout, sizelimit)
		ret += univention.admin.handlers.dhcp.sharedsubnet.lookup(co, lo, filter_s, base, superordinate, scope, unique, required, timeout, sizelimit)
		ret += univention.admin.handlers.dhcp.subnet.lookup(co, lo, filter_s, base, superordinate, scope, unique, required, timeout, sizelimit)
	else:
		ret += univention.admin.handlers.dhcp.service.lookup(co, lo, filter_s, base, superordinate, scope, unique, required, timeout, sizelimit)
	return ret


def identify(dn, attr, canonical=0):
	pass
