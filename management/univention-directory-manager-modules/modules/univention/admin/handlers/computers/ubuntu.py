# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  admin module for the managed client hosts
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

module = 'computers/ubuntu'
operations = ['add', 'edit', 'remove', 'search', 'move']
docleanup = 1
childs = 0
short_description = _('Computer: Ubuntu')
object_name = _('Ubuntu Computer')
object_name_plural = _('Ubuntu Computers')
long_description = _('Computer machine account for a Linux Client running Ubuntu')
options = {
	'default': univention.admin.option(
		short_description=_('Computer: Ubuntu'),
		default=True,
		objectClasses=('top', 'person', 'univentionHost', 'univentionUbuntuClient'),
	),
	'posix': univention.admin.option(
		short_description=_('Posix account'),
		long_description=_('Make this account an POSIX account, which is required i.a. for Linux'),
		default=1,
		objectClasses=('posixAccount', 'shadowAccount'),
	),
	'kerberos': univention.admin.option(
		short_description=_('Kerberos principal'),
		long_description=_('Make this account a Kerberos account, which is required i.a. for Single-Sign-On with Linux and Windows'),
		default=1,
		objectClasses=('krb5Principal', 'krb5KDCEntry'),
	),
	'samba': univention.admin.option(
		short_description=_('Samba account'),
		long_description=_('Make this account a Windows account'),
		editable=True,
		default=1,
		objectClasses=('sambaSamAccount',),
	)
}
property_descriptions = {
	'name': univention.admin.property(
		short_description=_('Ubuntu client name'),
		long_description=_('The node name of this computer'),
		syntax=univention.admin.syntax.hostName,
		include_in_default_search=True,
		required=True,
		identifies=True
	),
	'description': univention.admin.property(
		short_description=_('Description'),
		long_description=_('Some descriptive text for this host'),
		syntax=univention.admin.syntax.string,
		include_in_default_search=True,
	),
	'operatingSystem': univention.admin.property(
		short_description=_('Operating system'),
		long_description=_('Name of the operating system'),
		syntax=univention.admin.syntax.string,
		include_in_default_search=True,
	),
	'operatingSystemVersion': univention.admin.property(
		short_description=_('Operating system version'),
		long_description=_('Version number of the operating system'),
		syntax=univention.admin.syntax.string,
	),
	'domain': univention.admin.property(
		short_description=_('Domain'),
		long_description=_('The DNS domain of this host'),
		syntax=univention.admin.syntax.string,
		include_in_default_search=True,
	),
	'mac': univention.admin.property(
		short_description=_('MAC address'),
		long_description=_('One or more (Ethernet) Media-Access-Control addresses of network interfaces'),
		syntax=univention.admin.syntax.MAC_Address,
		multivalue=True,
		include_in_default_search=True,
	),
	'network': univention.admin.property(
		short_description=_('Network'),
		long_description=_('Reference to a network zone containing initial DNS and DHCP settings'),
		syntax=univention.admin.syntax.network,
	),
	'ip': univention.admin.property(
		short_description=_('IP address'),
		long_description=_('One or more IPv4 or IPv6 addresses of this host'),
		syntax=univention.admin.syntax.ipAddress,
		multivalue=True,
		include_in_default_search=True,
	),
	'dnsEntryZoneForward': univention.admin.property(
		short_description=_('Forward zone for DNS entry'),
		long_description=_('Reference to the DNS zone containing forward DNS entries of this host, e.g. hostname to IP addresses'),
		syntax=univention.admin.syntax.dnsEntry,
		multivalue=True,
		dontsearch=True,
	),
	'dnsEntryZoneReverse': univention.admin.property(
		short_description=_('Reverse zone for DNS entry'),
		long_description=_('Reference to the DNS zone containing reverse DNS entries of this host, e.g. IP address to hostname'),
		syntax=univention.admin.syntax.dnsEntryReverse,
		multivalue=True,
		dontsearch=True,
	),
	'dnsEntryZoneAlias': univention.admin.property(
		short_description=_('Zone for DNS alias'),
		long_description=_('Reference to the DNS zone containing DNS alias entries of this host'),
		syntax=univention.admin.syntax.dnsEntryAlias,
		multivalue=True,
		dontsearch=True,
	),
	'dnsAlias': univention.admin.property(
		short_description=_('DNS alias'),
		long_description=_('Additional names of this host in DNS'),
		syntax=univention.admin.syntax.string,
		multivalue=True,
	),
	'dhcpEntryZone': univention.admin.property(
		short_description=_('DHCP service'),
		long_description=_('Reference to the DHCP service for this host'),
		syntax=univention.admin.syntax.dhcpEntry,
		multivalue=True,
		dontsearch=True,
	),
	'password': univention.admin.property(
		short_description=_('Password'),
		long_description=_('Machine secret of this host. Must be synchronized with the password stored on the host itself, e.g. "/etc/machine.secret".'),
		syntax=univention.admin.syntax.passwd,
		options=['kerberos', 'posix', 'samba'],
		dontsearch=True
	),
	'unixhome': univention.admin.property(
		short_description=_('Unix home directory'),
		long_description=_('Absolute path to the home directory of this account'),
		syntax=univention.admin.syntax.absolutePath,
		options=['posix'],
		required=True,
		default=('/dev/null', [])
	),
	'shell': univention.admin.property(
		short_description=_('Login shell'),
		long_description=_('Absolute path to the login shell of this account'),
		syntax=univention.admin.syntax.string,
		options=['posix'],
		default=('/bin/bash', [])
	),
	'primaryGroup': univention.admin.property(
		short_description=_('Primary group'),
		long_description=_('The name of the default group of this account'),
		syntax=univention.admin.syntax.GroupDN,
		options=['posix'],
		required=True,
		dontsearch=True,
	),
	'inventoryNumber': univention.admin.property(
		short_description=_('Inventory number'),
		long_description=_('An unique identifier to identify this host as an asset of your company'),
		syntax=univention.admin.syntax.string,
		multivalue=True,
		include_in_default_search=True,
	),
	'groups': univention.admin.property(
		short_description=_('Groups'),
		long_description=_('References to additional groups of this account'),
		syntax=univention.admin.syntax.GroupDN,
		multivalue=True,
		dontsearch=True,
	),
	'sambaRID': univention.admin.property(
		short_description=_('Relative ID'),
		long_description=_('Host specific part of the security identifier to uniquely identify this computer account within your domain'),
		syntax=univention.admin.syntax.integer,
		dontsearch=True,
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
	CONFIG_NAME = 'univentionDefaultClientGroup'
	SAMBA_ACCOUNT_FLAG = 'W'

	def check_required_options(self):
		if not set(self.options) & set(['posix', 'kerberos']):
			raise univention.admin.uexceptions.invalidOptions(_('At least posix or kerberos is required.'))

	def link(self):
		pass

	@classmethod
	def lookup_filter(cls, filter_s=None, lo=None):
		con = super(object, cls).lookup_filter(filter_s, lo)
		con.expressions.append(univention.admin.filter.conjunction('|', [
			univention.admin.filter.expression('objectClass', 'posixAccount'),
			univention.admin.filter.conjunction('&', [
				univention.admin.filter.expression('objectClass', 'krb5KDCEntry'),
				univention.admin.filter.expression('objectClass', 'krb5Principal'),
			])
		]))
		return con


lookup = object.lookup


def identify(dn, attr, canonical=0):
	return 'univentionHost' in attr.get('objectClass', []) and 'univentionUbuntuClient' in attr.get('objectClass', []) and ('posixAccount' in attr.get('objectClass', []) or ('krb5KDCEntry' in attr.get('objectClass', []) and 'krb5Principal' in attr.get('objectClass', [])))
