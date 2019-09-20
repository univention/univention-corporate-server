# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  admin module for the DHCP hosts
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
import univention.debug as ud

from .__common import DHCPBase, add_dhcp_options

translation = univention.admin.localization.translation('univention.admin.handlers.dhcp')
_ = translation.translate

module = 'dhcp/host'
operations = ['add', 'edit', 'remove', 'search']
superordinate = 'dhcp/service'
childs = 0
short_description = _('DHCP: Host')
object_name = _('DHCP host')
object_name_plural = _('DHCP hosts')
long_description = _('Configure a host identified by its hardware MAC address.')
options = {
	'default': univention.admin.option(
		default=True,
		objectClasses=['top', 'univentionDhcpHost']
	),
}
property_descriptions = {
	'host': univention.admin.property(
		short_description=_('Hostname'),
		long_description=_('A unique name for this DHCP host entry. Using the hostname is recommended.'),
		syntax=univention.admin.syntax.string,
		include_in_default_search=True,
		required=True,
		identifies=True
	),
	'hwaddress': univention.admin.property(
		short_description=_('Hardware address'),
		long_description=_('Currently, only the ethernet and token-ring types are recognized. \
The hardware-address should be a set of hexadecimal octets (numbers from 0 through ff) separated by colons.'),
		syntax=univention.admin.syntax.DHCP_HardwareAddress,
		required=True,
	),
	'fixedaddress': univention.admin.property(
		short_description=_('Fixed IP addresses'),
		long_description=_('Assign one or more fixed IP addresses. \
Each address should be either an IP address or a domain name that resolves to one or more IP addresses.'),
		syntax=univention.admin.syntax.hostOrIP,
		multivalue=True,
	),
}
layout = [
	Tab(_('General'), _('Basic settings'), layout=[
		Group(_('General DHCP host settings'), layout=[
			'host',
			'hwaddress',
			'fixedaddress'
		]),
	])
]


def unmapHWAddress(old):
	ud.debug(ud.ADMIN, ud.INFO, 'host.py: unmapHWAddress: old: %s' % old)
	if not old:
		return ['', '']
	return old[0].split(' ')


def mapHWAddress(old):
	ud.debug(ud.ADMIN, ud.INFO, 'host.py: mapHWAddress: old: %s' % old)
	if not old[0]:
		return ''
	else:
		if len(old) > 1:
			return '%s %s' % (old[0], old[1])
		else:
			return old


mapping = univention.admin.mapping.mapping()
mapping.register('host', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('hwaddress', 'dhcpHWAddress', mapHWAddress, unmapHWAddress)
mapping.register('fixedaddress', 'univentionDhcpFixedAddress')

add_dhcp_options(__name__)


class object(DHCPBase):
	module = module


lookup_filter = object.lookup_filter
lookup = object.lookup
identify = object.identify
