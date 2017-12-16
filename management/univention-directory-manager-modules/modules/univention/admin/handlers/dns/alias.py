# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  admin module for the DNS aliases
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

import re
import string
from ldap.filter import filter_format

from univention.admin.layout import Tab, Group
import univention.admin.filter
import univention.admin.handlers
import univention.admin.handlers.dns.forward_zone
import univention.admin.localization
from univention.admin.handlers.dns import stripDot

translation = univention.admin.localization.translation('univention.admin.handlers.dns')
_ = translation.translate

module = 'dns/alias'
operations = ['add', 'edit', 'remove', 'search']
columns = ['cname']
superordinate = 'dns/forward_zone'
childs = 0
short_description = _('DNS: Alias record')
long_description = _('Assign additional names to a host.')
options = {
	'default': univention.admin.option(
		default=True,
		objectClasses=['top', 'dNSZone'],
	),
}
property_descriptions = {
	'name': univention.admin.property(
		short_description=_('Alias'),
		long_description=_('The name of the entry relative to the domain.'),
		syntax=univention.admin.syntax.dnsName,
		multivalue=False,
		include_in_default_search=True,
		options=[],
		required=True,
		may_change=True,
		identifies=True
	),
	'zonettl': univention.admin.property(
		short_description=_('Time to live'),
		long_description=_('The time this entry may be cached.'),
		syntax=univention.admin.syntax.UNIX_TimeInterval,
		multivalue=False,
		options=[],
		required=False,
		may_change=True,
		identifies=False,
		default=(('3', 'hours'), [])
	),
	'cname': univention.admin.property(
		short_description=_('Canonical name'),
		long_description=_("The name this alias points to. A FQDN must end with a dot."),
		syntax=univention.admin.syntax.dnsName,
		multivalue=False,
		include_in_default_search=True,
		options=[],
		required=True,
		may_change=True
	)
}

layout = [
	Tab(_('General'), _('Basic settings'), layout=[
		Group(_('General alias record settings'), layout=[
			'name',
			'zonettl',
			'cname'
		]),
	])
]


mapping = univention.admin.mapping.mapping()
mapping.register('name', 'relativeDomainName', stripDot, univention.admin.mapping.ListToString)
mapping.register('cname', 'cNAMERecord', None, univention.admin.mapping.ListToString)
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


def lookup(co, lo, filter_s, base='', superordinate=None, scope="sub", unique=False, required=False, timeout=-1, sizelimit=0):

	filter = univention.admin.filter.conjunction('&', [
		univention.admin.filter.expression('objectClass', 'dNSZone'),
		univention.admin.filter.conjunction('!', [univention.admin.filter.expression('relativeDomainName', '@')]),
		univention.admin.filter.conjunction('!', [univention.admin.filter.expression('zoneName', '*.in-addr.arpa')]),
		univention.admin.filter.conjunction('!', [univention.admin.filter.expression('aRecord', '*')]),
		univention.admin.filter.conjunction('!', [univention.admin.filter.expression('zoneName', '*.ip6.arpa')]),
		univention.admin.filter.conjunction('!', [univention.admin.filter.expression('aAAARecord', '*')]),
		univention.admin.filter.expression('cNAMERecord', '*')
	])

	if superordinate:
		filter.expressions.append(univention.admin.filter.expression('zoneName', superordinate.mapping.mapValue('zone', superordinate['zone']), escape=True))

	if filter_s:
		filter_p = univention.admin.filter.parse(filter_s)
		univention.admin.filter.walk(filter_p, univention.admin.mapping.mapRewrite, arg=mapping)
		filter.expressions.append(filter_p)

	res = []
	for dn, attrs in lo.search(unicode(filter), base, scope, [], unique, required, timeout, sizelimit):
		res.append((object(co, lo, None, dn=dn, superordinate=superordinate, attributes=attrs)))
	return res


def identify(dn, attr, canonical=0):
	return 'dNSZone' in attr.get('objectClass', []) and '@' not in attr.get('relativeDomainName', []) and \
		not attr['zoneName'][0].endswith('.in-addr.arpa') and not attr['zoneName'][0].endswith('.ip6.arpa') and attr.get('cNAMERecord', []) and not attr.get('aRecord', []) and not attr.get('aAAARecord', [])


def lookup_alias_filter(lo, filter_s):
	_re = re.compile('(.*)\(dnsAlias=([^=,]+)\)(.*)')
	match = _re.match(str(filter_s))
	filterlist = []
	if match:
		filter_p = univention.admin.filter.parse('name=%s' % match.group(2))
		univention.admin.filter.walk(filter_p, univention.admin.mapping.mapRewrite, arg=mapping)  # map property to ldap attribute
		alias_filter = univention.admin.filter.conjunction('&', [		# from dns/alias.lookup
			univention.admin.filter.expression('objectClass', 'dNSZone'),
			univention.admin.filter.conjunction('!', [univention.admin.filter.expression('relativeDomainName', '@')]),
			univention.admin.filter.conjunction('!', [univention.admin.filter.expression('zoneName', '*.in-addr.arpa')]),
			univention.admin.filter.expression('CNAMERecord', '*')
		])
		alias_filter.expressions.append(filter_p)
		alias_filter_s = unicode(alias_filter)
		alias_base = unicode(lo.base)					# std dns container might be a better choice
		for dn, attrs in lo.search(base=alias_base, scope='sub', filter=alias_filter_s, attr=['cNAMERecord']):
			cname = attrs['cNAMERecord'][0]
			cn_filter = filter_format('(cn=%s)', [cname.split('.', 1)[0]])
			if cn_filter not in filterlist:
				filterlist.append(cn_filter)
		if len(filterlist) > 0:
			return match.group(1) + '(|' + string.join(filterlist, '') + ')' + match.group(3)
		else:
			return ''
	else:
		return filter_s
