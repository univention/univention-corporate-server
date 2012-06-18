# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  admin module for the DHCP hosts
#
# Copyright 2004-2012 Univention GmbH
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
import univention.debug

translation=univention.admin.localization.translation('univention.admin.handlers.dhcp')
_=translation.translate

module='dhcp/host'
operations=['add','edit','remove','search']
superordinate='dhcp/service'
childs=0
usewizard=1
short_description=_('DHCP: Host')
long_description=''
options={
}
property_descriptions={
	'host':  univention.admin.property(
			short_description=_('Hostname'),
			long_description='',
			syntax=univention.admin.syntax.string,
			multivalue=0,
			options=[],
			required=1,
			may_change=1,
			identifies=1
		),
	'hwaddress': univention.admin.property(
			short_description=_('Hardware address'),
			long_description=_('Currently, only the ethernet and token-ring types are recognized. \
The hardware-address should be a set of hexadecimal octets (numbers from 0 through ff) separated by colons.'),
			syntax=univention.admin.syntax.DHCP_HardwareAddress,
			multivalue=0,
			options=[],
			required=1,
			may_change=1,
			identifies=0
		),
	'fixedaddress': univention.admin.property(
			short_description=_('Fixed IP addresses'),
			long_description=_('Assign one or more fixed IP addresses. \
Each address should be either an IP address or a domain name that resolves to one or more IP addresses'),
			syntax=univention.admin.syntax.string,
			multivalue=1,
			options=[],
			required=0,
			may_change=1,
			identifies=0
		),
}
layout=[
	Tab( _('General'), _('Basic settings'), layout = [
		Group( _( 'General' ), layout = [
			'host',
			'hwaddress',
			'fixedaddress'
		] ),
	] )
]

def unmapHWAddress(old):
	univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'host.py: unmapHWAddress: old: %s' % old)
	if not old:
		return ['', '']
	return old[0].split(' ')

def mapHWAddress(old):
	univention.debug.debug(univention.debug.ADMIN, univention.debug.INFO, 'host.py: mapHWAddress: old: %s' % old)
	if not old[0]:
		return ''
	else:
		if len (old) > 1:
			return '%s %s' % (old[0], old[1])
		else:
			return old

mapping=univention.admin.mapping.mapping()
mapping.register('host', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('hwaddress', 'dhcpHWAddress', mapHWAddress, unmapHWAddress)
mapping.register('fixedaddress', 'univentionDhcpFixedAddress')

class object(univention.admin.handlers.simpleLdap):
	module=module

	def __init__(self, co, lo, position, dn='', superordinate=None, attributes = [] ):
		global mapping
		global property_descriptions

		self.mapping=mapping
		self.descriptions=property_descriptions

		if not superordinate:
			raise univention.admin.uexceptions.insufficientInformation, 'superordinate object not present'
		if not dn and not position:
			raise univention.admin.uexceptions.insufficientInformation, 'neither dn nor position present'

		univention.admin.handlers.simpleLdap.__init__(self, co, lo, position, dn, superordinate, attributes = attributes )

	def _ldap_pre_create(self):
		self.dn='%s=%s,%s' % (mapping.mapName('host'), mapping.mapValue('host', self.info['host']), self.position.getDn())

	def _ldap_addlist(self):
		return [
			('objectClass', ['top', 'univentionDhcpHost']),
		]

def lookup(co, lo, filter_s, base='', superordinate=None, scope='sub', unique=0, required=0, timeout=-1, sizelimit=0):

	filter=univention.admin.filter.conjunction('&', [
	univention.admin.filter.expression('objectClass', 'univentionDhcpHost')
	])

	if filter_s:
		filter_p=univention.admin.filter.parse(filter_s)
		univention.admin.filter.walk(filter_p, univention.admin.mapping.mapRewrite, arg=mapping)
		filter.expressions.append(filter_p)

	res=[]
	for dn, attrs in lo.search(unicode(filter), base, scope, [], unique, required, timeout, sizelimit):
		res.append((object(co, lo, None, dn=dn, superordinate=superordinate, attributes = attrs )))
	return res

def identify(dn, attr):

	return 'univentionDhcpHost' in attr.get('objectClass', [])
