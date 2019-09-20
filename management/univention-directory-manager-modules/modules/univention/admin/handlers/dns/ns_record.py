# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  admin module for the DNS NS records
#
# Copyright 2018-2019 Univention GmbH
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
import univention.admin.handlers.dns.forward_zone
import univention.admin.localization

translation = univention.admin.localization.translation('univention.admin.handlers.dns')
_ = translation.translate

module = 'dns/ns_record'
operations = ['add', 'edit', 'remove', 'search']
columns = ['nameserver']
superordinate = 'dns/forward_zone'
childs = 0
short_description = 'DNS: NS Record'
object_name = 'Nameserver record'
object_name_plural = 'Nameserver records'
long_description = _('Delegate a subzone to other nameservers.')
options = {
	'default': univention.admin.option(
		default=True,
		objectClasses=['top', 'dNSZone'],
	),
}
property_descriptions = {
	'zone': univention.admin.property(
		short_description=_('Zone name'),
		long_description=_('The name of the subzone relative to the parent.'),
		syntax=univention.admin.syntax.dnsName,
		include_in_default_search=True,
		required=True,
		identifies=True,
	),
	'zonettl': univention.admin.property(
		short_description=_('Time to live'),
		long_description=_('The time this entry may be cached.'),
		syntax=univention.admin.syntax.UNIX_TimeInterval,
		default=(('22', 'hours'), []),
		dontsearch=True,
	),
	'nameserver': univention.admin.property(
		short_description=_('Name servers'),
		long_description=_('The FQDNs of the hosts serving the named zone.'),
		syntax=univention.admin.syntax.dnsHostname,
		multivalue=True,
		required=True,
	)
}

layout = [
	Tab(_('General'), _('Basic values'), layout=[
		Group(_('General NS record settings'), layout=[
			'zone',
			'nameserver',
			'zonettl'
		]),
	]),
]

mapping = univention.admin.mapping.mapping()
mapping.register('zone', 'relativeDomainName', None, univention.admin.mapping.ListToString)
mapping.register('nameserver', 'nSRecord')
mapping.register('zonettl', 'dNSTTL', univention.admin.mapping.mapUNIX_TimeInterval, univention.admin.mapping.unmapUNIX_TimeInterval)


class object(univention.admin.handlers.simpleLdap):
	module = module

	def _updateZone(self):
		if self.update_zone:
			self.superordinate.open()
			self.superordinate.modify()

	def __init__(self, co, lo, position, dn='', superordinate=None, attributes=[], update_zone=True):
		self.update_zone = update_zone
		univention.admin.handlers.simpleLdap.__init__(self, co, lo, position, dn, superordinate, attributes=attributes)

	def _ldap_addlist(self):
		return [
			(self.superordinate.mapping.mapName('zone'), self.superordinate.mapping.mapValue('zone', self.superordinate['zone'])),
		]

	def _ldap_post_create(self):
		self._updateZone()

	def _ldap_post_modify(self):
		if self.hasChanged(self.descriptions.keys()):
			self._updateZone()

	def _ldap_post_remove(self):
		self._updateZone()


def lookup_filter(filter_s=None, superordinate=None):
	lookup_filter_obj = \
		univention.admin.filter.conjunction('&', [
			univention.admin.filter.expression('objectClass', 'dNSZone'),
			univention.admin.filter.expression('nSRecord', '*', escape=False),
			univention.admin.filter.conjunction('!', [
				univention.admin.filter.conjunction('|', [
					univention.admin.filter.expression('relativeDomainName', '@'),
					univention.admin.filter.expression('zoneName', '*.in-addr.arpa', escape=False),
				])
			])
		])

	if superordinate:
		parent = superordinate.mapping.mapValue('zone', superordinate['zone'])
		lookup_filter_obj.expressions.append(
			univention.admin.filter.expression('zoneName', parent, escape=True)
		)

	lookup_filter_obj.append_unmapped_filter_string(filter_s, univention.admin.mapping.mapRewrite, mapping)
	return lookup_filter_obj


def lookup(co, lo, filter_s, base='', superordinate=None, scope="sub", unique=False, required=False, timeout=-1, sizelimit=0, serverctrls=None, response=None):

	filter = lookup_filter(filter_s, superordinate)

	res = []
	for dn, attrs in lo.search(unicode(filter), base, scope, [], unique, required, timeout, sizelimit, serverctrls, response):
		res.append((object(co, lo, None, dn=dn, superordinate=superordinate, attributes=attrs)))
	return res


def identify(dn, attr, canonical=0):
	return all([
		'dNSZone' in attr.get('objectClass', []),
		'@' not in attr.get('relativeDomainName', []),
		not attr.get('zoneName', ['.in-addr.arpa'])[0].endswith('.in-addr.arpa'),
		attr.get('nSRecord', []),
		module in attr.get('univentionObjectType', [module]),
	])
