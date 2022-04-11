# -*- coding: utf-8 -*-
#
# Copyright 2022 Univention GmbH
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
import univention.admin.handlers
import univention.admin.syntax

translation = univention.admin.localization.translation('univention.admin.handlers.oidc')
_ = translation.translate

module = 'oidc/relyingparty'
childs = False
short_description = _('OpenID Connect relying party')
long_description = _('Management of OpenID provider relying parties')
operations = ['add', 'edit', 'remove', 'search', 'move']
default_containers = ["cn=oidc-relying-parties,cn=univention"]
help_text = long_description

options = {
	'default': univention.admin.option(
		short_description=short_description,
		default=True,
		objectClasses=['top', 'univentionOIDCRelyingParty'],
	)
}

property_descriptions = {
	'name': univention.admin.property(
		short_description=_('Name'),
		long_description=_('Name of the service that connects to this configuration.'),
		syntax=univention.admin.syntax.string,
		required=True,
		identifies=True,
	),
	'description': univention.admin.property(
		short_description=_('Description'),
		long_description='',
		syntax=univention.admin.syntax.string,
	),
	'clientid': univention.admin.property(
		short_description=_('Client ID identifier'),
		long_description='',
		syntax=univention.admin.syntax.string,
		required=True,
	),
	'clientsecret': univention.admin.property(
		short_description=_('Client secret'),
		long_description='',
		syntax=univention.admin.syntax.passwd,
	),
	'baseurl': univention.admin.property(
		short_description=_('Base URL'),
		long_description='',
		syntax=univention.admin.syntax.string,
	),
	'clientscope': univention.admin.property(
		short_description=_('Client scopes'),
		long_description='',
		syntax=univention.admin.syntax.string,
		multivalue=True,
	),
	'optionalclientscope': univention.admin.property(
		short_description=_('Optional Client scopes'),
		long_description='',
		syntax=univention.admin.syntax.string,
		multivalue=True,
	),
	'redirectURI': univention.admin.property(
		short_description=_('Allowed redirect URI'),
		long_description='',
		syntax=univention.admin.syntax.FiveThirdsString,
		multivalue=True,
	),
	'accesstokenlifespan': univention.admin.property(
		short_description=_('Access token lifespan'),
		long_description=_('in seconds'),
		syntax=univention.admin.syntax.integer,
	),
	'keycloakAttributes': univention.admin.property(
		short_description=_('Additional keycloak attributes'),
		long_description='',
		syntax=univention.admin.syntax.keyAndValue,
		multivalue=True,
		#default=([
		#	("oauth2.device.authorization.grant.enabled", "false"),
		#	("backchannel.logout.revoke.offline.tokens", "false"),
		#	("use.refresh.tokens", "true"),
		#	("oidc.ciba.grant.enabled", "false"),
		#	("backchannel.logout.session.required", "true"),
		#	("client_credentials.use_refresh_token", "false"),
		#	("require.pushed.authorization.requests", "false"),
		#	("id.token.as.detached.signature", "false"),
		#	("exclude.session.state.from.auth.response", "false"),
		#	("acr.loa.map", "{}"),
		#	("tls.client.certificate.bound.access.tokens", "false"),
		#	("display.on.consent.screen", "false"),
		#	("token.response.type.bearer.lower-case", "false"),
		#], []),
	),
}

layout = [
	Tab(_('General'), _('Basic Settings'), layout=[
		Group(_('OIDC service settings'), layout=[
			["name", "description"],
			["baseurl", ],
			["clientid", ],
			["clientsecret", ],
			["clientscope", ],
			["optionalclientscope", ],
			["redirectURI", ],
			["accesstokenlifespan", ],
			["keycloakAttributes", ],
		]),
	]),
]


def map_keycloak_attributes(value, encoding=()):
	return [':'.join(val).encode(*encoding) for val in value]


def unmap_keycloak_attributes(value, encoding=()):
	return [val.decode(*encoding).split(':', 1) for val in value]


mapping = univention.admin.mapping.mapping()
mapping.register('name', 'cn', None, univention.admin.mapping.ListToString)
mapping.register('clientid', 'univentionOIDCClientID', None, univention.admin.mapping.ListToString)
mapping.register('clientsecret', 'univentionOIDCClientSecret', None, univention.admin.mapping.ListToString)
mapping.register('baseurl', 'univentionOIDCBaseURL', None, univention.admin.mapping.ListToString)
mapping.register('clientscope', 'univentionOIDCClienScope')
mapping.register('optionalclientscope', 'univentionOIDCOptionalClientScope')
mapping.register('redirectURI', 'univentionOIDCRedirectURI')
mapping.register('accesstokenlifespan', 'univentionOIDCAccessTokenLifespan', None, univention.admin.mapping.ListToString)
mapping.register('keycloakAttributes', 'univentionOIDCKeycloakAttributes', map_keycloak_attributes, unmap_keycloak_attributes)


class object(univention.admin.handlers.simpleLdap):
	module = module


identify = object.identify
lookup = object.lookup
lookup_filter = object.lookup_filter
