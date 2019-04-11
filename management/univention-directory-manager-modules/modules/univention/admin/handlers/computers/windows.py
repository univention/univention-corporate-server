# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  admin module for the windows hosts
#
# Copyright 2004-2019 Univention GmbH
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

from univention.admin.layout import Tab, Group
import univention.admin.filter
import univention.admin.handlers
import univention.admin.localization
import univention.admin.nagios as nagios
from univention.admin.handlers.computers.__base import ComputerObject

translation = univention.admin.localization.translation('univention.admin.handlers.computers')
_ = translation.translate

module = 'computers/windows'
operations = ['add', 'edit', 'remove', 'search', 'move']
docleanup = 1
childs = 0
short_description = _('Computer: Windows Workstation/Server')
object_name = _('Windows Workstation/Server')
object_name_plural = _('Windows Workstations/Servers')
long_description = ''
options = {
	'default': univention.admin.option(
		short_description=_('Computer: Windows Workstation/Server'),
		default=True,
		objectClasses=('top', 'person', 'univentionHost', 'univentionWindows'),
	),
	'posix': univention.admin.option(
		short_description=_('Posix account'),
		default=True,
		objectClasses=('posixAccount', 'shadowAccount'),
	),
	'kerberos': univention.admin.option(
		short_description=_('Kerberos principal'),
		default=True,
		objectClasses=('krb5Principal', 'krb5KDCEntry'),
	),
	'samba': univention.admin.option(
		short_description=_('Samba account'),
		editable=True,
		default=True,
		objectClasses=('sambaSamAccount',),
	)
}
property_descriptions = {
	'name': univention.admin.property(
		short_description=_('Windows workstation/server name'),
		long_description='',
		syntax=univention.admin.syntax.dnsName_umlauts,
		multivalue=False,
		include_in_default_search=True,
		options=[],
		required=True,
		may_change=True,
		identifies=True,
		readonly_when_synced=True,
	),
	'description': univention.admin.property(
		short_description=_('Description'),
		long_description='',
		syntax=univention.admin.syntax.string,
		multivalue=False,
		include_in_default_search=True,
		required=False,
		may_change=True,
		identifies=False,
		readonly_when_synced=True,
	),
	'operatingSystem': univention.admin.property(
		short_description=_('Operating system'),
		long_description='',
		syntax=univention.admin.syntax.string,
		multivalue=False,
		include_in_default_search=True,
		required=False,
		may_change=True,
		identifies=False,
		readonly_when_synced=True,
	),
	'operatingSystemVersion': univention.admin.property(
		short_description=_('Operating system version'),
		long_description='',
		syntax=univention.admin.syntax.string,
		multivalue=False,
		required=False,
		may_change=True,
		identifies=False,
		readonly_when_synced=True,
	),
	'domain': univention.admin.property(
		short_description=_('Domain'),
		long_description='',
		syntax=univention.admin.syntax.string,
		multivalue=False,
		include_in_default_search=True,
		required=False,
		may_change=True,
		identifies=False
	),
	'mac': univention.admin.property(
		short_description=_('MAC address'),
		long_description='',
		syntax=univention.admin.syntax.MAC_Address,
		multivalue=True,
		include_in_default_search=True,
		options=[],
		required=False,
		may_change=True,
		identifies=False
	),
	'network': univention.admin.property(
		short_description=_('Network'),
		long_description='',
		syntax=univention.admin.syntax.network,
		multivalue=False,
		options=[],
		required=False,
		may_change=True,
		identifies=False
	),
	'ip': univention.admin.property(
		short_description=_('IP address'),
		long_description='',
		syntax=univention.admin.syntax.ipAddress,
		multivalue=True,
		include_in_default_search=True,
		options=[],
		required=False,
		may_change=True,
		identifies=False
	),
	'dnsEntryZoneForward': univention.admin.property(
		short_description=_('Forward zone for DNS entry'),
		long_description='',
		syntax=univention.admin.syntax.dnsEntry,
		multivalue=True,
		options=[],
		required=False,
		may_change=True,
		dontsearch=True,
		identifies=False
	),
	'dnsEntryZoneReverse': univention.admin.property(
		short_description=_('Reverse zone for DNS entry'),
		long_description='',
		syntax=univention.admin.syntax.dnsEntryReverse,
		multivalue=True,
		options=[],
		required=False,
		may_change=True,
		dontsearch=True,
		identifies=False
	),
	'dnsEntryZoneAlias': univention.admin.property(
		short_description=_('Zone for DNS alias'),
		long_description='',
		syntax=univention.admin.syntax.dnsEntryAlias,
		multivalue=True,
		options=[],
		required=False,
		may_change=True,
		dontsearch=True,
		identifies=False
	),
	'dnsAlias': univention.admin.property(
		short_description=_('DNS alias'),
		long_description='',
		syntax=univention.admin.syntax.string,
		multivalue=True,
		options=[],
		required=False,
		may_change=True,
		identifies=False
	),
	'dhcpEntryZone': univention.admin.property(
		short_description=_('DHCP service'),
		long_description='',
		syntax=univention.admin.syntax.dhcpEntry,
		multivalue=True,
		options=[],
		required=False,
		may_change=True,
		dontsearch=True,
		identifies=False
	),
	'password': univention.admin.property(
		short_description=_('Password'),
		long_description='',
		syntax=univention.admin.syntax.passwd,
		multivalue=False,
		options=['kerberos', 'posix', 'samba'],
		required=False,
		may_change=True,
		identifies=False,
		dontsearch=True,
		readonly_when_synced=True,
	),
	'ntCompatibility': univention.admin.property(
		short_description=_('Initialize password with hostname'),
		long_description='Needed To Join NT4 Worstations',
		syntax=univention.admin.syntax.boolean,
		multivalue=False,
		options=[],
		required=False,
		dontsearch=True,
		may_change=True,
		identifies=False
	),
	'unixhome': univention.admin.property(
		short_description=_('Unix home directory'),
		long_description='',
		syntax=univention.admin.syntax.absolutePath,
		multivalue=False,
		options=['posix'],
		required=True,
		may_change=True,
		identifies=False,
		default=('/dev/null', [])
	),
	'shell': univention.admin.property(
		short_description=_('Login shell'),
		long_description='',
		syntax=univention.admin.syntax.string,
		multivalue=False,
		options=['posix'],
		required=False,
		may_change=True,
		identifies=False,
		default=('/bin/false', [])
	),
	'primaryGroup': univention.admin.property(
		short_description=_('Primary group'),
		long_description='',
		syntax=univention.admin.syntax.GroupDN,
		multivalue=False,
		include_in_default_search=True,
		options=['posix'],
		required=True,
		dontsearch=True,
		may_change=True,
		identifies=False
	),
	'inventoryNumber': univention.admin.property(
		short_description=_('Inventory number'),
		long_description='',
		syntax=univention.admin.syntax.string,
		multivalue=True,
		include_in_default_search=True,
		options=[],
		required=False,
		may_change=True,
		identifies=False
	),
	'groups': univention.admin.property(
		short_description=_('Groups'),
		long_description='',
		syntax=univention.admin.syntax.GroupDN,
		multivalue=True,
		options=[],
		required=False,
		may_change=True,
		dontsearch=True,
		identifies=False
	),
	'sambaRID': univention.admin.property(
		short_description=_('Relative ID'),
		long_description='',
		syntax=univention.admin.syntax.integer,
		multivalue=False,
		required=False,
		may_change=True,
		dontsearch=True,
		identifies=False,
		options=['samba']
	),
}

layout = [
	Tab(_('General'), _('Basic settings'), layout=[
		Group(_('Computer account'), layout=[
			['name', 'description'],
			['operatingSystem', 'operatingSystemVersion'],
			'inventoryNumber',
		]),
		Group(_('Network settings '), layout=[
			'network',
			'mac',
			'ip',
		]),
		Group(_('DNS Forward and Reverse Lookup Zone'), layout=[
			'dnsEntryZoneForward',
			'dnsEntryZoneReverse',
		]),
		Group(_('DHCP'), layout=[
			'dhcpEntryZone'
		]),
	]),
	Tab(_('Account'), _('Account'), advanced=True, layout=[
		'password',
		'ntCompatibility',
		'primaryGroup'
	]),
	Tab(_('Unix account'), _('Unix account settings'), advanced=True, layout=[
		['unixhome', 'shell']
	]),
	Tab(_('Groups'), _('Group memberships'), advanced=True, layout=[
		'groups',
	]),
	Tab(_('DNS alias'), _('Alias DNS entry'), advanced=True, layout=[
		'dnsEntryZoneAlias'
	]),
]

mapping = univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('description', 'description', None, univention.admin.mapping.ListToString)
mapping.register('domain', 'associatedDomain', None, univention.admin.mapping.ListToString)
mapping.register('inventoryNumber', 'univentionInventoryNumber')
mapping.register('mac', 'macAddress')
mapping.register('network', 'univentionNetworkLink', None, univention.admin.mapping.ListToString)
mapping.register('unixhome', 'homeDirectory', None, univention.admin.mapping.ListToString)
mapping.register('shell', 'loginShell', None, univention.admin.mapping.ListToString)
mapping.register('operatingSystem', 'univentionOperatingSystem', None, univention.admin.mapping.ListToString)
mapping.register('operatingSystemVersion', 'univentionOperatingSystemVersion', None, univention.admin.mapping.ListToString)

# add Nagios extension
nagios.addPropertiesMappingOptionsAndLayout(property_descriptions, mapping, options, layout)


class object(ComputerObject):
	module = module
	mapping = mapping
	CONFIG_NAME = 'computerGroup'
	SAMBA_ACCOUNT_FLAG = 'W'
	SERVER_TYPE = 'univentionWindows'
	SERVER_ROLE = 'windows_client'

	def _ldap_modlist(self):
		if self.hasChanged('ntCompatibility') and self['ntCompatibility'] == '1':
			self['password'] = self['name'].replace('$', '').lower()
			self.modifypassword = 1
		return super(object, self)._ldap_modlist()

	def link(self):
		pass

	@classmethod
	def lookup_filter(cls, filter_s=None, lo=None):
		con = super(object, cls).lookup_filter(filter_s, lo)
		con.expressions.append(univention.admin.filter.conjunction('!', [univention.admin.filter.expression('univentionServerRole', 'windows_domaincontroller')]))
		return con


lookup = object.lookup


def identify(dn, attr, canonical=0):
	return 'univentionHost' in attr.get('objectClass', []) and 'univentionWindows' in attr.get('objectClass', []) and 'windows_domaincontroller' not in attr.get('univentionServerRole', [])
