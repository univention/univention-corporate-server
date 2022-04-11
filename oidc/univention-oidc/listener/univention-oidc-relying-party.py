# -*- coding: utf-8 -*-
#
# Univention OIDC
#  listener module: management of OIDC relying party
#
# Copyright 2022 Univention GmbH
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

from __future__ import absolute_import

import listener

import keycloak

from univention.config_registry import ucr

name = 'univention-oidc-relying-party'
description = 'Manage OIDC relying party'
filter = '(objectClass=univentionOIDCRelyingParty)'


@listener.SetUID(0)
def handler(dn, new, old):
	# type: (str, dict, dict) -> None

	kc_admin = keycloak.KeycloakAdmin(
		server_url='https://keycloak.%(hostname)s.%(domainname)s' % ucr,  # FIXME
		username='Administrator',  # FIXME
		password='univention',  # FIXME
		realm_name='ucs',  # FIXME
		user_realm_name='master',  # FIXME
		verify=True
	)

	if not new:
		remove_relying_party(kc_admin, old)
	else:
		replace_relying_party(kc_admin, dn, old, new)


def remove_relying_party(kc_admin, old):
	client_id = old['univentionOIDCClientID'][0].decode('UTF-8')
	kc_admin.delete_client(client_id)


def replace_relying_party(kc_admin, dn, old, new):
	# https://www.keycloak.org/docs-api/17.0/rest-api/index.html#_clientrepresentation
	payload = {
		# "id": None,
		"clientId": None,
		"name": None,
		"description": None,
		"baseUrl": None,
		"secret": None,
		"rootUrl": None,
		"surrogateAuthRequired": False,
		"enabled": True,
		"alwaysDisplayInConsole": False,
		"clientAuthenticatorType": "client-secret",
		"redirectUris": [],
		"webOrigins": [],
		"notBefore": 0,
		"bearerOnly": False,
		"consentRequired": False,
		"standardFlowEnabled": True,
		"implicitFlowEnabled": False,
		"directAccessGrantsEnabled": True,
		"serviceAccountsEnabled": True,
		"publicClient": False,
		"frontchannelLogout": False,
		"protocol": "openid-connect",
		"attributes": {
			"access.token.lifespan": "",
			"oauth2.device.authorization.grant.enabled": "false",
			"backchannel.logout.revoke.offline.tokens": "false",
			"use.refresh.tokens": "true",
			"oidc.ciba.grant.enabled": "false",
			"backchannel.logout.session.required": "true",
			"client_credentials.use_refresh_token": "false",
			"require.pushed.authorization.requests": "false",
			"id.token.as.detached.signature": "false",
			"exclude.session.state.from.auth.response": "false",
			"acr.loa.map": "{}",
			"tls.client.certificate.bound.access.tokens": "false",
			"display.on.consent.screen": "false",
			"token.response.type.bearer.lower-case": "false",
		},
		"authenticationFlowBindingOverrides": {},
		"fullScopeAllowed": True,
		"nodeReRegistrationTimeout": -1,
		"defaultClientScopes": [],
		"optionalClientScopes": [],
		"access": {
			"view": True,
			"configure": True,
			"manage": True
		},
		"authorizationServicesEnabled": True,
		"adminUrl": None,
		"origin": None,
		"protocolMappers": None,
		"registeredNodes": None,
		"registrationAccessToken": None,
	}

	client_id = new['univentionOIDCClientID'][0].decode('UTF-8')
	secret = new.get('univentionOIDCClientSecret', [b''])[0].decode('UTF-8') or None
	base_url = new.get('univentionOIDCBaseURL', [b''])[0].decode('UTF-8')
	scopes = [x.decode('UTF-8') for x in new['univentionOIDCClienScope']]
	optional_scopes = [x.decode('UTF-8') for x in new['univentionOIDCOptionalClientScope']]
	redirect_uris = [x.decode('UTF-8') for x in new['univentionOIDCRedirectURI']]
	access_token_lifespan = new.get('univentionOIDCAccessTokenLifespan', [b'300'])[0].decode('UTF-8')
	attributes = dict(x.decode('UTF-8').split(':', 1) for x in new.get('univentionOIDCKeycloakAttributes', []) if b':' in x)
	attributes["access.token.lifespan"] = access_token_lifespan
	internal_id = None
	if old and new:
		internal_id = kc_admin.get_client_id(client_id)
		payload = kc_admin.get_client(internal_id)

	payload.update({
		"clientId": client_id,
		"name": dn,
		"description": description,
		"secret": secret,
		"baseUrl": base_url,
		"redirectUris": redirect_uris,
		"defaultClientScopes": scopes,
		"optionalClientScopes": optional_scopes,
	})
	payload.setdefault('attributes', {}).update(attributes)

	if old and new:
		kc_admin.update_client(internal_id, payload)
	else:
		kc_admin.create_client(payload=payload, skip_exists=True)


if __name__ == '__main__':
	import logging
	import univention.uldap
	logging.basicConfig(level=logging.DEBUG)
	lo = univention.uldap.getAdminConnection()
	dn, new = lo.search('univentionObjectType=oidc/relyingparty')[0]
	handler(dn, new, {})
	handler(dn, new, new)
