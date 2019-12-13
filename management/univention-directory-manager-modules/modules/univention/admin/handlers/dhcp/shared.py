# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  admin module for the dhcp shares
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

from univention.admin.layout import Tab, Group
import univention.admin.filter
import univention.admin.handlers
import univention.admin.localization

from .__common import DHCPBase, add_dhcp_options

translation = univention.admin.localization.translation('univention.admin.handlers.dhcp')
_ = translation.translate

module = 'dhcp/shared'
operations = ['add', 'edit', 'remove', 'search']
superordinate = 'dhcp/service'
childs = True
childmodules = ('dhcp/sharedsubnet',)
short_description = _('DHCP: Shared network')
object_name = _('Shared network')
object_name_plural = _('Shared network')
long_description = _('A shared physical network, where multiple IP address ranges are used.')
options = {
	'default': univention.admin.option(
		default=True,
		objectClasses=['top', 'dhcpSharedNetwork'],
	),
}
property_descriptions = {
	'name': univention.admin.property(
		short_description=_('Shared network name'),
		long_description=_('A unique name for this shared network.'),
		syntax=univention.admin.syntax.uid,
		include_in_default_search=True,
		required=True,
		may_change=False,
		identifies=True
	)
}

layout = [
	Tab(_('General'), _('Basic settings'), layout=[
		Group(_('DHCP shared network description'), layout=[
			'name'
		]),
	]),
]

mapping = univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)

add_dhcp_options(__name__)


class object(DHCPBase):
	module = module


lookup_filter = object.lookup_filter
lookup = object.lookup
identify = object.identify
