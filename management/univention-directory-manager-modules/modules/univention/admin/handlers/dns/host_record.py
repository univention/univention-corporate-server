# -*- coding: utf-8 -*-
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2004-2022 Univention GmbH
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

"""
|UDM| module for |DNS| host records
"""

import ipaddress

from univention.admin.layout import Tab, Group
import univention.admin.filter
import univention.admin.handlers
import univention.admin.handlers.dns.forward_zone
import univention.admin.localization

translation = univention.admin.localization.translation('univention.admin.handlers.dns')
_ = translation.translate

module = 'dns/host_record'
operations = ['add', 'edit', 'remove', 'search']
columns = ['a']
superordinate = 'dns/forward_zone'
childs = False
short_description = _('DNS: Host Record')
object_name = _('Host record')
object_name_plural = _('Host records')
long_description = _('Resolve the symbolic name to IP addresses.')
options = {
	'default': univention.admin.option(
		short_description=short_description,
		default=True,
		objectClasses=['top', 'dNSZone'],
	),
}
property_descriptions = {
	'name': univention.admin.property(
		short_description=_('Hostname'),
		long_description=_('The name of the host relative to the domain.'),
		syntax=univention.admin.syntax.dnsName,
		include_in_default_search=True,
		required=True,
		identifies=True
	),
	'zonettl': univention.admin.property(
		short_description=_('Time to live'),
		long_description=_('The time this entry may be cached.'),
		syntax=univention.admin.syntax.UNIX_TimeInterval,
		default=(('3', 'hours'), []),
		dontsearch=True,
	),
	'a': univention.admin.property(
		short_description=_('IP addresses'),
		long_description=_('One or more IP addresses, to which the name is resolved to.'),
		syntax=univention.admin.syntax.ipAddress,
		multivalue=True,
	),
	'mx': univention.admin.property(
		short_description=_('Mail exchanger host'),
		long_description=_('The FQDNs of the hosts responsible for receiving mail for this DNS name.'),
		syntax=univention.admin.syntax.dnsMX,
		multivalue=True,
		dontsearch=True,
	),
	'txt': univention.admin.property(
		short_description=_('Text Record'),
		long_description=_('One or more arbitrary text strings.'),
		syntax=univention.admin.syntax.string,
		multivalue=True,
	)
}

layout = [
	Tab(_('General'), _('Basic values'), layout=[
		Group(_('General host record settings'), layout=[
			'name',
			'a',
			'zonettl'
		]),
	]),
	Tab(_('Mail'), _('Mail exchangers for this host'), advanced=True, layout=[
		'mx'
	]),
	Tab(_('Text'), _('Optional text'), advanced=True, layout=[
		'txt',
	])
]


def unmapMX(old, encoding=()):
	new = []
	for i in old:
		new.append(i.decode(*encoding).split(u' ', 1))
	return new


def mapMX(old, encoding=()):
	new = []
	for i in old:
		new.append(u' '.join(i).encode(*encoding))
	return new


def unmapIPAddresses(values, encoding=()):
	records = []
	if 'aRecord' in values:
		records.extend([x.decode(*encoding) for x in values['aRecord']])
	if 'aAAARecord' in values:
		records.extend([ipaddress.IPv6Address(x.decode(*encoding)).exploded for x in values['aAAARecord']])
	return records


mapping = univention.admin.mapping.mapping()
mapping.register('name', 'relativeDomainName', None, univention.admin.mapping.ListToString, encoding='ASCII')
mapping.register('mx', 'mXRecord', mapMX, unmapMX, encoding='ASCII')
mapping.register('txt', 'tXTRecord', encoding='ASCII')
mapping.register('zonettl', 'dNSTTL', univention.admin.mapping.mapUNIX_TimeInterval, univention.admin.mapping.unmapUNIX_TimeInterval)
mapping.registerUnmapping('a', unmapIPAddresses, encoding='ASCII')


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
		return super(object, self)._ldap_addlist() + [
			(self.superordinate.mapping.mapName('zone'), self.superordinate.mapping.mapValue('zone', self.superordinate['zone'])),
		]

	def _ldap_modlist(self):  # IPv6
		ml = univention.admin.handlers.simpleLdap._ldap_modlist(self)
		oldAddresses = self.oldinfo.get('a')
		newAddresses = self.info.get('a')
		oldARecord = []
		newARecord = []
		oldAaaaRecord = []
		newAaaaRecord = []
		if oldAddresses != newAddresses:
			if oldAddresses:
				for address in oldAddresses:
					if u':' in address:  # IPv6
						oldAaaaRecord.append(address.encode('ASCII'))
					else:
						oldARecord.append(address.encode('ASCII'))
			if newAddresses:
				for address in newAddresses:
					if u':' in address:  # IPv6
						newAaaaRecord.append(address)
					else:
						newARecord.append(address.encode('ASCII'))

			# explode all IPv6 addresses and remove duplicates
			newAaaaRecord = {ipaddress.IPv6Address(u'%s' % (x,)).exploded for x in newAaaaRecord}
			newAaaaRecord = [x.encode('ASCII') for x in newAaaaRecord]

			ml.append(('aRecord', oldARecord, newARecord, ))
			ml.append(('aAAARecord', oldAaaaRecord, newAaaaRecord, ))
		return ml

	def _ldap_post_create(self):
		super(object, self)._ldap_post_create()
		self._updateZone()

	def _ldap_post_modify(self):
		super(object, self)._ldap_post_modify()
		if self.hasChanged(self.descriptions.keys()):
			self._updateZone()

	def _ldap_post_remove(self):
		super(object, self)._ldap_post_remove()
		self._updateZone()

	@classmethod
	def unmapped_lookup_filter(cls):
		return univention.admin.filter.conjunction('&', [
			univention.admin.filter.expression('objectClass', 'dNSZone'),
			univention.admin.filter.conjunction('!', [univention.admin.filter.expression('relativeDomainName', '@')]),
			univention.admin.filter.conjunction('!', [univention.admin.filter.expression('zoneName', '*.in-addr.arpa', escape=False)]),
			univention.admin.filter.conjunction('!', [univention.admin.filter.expression('zoneName', '*.ip6.arpa', escape=False)]),
			univention.admin.filter.conjunction('!', [univention.admin.filter.expression('cNAMERecord', '*', escape=False)]),
			univention.admin.filter.conjunction('!', [univention.admin.filter.expression('sRVRecord', '*', escape=False)]),
			univention.admin.filter.conjunction('|', [
				univention.admin.filter.expression('aRecord', '*', escape=False),
				univention.admin.filter.expression('aAAARecord', '*', escape=False),
				univention.admin.filter.expression('mXRecord', '*', escape=False),
				univention.admin.filter.expression('univentionObjectType', module, escape=True),  # host record without any record
			]),
		])

	@classmethod
	def lookup_filter_superordinate(cls, filter, superordinate):
		filter.expressions.append(univention.admin.filter.expression('zoneName', superordinate.mapping.mapValueDecoded('zone', superordinate['zone']), escape=True))
		return filter

	@classmethod
	def rewrite_filter(cls, filter, mapping):
		if filter.variable == 'a':
			filter.transform_to_conjunction(univention.admin.filter.conjunction('|', [
				univention.admin.filter.expression('aRecord', filter.value, escape=False),
				univention.admin.filter.expression('aAAARecord', filter.value, escape=False),
			]))
		else:
			return super(object, cls).rewrite_filter(filter, mapping)


lookup = object.lookup
lookup_filter = object.lookup_filter


def identify(dn, attr, canonical=False):
	mod = module.encode('ASCII')
	return all([
		b'dNSZone' in attr.get('objectClass', []),
		b'@' not in attr.get('relativeDomainName', []),
		not attr.get('zoneName', [b'.arpa'])[0].decode('UTF-8').endswith('.arpa'),
		not attr.get('cNAMERecord', []),
		not attr.get('sRVRecord', []),
		any(attr.get(a) for a in ('aRecord', 'aAAARecord', 'mXRecord')) or mod in attr.get('univentionObjectType', []),
		mod in attr.get('univentionObjectType', [mod])
	])
