# -*- coding: utf-8 -*-
#
# Copyright 2013-2019 Univention GmbH
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

module = 'saml/serviceprovider'
childs = False
short_description = _(u'SAML service provider')
object_name = _(u'SAML service provider')
object_name_plural = _(u'SAML service providers')
long_description = _(u'Management of service provider configurations for the SAML identity provider.')
operations = ['add', 'edit', 'remove', 'search']
default_containers = ["cn=saml-serviceprovider,cn=univention"]
help_text = _(u'You can download the public certificate for this identity provider at %s.') % ('<a href="/simplesamlphp/saml2/idp/certificate" target="_blank">/simplesamlphp/saml2/idp/certificate</a>',)

options = {
	'default': univention.admin.option(
		short_description='',
		default=True,
		objectClasses=['top', 'univentionSAMLServiceProvider'],
	),
}

property_descriptions = {
	'isActivated': univention.admin.property(
		short_description=_(u'Service provider activation status'),
		long_description=_(u'Defines if this service provider is activated, i.e., its configuration is loaded'),
		syntax=univention.admin.syntax.TrueFalseUp,
		default="FALSE",
		size='Two',
	),
	'Identifier': univention.admin.property(
		short_description=_(u'Service provider identifier'),
		long_description=_(u'Unique identifier for the service provider definition. With this string the service provider identifies itself at the identity provider'),
		syntax=univention.admin.syntax.FiveThirdsString,
		required=True,
		may_change=False,
		identifies=True,
	),
	'AssertionConsumerService': univention.admin.property(
		short_description=_(u'Respond to this service provider URL after login'),
		long_description=_(u'The URL(s) of the AssertionConsumerService endpoints for this SP. Users will be redirected to the URL upon successful authentication. Example: https://sp.example.com/login'),
		syntax=univention.admin.syntax.FiveThirdsString,
		multivalue=True,
		required=True,
	),
	'NameIDFormat': univention.admin.property(
		short_description=_(u'Format of NameID attribute'),
		long_description=_(u'The NameIDFormat the service provider receives. The service provider documentation should mention expected formats. Example: urn:oasis:names:tc:SAML:2.0:nameid-format:transient'),
		syntax=univention.admin.syntax.FiveThirdsString,
	),
	'simplesamlNameIDAttribute': univention.admin.property(
		short_description=_(u'Name of the attribute that is used as NameID'),
		long_description=_(u'The name of the attribute which should be used as the value of the NameID, e.g. uid'),
		syntax=univention.admin.syntax.FiveThirdsString,
		default="uid"
	),
	'simplesamlAttributes': univention.admin.property(
		short_description=_(u'Allow transmission of ldap attributes to the service provider'),
		long_description=_(u'Whether the service provider should receive any ldap attributes from the IdP'),
		syntax=univention.admin.syntax.TrueFalseUp,
		default="FALSE",
		size='Two',
	),
	'LDAPattributes': univention.admin.property(
		short_description=_(u'List of ldap attributes to transmit'),
		long_description=_(u'A list of ldap attributes that are transmitted to the service provider'),
		syntax=univention.admin.syntax.FiveThirdsString,
		multivalue=True,
	),
	'serviceproviderdescription': univention.admin.property(
		short_description=_(u'Description of this service provider'),
		long_description=_(u'A description of this service provider that can be shown to users'),
		syntax=univention.admin.syntax.FiveThirdsString,
	),
	'serviceProviderOrganizationName': univention.admin.property(
		short_description=_(u'Name of the organization for this service provider'),
		long_description=_(u'The name of the organization responsible for the service provider that can be shown to users'),
		syntax=univention.admin.syntax.FiveThirdsString,
	),
	'privacypolicyURL': univention.admin.property(
		short_description=_(u'URL to the service provider\'s privacy policy'),
		long_description=_(u'An absolute URL for the service provider\'s privacy policy, which will be shown on the consent page'),
		syntax=univention.admin.syntax.FiveThirdsString,
	),
	'attributesNameFormat': univention.admin.property(
		short_description=_(u'Value for attribute format field'),
		long_description=_(u'Which value will be set in the format field of attribute statements. Default: urn:oasis:names:tc:SAML:2.0:attrname-format:basic'),
		syntax=univention.admin.syntax.FiveThirdsString,
	),
	'singleLogoutService': univention.admin.property(
		short_description=_(u'Single logout URL for this service provider'),
		long_description=_(u'The URL of the SingleLogoutService endpoint for this service provider'),
		syntax=univention.admin.syntax.FiveThirdsString,
	),
	'serviceProviderMetadata': univention.admin.property(
		short_description=_('XML metadata'),
		long_description=_('Raw XML metadata of the service provider to extend the simplesamlphp configuration.'),
		syntax=univention.admin.syntax.string,
		dontsearch=True,
	),
	'rawsimplesamlSPconfig': univention.admin.property(
		short_description=_('raw simplesaml SP config'),
		long_description=_('A raw simplesamlphp service provider configuration.'),
		syntax=univention.admin.syntax.string,
		dontsearch=True,
	),
}

layout = [
	Tab(_(u'General'), _(u'Basic Settings'), layout=[
		Group(_('SAML service provider basic settings'), layout=[
			["isActivated", ],
			["Identifier", ],
			["AssertionConsumerService", ],
			["singleLogoutService", ],
			["NameIDFormat", ],
			["simplesamlNameIDAttribute", ],
			["serviceProviderOrganizationName", ],
			["serviceproviderdescription", ],
		]),
	]),
	Tab(_(u'Extended Settings'), _(u'Additional configuration options'), layout=[
		Group(_('Extended Settings'), layout=[
			["privacypolicyURL"],
			["simplesamlAttributes", ],
			["attributesNameFormat", ],
			["LDAPattributes", ],
		]),
	]),
]

mapping = univention.admin.mapping.mapping()
mapping.register('isActivated', 'isServiceProviderActivated', None, univention.admin.mapping.ListToString)
mapping.register('Identifier', 'SAMLServiceProviderIdentifier', None, univention.admin.mapping.ListToString)
mapping.register('AssertionConsumerService', 'AssertionConsumerService')
mapping.register('NameIDFormat', 'NameIDFormat', None, univention.admin.mapping.ListToString)
mapping.register('simplesamlNameIDAttribute', 'simplesamlNameIDAttribute', None, univention.admin.mapping.ListToString)
mapping.register('simplesamlAttributes', 'simplesamlAttributes', None, univention.admin.mapping.ListToString)
mapping.register('LDAPattributes', 'simplesamlLDAPattributes')
mapping.register('serviceproviderdescription', 'serviceproviderdescription', None, univention.admin.mapping.ListToString)
mapping.register('serviceProviderOrganizationName', 'serviceProviderOrganizationName', None, univention.admin.mapping.ListToString)
mapping.register('privacypolicyURL', 'privacypolicyURL', None, univention.admin.mapping.ListToString)
mapping.register('attributesNameFormat', 'attributesNameFormat', None, univention.admin.mapping.ListToString)
mapping.register('singleLogoutService', 'singleLogoutService', None, univention.admin.mapping.ListToString)
mapping.register('serviceProviderMetadata', 'serviceProviderMetadata', None, univention.admin.mapping.ListToString)
mapping.register('rawsimplesamlSPconfig', 'rawsimplesamlSPconfig', None, univention.admin.mapping.ListToString)


class object(univention.admin.handlers.simpleLdap):
	module = module


lookup = object.lookup
identify = object.identify
