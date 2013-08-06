#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Copyright 2013 Univention GmbH
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
import univention.admin.syntax

translation = univention.admin.localization.translation('univention.admin.handlers.saml')
_ = translation.translate

module = 'saml/serviceprovider'
#superordinate='settings/cn'
childs = 0
short_description = _(u'saml service provider')
long_description = _(u'SAML service provider and their settings')
operations = ['add', 'edit', 'remove', 'search']

options = {
}

property_descriptions = {
	'Identifier': univention.admin.property(
			short_description = _(u'Identifier'),
			long_description = _(u'Unique identifier for the service provider definition'),
			syntax = univention.admin.syntax.string,
			multivalue = False,
			options = [],
			required = True,
			may_change = True,
			identifies = True,
		),
	'AssertionConsumerService': univention.admin.property(
			short_description = _(u'AssertionConsumerService'),
			long_description = _(u'The URL of the AssertionConsumerService endpoint for this SP'),
			syntax = univention.admin.syntax.string,
			multivalue = False,
			options = [],
			required = True,
			may_change = True,
			identifies = True,
		),
	'NameIDFormat': univention.admin.property(
			short_description = _(u'NameIDFormat'),
			long_description = _(u'The NameIDFormat this SP should receive'),
			syntax = univention.admin.syntax.string,
			multivalue = False,
			options = [],
			required = False,
			may_change = True,
			identifies = True,
		),
	'simplesamlNameIDAttribute': univention.admin.property(
			short_description = _(u'simplesamlNameIDAttribute'),
			long_description = _(u'The name of the attribute which should be used as the value of the NameID'),
			syntax = univention.admin.syntax.string,
			multivalue = False,
			options = [],
			required = False,
			may_change = True,
			identifies = True,
		),
	'simplesamlAttributes': univention.admin.property(
			short_description = _(u'simplesamlAttributes'),
			long_description = _(u'Whether the SP should receive any attributes from the IdP'),
			syntax = univention.admin.syntax.string,
			multivalue = False,
			options = [],
			required = False,
			may_change = True,
			identifies = True,
		),
}

layout = [
	Tab(_(u'General'), _(u'Basic Settings'), layout=[
		Group(_('Definition'), layout=[
			["Identifier", ],
			["AssertionConsumerService", ],
			["NameIDFormat", ],
			["simplesamlNameIDAttribute", ],
			["simplesamlAttributes", ],
		]),
	])
]

mapping = univention.admin.mapping.mapping()
mapping.register('Identifier', 'SAMLServiceProviderIdentifier', None, univention.admin.mapping.ListToString)
mapping.register('AssertionConsumerService', 'AssertionConsumerService', None, univention.admin.mapping.ListToString)
mapping.register('NameIDFormat', 'NameIDFormat', None, univention.admin.mapping.ListToString)
mapping.register('simplesamlNameIDAttribute', 'simplesamlNameIDAttribute', None, univention.admin.mapping.ListToString)
mapping.register('simplesamlAttributes', 'simplesamlAttributes', None, univention.admin.mapping.ListToString)

class object(univention.admin.handlers.simpleLdap):
	module = module

	def __init__(self, co, lo, position, dn='', superordinate=None, attributes=None):
		self.co = co
		self.lo = lo
		self.dn = dn
		self.position = position
		self.mapping = mapping
		self.descriptions = property_descriptions
		univention.admin.handlers.simpleLdap.__init__(self, co, lo, position, dn, superordinate)
		self.options = []

	def open(self):
		univention.admin.handlers.simpleLdap.open(self)
		self.save()

	def _ldap_pre_create(self):
		self.dn = '%s=%s,%s' % (mapping.mapName('Identifier'), mapping.mapValue('Identifier', self.info['Identifier']), self.position.getDn())

	def _ldap_post_create(self):
		pass

	def _ldap_pre_modify(self):
		pass

	def _ldap_post_modify(self):
		pass

	def _ldap_pre_remove(self):
		pass

	def _ldap_post_remove(self):
		pass

	def _update_policies(self):
		pass

	def _ldap_addlist(self):
		al = [('objectClass', ['top', 'univentionSAMLServiceProvider' ])]
		return al

def lookup(co, lo, filter_s, base='', superordinate=None, scope='sub', unique=0, required=0, timeout=-1, sizelimit=0):
	searchfilter = univention.admin.filter.conjunction('&', [
				univention.admin.filter.expression('objectClass', 'univentionSAMLServiceProvider'),
				])

	if filter_s:
		filter_p = univention.admin.filter.parse(filter_s)
		univention.admin.filter.walk(filter_p, univention.admin.mapping.mapRewrite, arg=mapping)
		searchfilter.expressions.append(filter_p)

	res = []
	for dn in lo.searchDn(unicode(searchfilter), base, scope, unique, required, timeout, sizelimit):
		res.append(object(co, lo, None, dn))
	return res

def identify(distinguished_name, attributes, canonical=False):
	return 'univentionSAMLServiceProvider' in attributes.get('objectClass', [])
