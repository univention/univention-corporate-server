# -*- coding: utf-8 -*-
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
import univention.admin.handlers
import univention.admin.syntax

translation = univention.admin.localization.translation('univention.admin.handlers.saml-serviceprovider')
_ = translation.translate

module = 'saml/idpconfig'
childs = False
short_description = _(u'SAML IdP configuration')
object_name = _(u'SAML IdP configuration')
object_name_plural = _(u'SAML IdP configurations')
long_description = _(u'univention simplesamlphp identity provider settings')
operations = ['add', 'edit', 'remove', 'search']
default_containers = ["cn=univention"]
help_text = _(u'You can download the public certificate for this identity provider at %s.') % ('<a href="/simplesamlphp/saml2/idp/certificate" target="_blank">/simplesamlphp/saml2/idp/certificate</a>',)

options = {
	'default': univention.admin.option(
		short_description='',
		default=True,
		objectClasses=['top', 'univentionSAMLIdpConfig'],
	),
}

property_descriptions = {
	'id': univention.admin.property(
		short_description=_(u'Config object identifier'),
		long_description=_(u'IdP config object identifier'),
		syntax=univention.admin.syntax.string,
		required=True,
		may_change=False,
		identifies=True,
	),
	'LdapGetAttributes': univention.admin.property(
		short_description=_(u'LDAP attribute name'),
		long_description=_(u'A list of ldap attribute names that the IdP is allowed to fetch from LDAP'),
		syntax=univention.admin.syntax.string,
		multivalue=True,
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


lookup = object.lookup
identify = object.identify
