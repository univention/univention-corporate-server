#!/usr/bin/python3
# SPDX-FileCopyrightText: 2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
"""setup external management domain in keycloak for tests with delegated administration"""

import argparse
import json
import uuid

from keycloak import KeycloakAdmin

from univention.admin import modules, uldap
from univention.config_registry import ucr


# keycloak credentials
USERNAME = 'Administrator'
PASSWORD = 'univention'
SERVER_URL = ucr['ucs/server/sso/uri'].strip('/')

CLIENT_SECRET = 'LOcftoYscwZMOMPasSlygMvuxdUpCjqj'
CLIENT_ID = 'idp-client'
IDP_ALIAS = 'oidc'
IDP_DISPLAY_NAME = 'management domain'


def get_keycloak_session(realm):
    return KeycloakAdmin(
        server_url=SERVER_URL,
        username=USERNAME,
        password=PASSWORD,
        realm_name=realm,
        user_realm_name='master',
        verify=True,
    )


def create_oidc_client_external_keycloak():
    """
    create oidc client in master realm
    with mappers for preferred_username and nubus_roles
    """
    session = get_keycloak_session('master')
    client_payload = {
        'clientId': CLIENT_ID,
        'name': CLIENT_ID,
        'enabled': True,
        'clientAuthenticatorType': 'client-secret',
        'secret': CLIENT_SECRET,
        'redirectUris': ['https://*'],
        'webOrigins': ['https://*'],
        'consentRequired': False,
        'standardFlowEnabled': True,
        'directAccessGrantsEnabled': False,
        'frontchannelLogout': True,
        'protocol': 'openid-connect',
        'publicClient': False,
        'attributes': {
            'frontchannel.logout.session.required': 'false',
            'oauth2.device.authorization.grant.enabled': 'false',
            'backchannel.logout.revoke.offline.tokens': 'false',
            'use.refresh.tokens': 'true',
            'realm_client': 'false',
            'oidc.ciba.grant.enabled': 'false',
            'backchannel.logout.session.required': 'true',
            'client_credentials.use_refresh_token': 'false',
            'require.pushed.authorization.requests': 'false',
            'id.token.as.detached.signature': 'false',
            'client.secret.creation.time': '1661514856',
            'exclude.session.state.from.auth.response': 'false',
            'tls.client.certificate.bound.access.tokens': 'false',
            'acr.loa.map': '{}',
            'display.on.consent.screen': 'false',
            'token.response.type.bearer.lower-case': 'false',
        },
        'fullScopeAllowed': True,
        'protocolMappers': [
            {
                'name': 'username',
                'protocol': 'openid-connect',
                'protocolMapper': 'oidc-usermodel-property-mapper',
                'consentRequired': False,
                'config': {
                    'userinfo.token.claim': 'true',
                    'user.attribute': 'username',
                    'id.token.claim': 'true',
                    'access.token.claim': 'true',
                    'claim.name': 'preferred_username',
                    'jsonType.label': 'String',
                },
            },
            {
                'name': 'nubus_roles',
                'protocol': 'openid-connect',
                'protocolMapper': 'oidc-usermodel-attribute-mapper',
                'consentRequired': False,
                'config': {
                    'aggregate.attrs': 'false',
                    'introspection.token.claim': 'true',
                    'multivalued': 'true',
                    'userinfo.token.claim': 'true',
                    'user.attribute': 'nubus_roles',
                    'id.token.claim': 'false',
                    'lightweight.claim': 'false',
                    'access.token.claim': 'false',
                    'claim.name': 'nubus_roles',
                    'jsonType.label': 'String',
                },
            },
            {
                'name': 'nubus_id',
                'protocol': 'openid-connect',
                'protocolMapper': 'oidc-usermodel-attribute-mapper',
                'consentRequired': False,
                'config': {
                    'aggregate.attrs': 'false',
                    'introspection.token.claim': 'true',
                    'multivalued': 'false',
                    'userinfo.token.claim': 'true',
                    'user.attribute': 'nubus_id',
                    'id.token.claim': 'true',
                    'lightweight.claim': 'false',
                    'access.token.claim': 'true',
                    'claim.name': 'nubus_id',
                    'jsonType.label': 'String',
                },
            },

        ],
        'defaultClientScopes': ['web-origins', 'acr', 'roles', 'profile', 'basic', 'email'],
        'optionalClientScopes': ['address', 'phone', 'offline_access', 'microprofile-jwt'],
        'access': {'view': True, 'configure': True, 'manage': True},
    }
    session.create_client(client_payload, skip_exists=False)


def create_idp_in_ucs_keycloak():
    """
    create idp in ucs realm with mappers to
     * store nubus_roles from claim
     * stpre nubus_id from claim
     * hardcoded mapper to store nubus_federated_account=true
    """
    session = get_keycloak_session('ucs')
    idp_payload = {
        'alias': IDP_ALIAS,
        'displayName': IDP_DISPLAY_NAME,
        'providerId': 'oidc',
        'enabled': True,
        'updateProfileFirstLoginMode': 'off',
        'trustEmail': True,
        'config': {
            'tokenUrl': f'{SERVER_URL}/realms/master/protocol/openid-connect/token',
            'jwksUrl': f'{SERVER_URL}/realms/master/protocol/openid-connect/certs',
            'issuer': f'{SERVER_URL}/realms/master',
            'clientSecret': CLIENT_SECRET,
            'userInfoUrl': f'{SERVER_URL}/realms/master/protocol/openid-connect/userinfo',
            'validateSignature': 'true',
            'clientId': CLIENT_ID,
            'useJwksUrl': 'true',
            'metadataDescriptorUrl': f'{SERVER_URL}/realms/master/.well-known/openid-configuration',
            'authorizationUrl': f'{SERVER_URL}/realms/master/protocol/openid-connect/auth',
            'logoutUrl': f'{SERVER_URL}/realms/master/protocol/openid-connect/logout',
        },
    }
    session.create_idp(idp_payload)
    mappers = [
        {
            'name': 'nubus_federated_account',
            'identityProviderAlias': IDP_ALIAS,
            'identityProviderMapper': 'hardcoded-attribute-idp-mapper',
            'config': {'attribute.value': 'true', 'syncMode': 'INHERIT', 'attribute': 'nubus_federated_account'},
        },
        {
            'name': 'nubus_roles',
            'identityProviderAlias': IDP_ALIAS,
            'identityProviderMapper': 'oidc-user-attribute-idp-mapper',
            'config': {'syncMode': 'FORCE', 'claim': 'nubus_roles', 'user.attribute': 'nubus_roles'},
        },
        {
            'name': 'nubus_id',
            'identityProviderAlias': IDP_ALIAS,
            'identityProviderMapper': 'oidc-user-attribute-idp-mapper',
            'config': {'syncMode': 'FORCE', 'claim': 'nubus_id', 'user.attribute': 'nubus_id'},
        },
        {
            'name': 'nubus_external_username',
            'identityProviderAlias': IDP_ALIAS,
            'identityProviderMapper': 'oidc-user-attribute-idp-mapper',
            'config': {'syncMode': 'FORCE', 'claim': 'preferred_username', 'user.attribute': 'nubus_external_username'},
        },
    ]
    for mapper in mappers:
        session.add_mapper_to_idp(IDP_ALIAS, mapper)


def add_mappers_to_umc_oidc_client():
    """
    add mappers to UMC client to provide
     * nubus_roles
     * nubus_id
     * uid from user attr nubus_id
     * nubus_external_username
    """
    session = get_keycloak_session('ucs')
    mappers = [
        {
            'name': 'nubus-roles',
            'protocol': 'openid-connect',
            'protocolMapper': 'oidc-usermodel-attribute-mapper',
            'consentRequired': False,
            'config': {
                'introspection.token.claim': 'true',
                'userinfo.token.claim': 'true',
                'multivalued': 'true',
                'user.attribute': 'nubus_roles',
                'id.token.claim': 'false',
                'lightweight.claim': 'false',
                'access.token.claim': 'false',
                'claim.name': 'nubus_roles',
                'jsonType.label': 'String',
            },
        },
        {
            'name': 'nubus_id_to_uid',
            'protocol': 'openid-connect',
            'protocolMapper': 'oidc-usermodel-attribute-mapper',
            'consentRequired': False,
            'config': {
                'aggregate.attrs': 'false',
                'introspection.token.claim': 'true',
                'multivalued': 'false',
                'userinfo.token.claim': 'true',
                'user.attribute': 'nubus_id',
                'id.token.claim': 'true',
                'lightweight.claim': 'false',
                'access.token.claim': 'true',
                'claim.name': 'uid',
                'jsonType.label': 'String',
            },
        },
        {
            'name': 'nubus_id',
            'protocol': 'openid-connect',
            'protocolMapper': 'oidc-usermodel-attribute-mapper',
            'consentRequired': False,
            'config': {
                'introspection.token.claim': 'true',
                'userinfo.token.claim': 'true',
                'user.attribute': 'nubus_id',
                'id.token.claim': 'false',
                'lightweight.claim': 'false',
                'access.token.claim': 'false',
                'claim.name': 'nubus_id',
                'jsonType.label': 'String',
            },
        },
        {
            'name': 'nubus_federated_account',
            'protocol': 'openid-connect',
            'protocolMapper': 'oidc-usermodel-attribute-mapper',
            'consentRequired': False,
            'config': {
                'introspection.token.claim': 'true',
                'userinfo.token.claim': 'true',
                'user.attribute': 'nubus_federated_account',
                'id.token.claim': 'true',
                'lightweight.claim': 'false',
                'access.token.claim': 'true',
                'claim.name': 'nubus_federated_account',
                'jsonType.label': 'boolean',
            },
        },
    ]
    umc_client = 'https://{hostname}.{domainname}/univention/oidc/'.format(**ucr)
    umc_client_id = session.get_client_id(umc_client)
    for mapper in mappers:
        session.add_mapper_to_client(umc_client_id, mapper)


def _create_user(session, username, password, roles):
    user_payload = {
        'username': username,
        'firstName': username,
        'lastName': username,
        'email': f'{username}@test',
        'emailVerified': True,
        'enabled': True,
        'attributes': {
            'locale': ['en'],
            'nubus_roles': roles,
            'nubus_id': str(uuid.uuid4()),
        },
    }
    user_id = session.create_user(user_payload)
    session.set_user_password(user_id, password, temporary=False)


def create_user_profile():
    session = get_keycloak_session('ucs')
    resp = session.connection.raw_get('admin/realms/ucs/users/profile')
    profile = json.loads(resp.text)
    profile['attributes'].append(
        {
            'name': 'nubus_roles',
            'displayName': '${profile.attributes.nubus_roles}',
            'permissions': {'edit': ['admin'], 'view': ['admin']},
            'multivalued': True,
            'group': 'user-metadata',
        },
    )
    profile['attributes'].append(
        {
            'name': 'nubus_id',
            'displayName': '${profile.attributes.nubus_id}',
            'permissions': {'edit': ['admin'], 'view': ['admin']},
            'multivalued': False,
            'group': 'user-metadata',
        },
    )
    profile['attributes'].append(
        {
            'name': 'nubus_federated_account',
            'displayName': '${profile.attributes.nubus_federated_account}',
            'permissions': {'edit': ['admin'], 'view': ['admin']},
            'multivalued': False,
            'group': 'user-metadata',
        },
    )
    resp = session.connection.raw_put('admin/realms/ucs/users/profile', data=json.dumps(profile))
    assert resp.status_code == 200, resp.text


def create_users_external_keycloak():
    session = get_keycloak_session('master')
    # create user profile for ucs role and id attribute
    resp = session.connection.raw_get('admin/realms/master/users/profile')
    profile = json.loads(resp.text)
    profile['attributes'].append(
        {
            'name': 'nubus_roles',
            'displayName': '${profile.attributes.nubus_roles}',
            'permissions': {'edit': ['admin'], 'view': ['admin']},
            'multivalued': True,
            'group': 'user-metadata',
        },
    )
    profile['attributes'].append(
        {
            'name': 'nubus_id',
            'displayName': '${profile.attributes.nubus_id}',
            'permissions': {'edit': ['admin'], 'view': ['admin']},
            'multivalued': False,
            'group': 'user-metadata',
        },
    )
    resp = session.connection.raw_put('admin/realms/master/users/profile', data=json.dumps(profile))
    assert resp.status_code == 200, resp.text
    # create ouadmin, helpdesk-operator users and one domain admin user in external keycloak
    for i in range(1, 11):
        _create_user(session, f'manager-ou{i}', 'univention', [f'udm:default-roles:organizational-unit-admin&udm:contexts:position=ou=ou{i}'])
        _create_user(session, f'helpdesk-ou{i}', 'univention', [f'udm:default-roles:helpdesk-operator&udm:contexts:position=ou=ou{i}'])
    _create_user(session, 'manager-all', 'univention', ['udm:default-roles:domain-administrator'])


def create_federated_accounts_container():
    lo, position = uldap.getAdminConnection()
    modules.update()
    cns = modules.get('container/cn')
    umc_policies = modules.get('policies/umc')
    modules.init(lo, position, cns)
    modules.init(lo, position, umc_policies)
    ldap_base = ucr['ldap/base']
    position.setDn(f'cn=univention,{ldap_base}')
    cn = cns.object(None, lo, position)
    cn['name'] = 'federated_accounts'
    cn.create()

    # link some UMC policiy as long as we don't have guardianRoles support for UMC authz
    pol_dn = umc_policies.lookup(None, lo, 'cn=organizational-unit-admins', unique=True, required=True)[0].dn
    cn = cns.lookup(None, lo, 'cn=federated_accounts', unique=True, required=True)[0]
    cn.open()
    cn.policies = [pol_dn]
    cn.modify()


def main():
    create_oidc_client_external_keycloak()
    create_users_external_keycloak()
    create_idp_in_ucs_keycloak()
    add_mappers_to_umc_oidc_client()
    create_user_profile()
    create_federated_accounts_container()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    main()
