# -*- coding: utf-8 -*-
#
# Copyright 2018 Univention GmbH
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

translation = univention.admin.localization.translation('univention.admin.handlers.saml-serviceprovider')
_ = translation.translate

module = 'saml/idpconfig'
childs = 0
short_description = _(u'SAML IdP configuration')
long_description = _(u'univention simplesamlphp identity provider settings')
operations = ['add', 'edit', 'remove', 'search']
default_containers = ["cn=univention"]
help_text = _(u'You can download the public certificate for this identity provider at %s.') % ('<a href="/simplesamlphp/saml2/idp/certificate" target="_blank">/simplesamlphp/saml2/idp/certificate</a>',)

options = {}

property_descriptions = {
	'id': univention.admin.property(
		short_description=_(u'Config object identifier'),
		long_description=_(u'IdP config object identifier'),
		syntax=univention.admin.syntax.string,
		multivalue=False,
		options=[],
		required=True,
		may_change=False,
		identifies=True,
	),
	'LdapGetAttributes': univention.admin.property(
		short_description=_(u'LDAP attribute name'),
		long_description=_(u'A list of ldap attribute names that the IdP is allowed to fetch from LDAP'),
		syntax=univention.admin.syntax.string,
		multivalue=True,
		options=[],
		required=False,
		may_change=True,
		identifies=False,
	),
}

layout = [
	Tab(_(u'General'), _(u'Settings'), layout=[
		Group(_('SAML identity provider settings'), layout=[
			["id", ],
			["LdapGetAttributes", ],
		]),
	]),
]

mapping = univention.admin.mapping.mapping()
mapping.register('id', 'id', None, univention.admin.mapping.ListToString)
mapping.register('LdapGetAttributes', 'LdapGetAttributes', None, None)


class object(univention.admin.handlers.simpleLdap):
	module = module

	def _ldap_addlist(self):
		al = [('objectClass', ['top', 'univentionSAMLIdpConfig'])]
		return al


def lookup(co, lo, filter_s, base='', superordinate=None, scope='sub', unique=False, required=False, timeout=-1, sizelimit=0):
	searchfilter = univention.admin.filter.conjunction('&', [
		univention.admin.filter.expression('objectClass', 'univentionSAMLIdpConfig'),
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
	return 'univentionSAMLIdpConfig' in attributes.get('objectClass', [])
