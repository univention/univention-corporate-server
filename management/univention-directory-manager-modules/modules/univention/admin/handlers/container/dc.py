# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  admin module for the dc objects
#
# Copyright 2004-2017 Univention GmbH
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
from univention.admin import configRegistry

import univention.admin.filter
import univention.admin.handlers
import univention.admin.password
import univention.admin.allocators
import univention.admin.localization

import univention.admin.handlers.settings.directory
import univention.admin.handlers.users.user
import univention.admin.handlers.groups.group

translation = univention.admin.localization.translation('univention.admin.handlers.container')
_ = translation.translate


module = 'container/dc'
childs = 1
operations = ['search', 'edit']
short_description = _('Container: Domain')
long_description = ''
options = {
	'default': univention.admin.option(
		default=True,
		objectClasses=['top', 'domain', 'univentionDomain', 'univentionBase']
	),
	'kerberos': univention.admin.option(
		short_description=_('Kerberos realm'),
		objectClasses=['krb5Realm', ],
		default=1
	),
	'samba': univention.admin.option(
		short_description=_('Samba'),
		objectClasses=['sambaDomain'],
		default=1
	),
}
property_descriptions = {
	'name': univention.admin.property(
		short_description=_('Name'),
		long_description='',
		syntax=univention.admin.syntax.string,
		multivalue=False,
		include_in_default_search=True,
		options=[],
		required=True,
		may_change=False,
		identifies=True
	),
	'dnsForwardZone': univention.admin.property(
		short_description=_('DNS forward lookup zone'),
		long_description='',
		syntax=univention.admin.syntax.DNS_ForwardZone,
		multivalue=True,
		options=[],
		required=False,
		may_change=False,
		identifies=False
	),
	'dnsReverseZone': univention.admin.property(
		short_description=_('DNS reverse lookup zone'),
		long_description='',
		syntax=univention.admin.syntax.DNS_ReverseZone,
		multivalue=True,
		options=[],
		required=False,
		may_change=False,
		identifies=False
	),
	'sambaDomainName': univention.admin.property(
		short_description=_('Samba domain name'),
		long_description='',
		syntax=univention.admin.syntax.string,
		multivalue=True,
		options=['samba'],
		required=True,
		may_change=True,
		default=(configRegistry.get('domainname', '').upper(), []),
		identifies=False
	),
	'sambaSID': univention.admin.property(
		short_description=_('Samba SID'),
		long_description='',
		syntax=univention.admin.syntax.string,
		multivalue=False,
		options=['samba'],
		required=True,
		may_change=False,
		identifies=False
	),
	'sambaNextUserRid': univention.admin.property(
		short_description=_('Samba Next User RID'),
		long_description='',
		syntax=univention.admin.syntax.string,
		multivalue=False,
		options=['samba'],
		required=False,
		may_change=True,
		default=('1000', []),
		identifies=False
	),
	'sambaNextGroupRid': univention.admin.property(
		short_description=_('Samba Next Group RID'),
		long_description='',
		syntax=univention.admin.syntax.string,
		multivalue=False,
		options=['samba'],
		required=False,
		may_change=True,
		default=('1000', []),
		identifies=False
	),
	'kerberosRealm': univention.admin.property(
		short_description=_('Kerberos realm'),
		long_description='',
		syntax=univention.admin.syntax.string,
		multivalue=False,
		options=['kerberos'],
		required=True,
		may_change=False,
		default=(configRegistry.get('domainname', '').upper(), []),
		identifies=False
	),
}

layout = [
	Tab(_('General'), _('Basic settings'), layout=[
		Group(_('Domain container description'), layout=[
			"name"
		]),
	]),
	Tab(_('DNS'), _('DNS Zones'), advanced=True, layout=[
		["dnsForwardZone", "dnsReverseZone"]
	]),
	Tab(_('Samba'), _('Samba Settings'), advanced=True, layout=[
		["sambaDomainName", "sambaSID"],
		["sambaNextUserRid", "sambaNextGroupRid"]
	]),
	Tab(_('Kerberos'), _('Kerberos Settings'), advanced=True, layout=[
		'kerberosRealm'
	]),
]

mapping = univention.admin.mapping.mapping()
mapping.register('name', 'dc', None, univention.admin.mapping.ListToString)
mapping.register('sambaDomainName', 'sambaDomainName')
mapping.register('sambaSID', 'sambaSID', None, univention.admin.mapping.ListToString)
mapping.register('sambaNextUserRid', 'sambaNextUserRid', None, univention.admin.mapping.ListToString)
mapping.register('sambaNextGroupRid', 'sambaNextGroupRid', None, univention.admin.mapping.ListToString)
mapping.register('kerberosRealm', 'krb5RealmName', None, univention.admin.mapping.ListToString)


class object(univention.admin.handlers.simpleLdap):
	module = module

	def open(self):
		univention.admin.handlers.simpleLdap.open(self)

		if self.exists():
			self['dnsForwardZone'] = self.lo.searchDn(base=self.dn, scope='domain', filter='(&(objectClass=dNSZone)(relativeDomainName=@)(!(zoneName=*.in-addr.arpa)))')
			self['dnsReverseZone'] = self.lo.searchDn(base=self.dn, scope='domain', filter='(&(objectClass=dNSZone)(relativeDomainName=@)(zoneName=*.in-addr.arpa))')


def lookup(co, lo, filter_s, base='', superordinate=None, scope='sub', unique=False, required=False, timeout=-1, sizelimit=0):
	filter = univention.admin.filter.conjunction('&', [
		univention.admin.filter.expression('objectClass', 'univentionBase'),
	])

	if filter_s:
		filter_p = univention.admin.filter.parse(filter_s)
		univention.admin.filter.walk(filter_p, univention.admin.mapping.mapRewrite, arg=mapping)
		filter.expressions.append(filter_p)

	res = []
	for dn, attrs in lo.search(unicode(filter), base, scope, [], unique, required, timeout, sizelimit):
		res.append(object(co, lo, None, dn, attributes=attrs))
	return res


def identify(dn, attr, canonical=0):
	return 'univentionBase' in attr.get('objectClass', [])
