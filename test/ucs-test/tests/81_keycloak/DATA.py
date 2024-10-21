#!/usr/bin/python3

O365CLIENT = {'id': '8478536d-6933-4e38-af96-cbe220f268bb', 'clientId': 'urn:federation:MicrosoftOnline', 'surrogateAuthRequired': False, 'enabled': True, 'alwaysDisplayInConsole': False, 'clientAuthenticatorType': 'client-secret', 'redirectUris': ['https://login.microsoftonline.com/login.srf'], 'webOrigins': [], 'notBefore': 0, 'bearerOnly': False, 'consentRequired': False, 'standardFlowEnabled': True, 'implicitFlowEnabled': False, 'directAccessGrantsEnabled': True, 'serviceAccountsEnabled': False, 'publicClient': True, 'frontchannelLogout': True, 'protocol': 'saml', 'attributes': {'saml.multivalued.roles': 'false', 'saml.force.post.binding': 'true', 'post.logout.redirect.uris': '+', 'oauth2.device.authorization.grant.enabled': 'false', 'backchannel.logout.revoke.offline.tokens': 'false', 'saml.server.signature.keyinfo.ext': 'false', 'use.refresh.tokens': 'true', 'oidc.ciba.grant.enabled': 'false', 'backchannel.logout.session.required': 'true', 'client_credentials.use_refresh_token': 'false', 'saml.signature.algorithm': 'RSA_SHA256', 'saml.client.signature': 'false', 'require.pushed.authorization.requests': 'false', 'saml.allow.ecp.flow': 'false', 'id.token.as.detached.signature': 'false', 'saml.assertion.signature': 'true', 'saml_single_logout_service_url_post': 'https://login.microsoftonline.com/login.srf', 'saml.encrypt': 'false', 'saml_assertion_consumer_url_post': 'https://login.microsoftonline.com/login.srf', 'saml.server.signature': 'true', 'saml_idp_initiated_sso_url_name': 'MicrosoftOnline', 'exclude.session.state.from.auth.response': 'false', 'saml.artifact.binding.identifier': 'Ohzdm/95RuxvhGbq/vi8GUTaHf4=', 'saml.artifact.binding': 'false', 'saml_force_name_id_format': 'true', 'tls.client.certificate.bound.access.tokens': 'false', 'acr.loa.map': 'ignore', 'saml.authnstatement': 'true', 'display.on.consent.screen': 'false', 'saml.assertion.lifespan': '300', 'saml_name_id_format': 'persistent', 'token.response.type.bearer.lower-case': 'false', 'saml.onetimeuse.condition': 'false', 'saml_signature_canonicalization_method': 'http://www.w3.org/2001/10/xml-exc-c14n#'}, 'authenticationFlowBindingOverrides': {}, 'fullScopeAllowed': True, 'nodeReRegistrationTimeout': -1, 'protocolMappers': [{'id': 'e25da62a-916e-4412-be0f-4c42c25f99ee', 'name': 'userid_mapper', 'protocol': 'saml', 'protocolMapper': 'saml-user-attribute-mapper', 'consentRequired': False, 'config': {'attribute.nameformat': 'Basic', 'user.attribute': 'uid', 'friendly.name': 'uid', 'attribute.name': 'uid'}}], 'defaultClientScopes': [], 'optionalClientScopes': [], 'access': {'view': True, 'configure': True, 'manage': True}}


GOOGLE_CLIENT = {'id': 'dc72d8ae-7f4b-447c-87b3-1446c8d31e87', 'clientId': 'google.com', 'surrogateAuthRequired': False, 'enabled': True, 'alwaysDisplayInConsole': False, 'clientAuthenticatorType': 'client-secret', 'redirectUris': [], 'webOrigins': [], 'notBefore': 0, 'bearerOnly': False, 'consentRequired': False, 'standardFlowEnabled': True, 'implicitFlowEnabled': False, 'directAccessGrantsEnabled': True, 'serviceAccountsEnabled': False, 'publicClient': True, 'frontchannelLogout': False, 'protocol': 'saml', 'attributes': {'saml.multivalued.roles': 'false', 'saml.force.post.binding': 'true', 'oauth2.device.authorization.grant.enabled': 'false', 'backchannel.logout.revoke.offline.tokens': 'false', 'saml.server.signature.keyinfo.ext': 'false', 'use.refresh.tokens': 'true', 'oidc.ciba.grant.enabled': 'false', 'backchannel.logout.session.required': 'true', 'client_credentials.use_refresh_token': 'false', 'saml.signature.algorithm': 'RSA_SHA256', 'saml.client.signature': 'false', 'require.pushed.authorization.requests': 'false', 'saml.allow.ecp.flow': 'false', 'id.token.as.detached.signature': 'false', 'saml.assertion.signature': 'true', 'saml_single_logout_service_url_post': 'https://www.google.com/a/testdomain.com/acs', 'saml.encrypt': 'false', 'saml_assertion_consumer_url_post': 'https://www.google.com/a/testdomain.com/acs', 'saml.server.signature': 'true', 'saml_idp_initiated_sso_url_name': 'google.com', 'exclude.session.state.from.auth.response': 'false', 'saml.artifact.binding.identifier': 'uuqVS5VzHGiubkW9HiUutFYM3EU=', 'saml.artifact.binding': 'false', 'saml_force_name_id_format': 'false', 'tls.client.certificate.bound.access.tokens': 'false', 'acr.loa.map': 'ignore', 'saml.authnstatement': 'true', 'display.on.consent.screen': 'false', 'saml.assertion.lifespan': '300', 'saml_name_id_format': 'email', 'token.response.type.bearer.lower-case': 'false', 'saml.onetimeuse.condition': 'false', 'saml_signature_canonicalization_method': 'http://www.w3.org/2001/10/xml-exc-c14n#'}, 'authenticationFlowBindingOverrides': {}, 'fullScopeAllowed': True, 'nodeReRegistrationTimeout': -1, 'protocolMappers': [{'id': '53bce0b9-d2f3-4147-9ee6-c3b82e9483cd', 'name': 'userid_mapper', 'protocol': 'saml', 'protocolMapper': 'saml-user-attribute-mapper', 'consentRequired': False, 'config': {'attribute.nameformat': 'Basic', 'user.attribute': 'uid', 'friendly.name': 'uid', 'attribute.name': 'uid'}}], 'defaultClientScopes': [], 'optionalClientScopes': [], 'access': {'view': True, 'configure': True, 'manage': True}}

NC_CLIENT = {'id': 'ace66de8-16ef-4ea6-89bb-9160fc959438', 'clientId': 'https://backup.ucs.test/nextcloud/apps/user_saml/saml/metadata', 'surrogateAuthRequired': False, 'enabled': True, 'alwaysDisplayInConsole': False, 'clientAuthenticatorType': 'client-secret', 'redirectUris': ['https://backup.ucs.test/nextcloud/apps/user_saml/saml/sls', 'https://backup.ucs.test/nextcloud/apps/user_saml/saml/acs'], 'webOrigins': [], 'notBefore': 0, 'bearerOnly': False, 'consentRequired': False, 'standardFlowEnabled': True, 'implicitFlowEnabled': False, 'directAccessGrantsEnabled': True, 'serviceAccountsEnabled': False, 'publicClient': True, 'frontchannelLogout': True, 'protocol': 'saml', 'attributes': {'saml.multivalued.roles': 'false', 'saml.force.post.binding': 'true', 'post.logout.redirect.uris': '+', 'oauth2.device.authorization.grant.enabled': 'false', 'backchannel.logout.revoke.offline.tokens': 'false', 'saml.server.signature.keyinfo.ext': 'false', 'use.refresh.tokens': 'true', 'oidc.ciba.grant.enabled': 'false', 'backchannel.logout.session.required': 'true', 'client_credentials.use_refresh_token': 'false', 'saml.signature.algorithm': 'RSA_SHA256', 'saml.client.signature': 'false', 'require.pushed.authorization.requests': 'false', 'saml.allow.ecp.flow': 'false', 'id.token.as.detached.signature': 'false', 'saml.assertion.signature': 'true', 'saml.encrypt': 'false', 'saml_assertion_consumer_url_post': 'https://backup.ucs.test/nextcloud/apps/user_saml/saml/acs', 'saml.server.signature': 'true', 'exclude.session.state.from.auth.response': 'false', 'saml.artifact.binding.identifier': 'o9mvrwCJYjX2qtSjYoQTxiLHVog=', 'saml.artifact.binding': 'false', 'saml_single_logout_service_url_redirect': 'https://backup.ucs.test/nextcloud/apps/user_saml/saml/sls', 'saml_force_name_id_format': 'true', 'tls.client.certificate.bound.access.tokens': 'false', 'acr.loa.map': 'ignore', 'saml.authnstatement': 'true', 'display.on.consent.screen': 'false', 'saml.assertion.lifespan': '300', 'saml_name_id_format': 'username', 'token.response.type.bearer.lower-case': 'false', 'saml.onetimeuse.condition': 'false', 'saml_signature_canonicalization_method': 'http://www.w3.org/2001/10/xml-exc-c14n#'}, 'authenticationFlowBindingOverrides': {}, 'fullScopeAllowed': True, 'nodeReRegistrationTimeout': -1, 'protocolMappers': [{'id': '161b6b24-2069-4cf0-a7b6-7f97d0e55768', 'name': 'role_list_mapper', 'protocol': 'saml', 'protocolMapper': 'saml-role-list-mapper', 'consentRequired': False, 'config': {'single': 'true', 'attribute.nameformat': 'Basic', 'friendly.name': 'role list mapper', 'attribute.name': 'Role'}}, {'id': '950ef630-242e-4ecb-abfd-637521116d05', 'name': 'userid_mapper', 'protocol': 'saml', 'protocolMapper': 'saml-user-attribute-mapper', 'consentRequired': False, 'config': {'attribute.nameformat': 'Basic', 'user.attribute': 'uid', 'friendly.name': 'uid', 'attribute.name': 'uid'}}], 'defaultClientScopes': [], 'optionalClientScopes': [], 'access': {'view': True, 'configure': True, 'manage': True}}

OC_CLIENT = {'id': '56fd6a56-6d7b-4ba8-a01e-a5cccddee71a', 'clientId': 'owncloudclient', 'name': 'owncloudclient', 'description': '', 'rootUrl': 'https://backup.ucs.test/owncloud/apps/openidconnect/redirect', 'adminUrl': '', 'baseUrl': 'https://backup.ucs.test/owncloud/apps/openidconnect/redirect', 'surrogateAuthRequired': False, 'enabled': True, 'alwaysDisplayInConsole': False, 'clientAuthenticatorType': 'client-secret', 'secret': 'univention', 'redirectUris': ['https://p25.jbp25.intranet', 'https://backup.ucs.test/owncloud/apps/openidconnect/redirect'], 'webOrigins': ['https://p25.jbp25.intranet', 'https://backup.ucs.test/owncloud/apps/openidconnect/redirect'], 'notBefore': 0, 'bearerOnly': False, 'consentRequired': False, 'standardFlowEnabled': True, 'implicitFlowEnabled': False, 'directAccessGrantsEnabled': False, 'serviceAccountsEnabled': False, 'publicClient': False, 'frontchannelLogout': True, 'protocol': 'openid-connect', 'attributes': {'saml.multivalued.roles': 'false', 'saml.force.post.binding': 'false', 'frontchannel.logout.session.required': 'false', 'oauth2.device.authorization.grant.enabled': 'false', 'backchannel.logout.revoke.offline.tokens': 'false', 'saml.server.signature.keyinfo.ext': 'false', 'use.refresh.tokens': 'true', 'oidc.ciba.grant.enabled': 'false', 'backchannel.logout.session.required': 'true', 'client_credentials.use_refresh_token': 'false', 'saml.client.signature': 'false', 'require.pushed.authorization.requests': 'false', 'saml.allow.ecp.flow': 'false', 'saml.assertion.signature': 'false', 'id.token.as.detached.signature': 'false', 'client.secret.creation.time': '1661514856', 'saml.encrypt': 'false', 'saml.server.signature': 'false', 'exclude.session.state.from.auth.response': 'false', 'saml.artifact.binding': 'false', 'saml_force_name_id_format': 'false', 'tls.client.certificate.bound.access.tokens': 'false', 'acr.loa.map': 'ignore', 'saml.authnstatement': 'false', 'display.on.consent.screen': 'false', 'token.response.type.bearer.lower-case': 'false', 'saml.onetimeuse.condition': 'false'}, 'authenticationFlowBindingOverrides': {}, 'fullScopeAllowed': True, 'nodeReRegistrationTimeout': -1, 'protocolMappers': [{'id': '74253a76-4b93-49a4-885d-b5a9b753f678', 'name': 'email', 'protocol': 'openid-connect', 'protocolMapper': 'oidc-usermodel-property-mapper', 'consentRequired': False, 'config': {'userinfo.token.claim': 'true', 'user.attribute': 'email', 'id.token.claim': 'true', 'access.token.claim': 'true', 'claim.name': 'email', 'jsonType.label': 'String'}}, {'id': 'cc653613-6311-46aa-8098-5041d001b48a', 'name': 'username', 'protocol': 'openid-connect', 'protocolMapper': 'oidc-usermodel-property-mapper', 'consentRequired': False, 'config': {'userinfo.token.claim': 'true', 'user.attribute': 'username', 'id.token.claim': 'true', 'access.token.claim': 'true', 'claim.name': 'preferred_username', 'jsonType.label': 'String'}}, {'id': 'f3b27fd5-0730-4b6d-80b5-620beb3cf65d', 'name': 'uid', 'protocol': 'openid-connect', 'protocolMapper': 'oidc-usermodel-attribute-mapper', 'consentRequired': False, 'config': {'userinfo.token.claim': 'true', 'user.attribute': 'uid', 'id.token.claim': 'true', 'access.token.claim': 'true', 'claim.name': 'uid', 'jsonType.label': 'String'}}], 'defaultClientScopes': ['web-origins', 'acr', 'roles', 'profile', 'email'], 'optionalClientScopes': ['address', 'phone', 'offline_access', 'microprofile-jwt'], 'access': {'view': True, 'configure': True, 'manage': True}}

UMC_CLIENT = {'id': '84283fc3-3aed-4cdb-9c28-546cd8e5dcce', 'clientId': 'https://whatever.ucs.test/univention/saml/metadata', 'description': 'Univention Management Console at p25.jbp25.intranet', 'surrogateAuthRequired': False, 'enabled': True, 'alwaysDisplayInConsole': False, 'clientAuthenticatorType': 'client-secret', 'redirectUris': ['http://169.254.240.97/univention/saml/slo/', 'http://p25.jbp25.intranet/univention/saml/slo/', 'http://p25.jbp25.intranet/univention/saml/', 'http://10.200.21.25/univention/saml/', 'http://169.254.240.97/univention/saml/', 'http://10.200.21.25/univention/saml/slo/', 'https://10.200.21.25/univention/saml/', 'https://p25.jbp25.intranet/univention/saml/slo/', 'https://169.254.240.97/univention/saml/', 'https://10.200.21.25/univention/saml/slo/', 'https://p25.jbp25.intranet/univention/saml/', 'https://169.254.240.97/univention/saml/slo/'], 'webOrigins': [], 'notBefore': 0, 'bearerOnly': False, 'consentRequired': False, 'standardFlowEnabled': True, 'implicitFlowEnabled': False, 'directAccessGrantsEnabled': True, 'serviceAccountsEnabled': False, 'publicClient': True, 'frontchannelLogout': True, 'protocol': 'saml', 'attributes': {'saml.multivalued.roles': 'false', 'saml.force.post.binding': 'true', 'post.logout.redirect.uris': '+', 'oauth2.device.authorization.grant.enabled': 'false', 'backchannel.logout.revoke.offline.tokens': 'false', 'saml.server.signature.keyinfo.ext': 'false', 'use.refresh.tokens': 'true', 'oidc.ciba.grant.enabled': 'false', 'backchannel.logout.session.required': 'true', 'client_credentials.use_refresh_token': 'false', 'saml.signature.algorithm': 'RSA_SHA256', 'saml.client.signature': 'false', 'require.pushed.authorization.requests': 'false', 'saml.allow.ecp.flow': 'false', 'id.token.as.detached.signature': 'false', 'saml.assertion.signature': 'true', 'saml_single_logout_service_url_post': 'https://p25.jbp25.intranet/univention/saml/slo/', 'saml.encrypt': 'false', 'saml_assertion_consumer_url_post': 'https://p25.jbp25.intranet/univention/saml/', 'saml.server.signature': 'true', 'exclude.session.state.from.auth.response': 'false', 'saml.artifact.binding.identifier': 'NFMARG3lebyfCWPQ5ef20F+Mxnk=', 'saml.artifact.binding': 'false', 'saml_single_logout_service_url_redirect': 'https://p25.jbp25.intranet/univention/saml/slo/', 'saml_force_name_id_format': 'true', 'tls.client.certificate.bound.access.tokens': 'false', 'acr.loa.map': 'ignore', 'saml.authnstatement': 'true', 'display.on.consent.screen': 'false', 'saml.assertion.lifespan': '300', 'saml_name_id_format': 'transient', 'token.response.type.bearer.lower-case': 'false', 'saml.onetimeuse.condition': 'false', 'saml_signature_canonicalization_method': 'http://www.w3.org/2001/10/xml-exc-c14n#'}, 'authenticationFlowBindingOverrides': {}, 'fullScopeAllowed': True, 'nodeReRegistrationTimeout': -1, 'protocolMappers': [{'id': '6929aea8-ff90-4a7b-87cf-342abed2e51c', 'name': 'uid_mapper', 'protocol': 'saml', 'protocolMapper': 'saml-user-attribute-mapper', 'consentRequired': False, 'config': {'attribute.nameformat': 'URI Reference', 'user.attribute': 'uid', 'friendly.name': 'uid', 'attribute.name': 'urn:oid:0.9.2342.19200300.100.1.1'}}, {'id': '3d54d6fa-d441-420f-9e41-c9eb5fe855d1', 'name': 'userid_mapper', 'protocol': 'saml', 'protocolMapper': 'saml-user-attribute-mapper', 'consentRequired': False, 'config': {'attribute.nameformat': 'Basic', 'user.attribute': 'uid', 'friendly.name': 'uid', 'attribute.name': 'uid'}}], 'defaultClientScopes': [], 'optionalClientScopes': [], 'access': {'view': True, 'configure': True, 'manage': True}}


UMC_OIDC_CLIENT = {
    "id": "bac75d13-f7d8-4a78-bf89-5b77cc5bfd99",
    "clientId": "https://{fqdn}/univention/oidc/",
    "name": "UMC on {fqdn}",
    "description": "Univention Management Console on {fqdn}",
    "rootUrl": "https://{fqdn}/univention/oidc/",
    "adminUrl": "",
    "baseUrl": "https://{fqdn}/univention/oidc/",
    "surrogateAuthRequired": False,
    "enabled": True,
    "alwaysDisplayInConsole": True,
    "clientAuthenticatorType": "client-secret",
    "secret": "ignore",
    "redirectUris": [
        "https://{ip}/univention/oidc/*",
        "http://{ip}/univention/oidc/*",
        "https://{fqdn}",
        "http://{fqdn}/univention/oidc/*",
        "https://{fqdn}/univention/oidc/",
        "https://{fqdn}/univention/oidc/*"
    ],
    "webOrigins": [
        "+"
    ],
    "notBefore": 0,
    "bearerOnly": False,
    "consentRequired": False,
    "standardFlowEnabled": True,
    "implicitFlowEnabled": False,
    "directAccessGrantsEnabled": True,
    "serviceAccountsEnabled": False,
    "publicClient": False,
    "frontchannelLogout": False,
    "protocol": "openid-connect",
    "attributes": {
        "access.token.lifespan": "300",
        "saml.multivalued.roles": "false",
        "saml.force.post.binding": "false",
        "post.logout.redirect.uris": "http://{fqdn_lower}/univention/oidc/*##https://{fqdn_lower}/univention/oidc/*##http://{ip}/univention/oidc/*##https://{ip}/univention/oidc/*",
        "frontchannel.logout.session.required": "false",
        "oauth2.device.authorization.grant.enabled": "false",
        "backchannel.logout.revoke.offline.tokens": "false",
        "saml.server.signature.keyinfo.ext": "false",
        "use.refresh.tokens": "true",
        "oidc.ciba.grant.enabled": "false",
        "backchannel.logout.url": "https://{fqdn_lower}/univention/oidc/backchannel-logout",
        "backchannel.logout.session.required": "false",
        "client_credentials.use_refresh_token": "false",
        "consent.screen.text": "Allow access to UDM-REST API and OpenLDAP?",
        "saml.client.signature": "false",
        "require.pushed.authorization.requests": "false",
        "pkce.code.challenge.method": "S256",
        "saml.allow.ecp.flow": "false",
        "saml.assertion.signature": "false",
        "id.token.as.detached.signature": "false",
        "client.secret.creation.time": "1661514856",
        "saml.encrypt": "false",
        "frontchannel.logout.url": "https://{fqdn_lower}/univention/oidc/frontchannel-logout",
        "logoUri": "https://{fqdn}/favicon.ico",
        "saml.server.signature": "false",
        "exclude.session.state.from.auth.response": "false",
        "saml.artifact.binding": "false",
        "saml_force_name_id_format": "false",
        "tls.client.certificate.bound.access.tokens": "false",
        "acr.loa.map": "ignore",
        "saml.authnstatement": "false",
        "display.on.consent.screen": "false",
        "token.response.type.bearer.lower-case": "false",
        "saml.onetimeuse.condition": "false"
    },
    "authenticationFlowBindingOverrides": {},
    "fullScopeAllowed": True,
    "nodeReRegistrationTimeout": -1,
    "protocolMappers": [
        {
            "id": "f60b68cc-4834-4758-bd83-48aaab8fbffd",
            "name": "uid",
            "protocol": "openid-connect",
            "protocolMapper": "oidc-usermodel-attribute-mapper",
            "consentRequired": False,
            "config": {
                "userinfo.token.claim": "true",
                "user.attribute": "uid",
                "id.token.claim": "true",
                "access.token.claim": "true",
                "claim.name": "uid",
                "jsonType.label": "String"
            }
        },
        {
            "id": "b508f094-e7ca-45ea-b139-933dbc2f7d55",
            "name": "email",
            "protocol": "openid-connect",
            "protocolMapper": "oidc-usermodel-property-mapper",
            "consentRequired": False,
            "config": {
                "userinfo.token.claim": "true",
                "user.attribute": "email",
                "id.token.claim": "true",
                "access.token.claim": "true",
                "claim.name": "email",
                "jsonType.label": "String"
            }
        },
        {
            "id": "9321fa9f-beb9-49e8-9d2f-8abfb49bc649",
            "name": "id-audience-0",
            "protocol": "openid-connect",
            "protocolMapper": "oidc-audience-mapper",
            "consentRequired": False,
            "config": {
                "included.client.audience": "https://{fqdn_lower}/univention/oidc/",
                "id.token.claim": "true",
                "access.token.claim": "false",
                "userinfo.token.claim": "true"
            }
        },
        {
            "id": "e6bc7149-2095-49a6-9b3a-3e1570ea5461",
            "name": "access-audience-0",
            "protocol": "openid-connect",
            "protocolMapper": "oidc-audience-mapper",
            "consentRequired": False,
            "config": {
                "included.client.audience": "ldaps://{domainname}/",
                "id.token.claim": "false",
                "access.token.claim": "true",
                "userinfo.token.claim": "false"
            }
        },
        {
            "id": "a5c99f92-3b60-402c-bca4-8267cb6a26ba",
            "name": "username",
            "protocol": "openid-connect",
            "protocolMapper": "oidc-usermodel-property-mapper",
            "consentRequired": False,
            "config": {
                "userinfo.token.claim": "true",
                "user.attribute": "username",
                "id.token.claim": "true",
                "access.token.claim": "true",
                "claim.name": "preferred_username",
                "jsonType.label": "String"
            }
        }
    ],
    "defaultClientScopes": [
        "web-origins",
        "acr",
        "roles",
        "profile",
        "email"
    ],
    "optionalClientScopes": [
        "address",
        "phone",
        "offline_access",
        "microprofile-jwt"
    ],
    "access": {
        "view": True,
        "configure": True,
        "manage": True
    }
}
