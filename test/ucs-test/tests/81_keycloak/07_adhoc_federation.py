#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: Test keycloak ad hoc federation
## tags: [keycloak]
## roles: [domaincontroller_master, domaincontroller_backup]
## exposure: dangerous

import base64
import json
import os
import uuid
from types import SimpleNamespace
from typing import Optional

import pytest
from keycloak import KeycloakAdmin
from keycloak.exceptions import KeycloakError, KeycloakGetError
from selenium.webdriver.chrome.webdriver import WebDriver
from utils import get_portal_tile, keycloak_login, run_command, wait_for_id

from univention.config_registry.backend import ConfigRegistry
from univention.udm import UDM
from univention.udm.modules.users_user import UsersUserObject


def get_realm_payload(realm: str, locales_format: str, default_locale: str, keycloak_url: str) -> dict:
    return {
        "id": realm,
        "realm": realm,
        "enabled": True,
        "internationalizationEnabled": True,
        "supportedLocales": locales_format,
        "defaultLocale": default_locale,
        "adminTheme": "keycloak",
        "accountTheme": "keycloak",
        "emailTheme": "keycloak",
        "loginTheme": "UCS",
        "browserSecurityHeaders": {
            "contentSecurityPolicyReportOnly": "",
            "xContentTypeOptions": "nosniff",
            "xRobotsTag": "none",
            "xFrameOptions": "",
            "contentSecurityPolicy": f"frame-src 'self'; frame-ancestors 'self' {keycloak_url}/univention; object-src 'none';",
            "xXSSProtection": "1; mode=block",
            "strictTransportSecurity": "max-age=31536000; includeSubDomains",
        },
    }


def get_client_payload(client_id: str, valid_redirect_urls: list) -> dict:
    return {
        "clientId": client_id,
        "surrogateAuthRequired": False,
        "enabled": True,
        "alwaysDisplayInConsole": False,
        "clientAuthenticatorType": "client-secret",
        "redirectUris": valid_redirect_urls,
        "webOrigins": [],
        "notBefore": 0,
        "bearerOnly": False,
        "consentRequired": False,
        "standardFlowEnabled": True,
        "implicitFlowEnabled": False,
        "directAccessGrantsEnabled": True,
        "serviceAccountsEnabled": False,
        "publicClient": True,
        "frontchannelLogout": True,
        "protocol": "saml",
        "attributes": {
            "saml.multivalued.roles": "false",
            "saml.force.post.binding": "true",
            "oauth2.device.authorization.grant.enabled": "false",
            "backchannel.logout.revoke.offline.tokens": "false",
            "saml.server.signature.keyinfo.ext": "false",
            "use.refresh.tokens": "true",
            "oidc.ciba.grant.enabled": "false",
            "backchannel.logout.session.required": "true",
            "client_credentials.use_refresh_token": "false",
            "saml.signature.algorithm": "RSA_SHA256",
            "saml.client.signature": "false",
            "require.pushed.authorization.requests": "false",
            "id.token.as.detached.signature": "false",
            "saml.assertion.signature": "true",
            "saml_single_logout_service_url_post": "",
            "saml.encrypt": "false",
            "saml_assertion_consumer_url_post": "",
            "saml.server.signature": "true",
            "exclude.session.state.from.auth.response": "false",
            "saml.artifact.binding.identifier": "JOtItQNol3ThXjMMWI3gcbW92sU=",
            "saml.artifact.binding": "false",
            "saml_single_logout_service_url_redirect": "",
            "saml_force_name_id_format": "false",
            "tls.client.certificate.bound.access.tokens": "false",
            "acr.loa.map": "{}",
            "saml.authnstatement": "true",
            "display.on.consent.screen": "false",
            "saml.assertion.lifespan": "300",
            "token.response.type.bearer.lower-case": "false",
            "saml.onetimeuse.condition": "false",
            "saml_signature_canonicalization_method": "http://www.w3.org/2001/10/xml-exc-c14n#",
        },
        "authenticationFlowBindingOverrides": {},
        "fullScopeAllowed": True,
        "nodeReRegistrationTimeout": -1,
        "protocolMappers": [
            {
                "config": {
                    "attribute.name": "sAMAccountName",
                    "attribute.nameformat": "Unspecified",
                    "friendly.name": "uid",
                    "user.attribute": "uid",
                },
                "consentRequired": "false",
                "name": "userid_mapper",
                "protocol": "saml",
                "protocolMapper": "saml-user-attribute-mapper",
            },
            {
                "config": {
                    "attribute.name": "objectGUID",
                    "attribute.nameformat": "Unspecified",
                    "friendly.name": "uuid_remote",
                    "user.attribute": "uuid_remote",
                },
                "consentRequired": "false",
                "name": "objectGUID_mapper",
                "protocol": "saml",
                "protocolMapper": "saml-user-attribute-mapper",
            },
            {
                "config": {
                    "attribute.name": "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/surname",
                    "attribute.nameformat": "Unspecified",
                    "friendly.name": "lastName",
                    "user.attribute": "lastName",
                },
                "consentRequired": "false",
                "name": "lastname_mapper",
                "protocol": "saml",
                "protocolMapper": "saml-user-attribute-mapper",
            },
            {
                "config": {
                    "attribute.name": "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/givenname",
                    "attribute.nameformat": "Unspecified",
                    "friendly.name": "firstName",
                    "user.attribute": "firstName",
                },
                "consentRequired": "false",
                "name": "firstname_mapper",
                "protocol": "saml",
                "protocolMapper": "saml-user-attribute-mapper",
            },
            {
                "config": {
                    "attribute.name": "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress",
                    "attribute.nameformat": "Unspecified",
                    "friendly.name": "email",
                    "user.attribute": "email",
                },
                "consentRequired": "false",
                "name": "email_mapper",
                "protocol": "saml",
                "protocolMapper": "saml-user-attribute-mapper",
            },
        ],
        "defaultClientScopes": [
            "role_list",
        ],
        "optionalClientScopes": [],
        "access": {
            "view": True,
            "configure": True,
            "manage": True,
        },
    }


def get_user_payload(uid: str) -> dict:
    return {
        "email": f"{uid}@univention.de",
        "username": uid,
        "enabled": True,
        "firstName": "Test",
        "lastName": "Example",
        "credentials": [
            {
                "value": "univention",
                "type": "password",
            },
        ],
        "attributes": {
            "uid": [uid],
            "uuid_remote": [base64.b64encode(uuid.UUID('60722945-2fb8-49e4-b5d0-c2838a390365').bytes_le).decode('utf-8')],
        },
    }


def get_idp_payload(keycloak_fqdn: str, certificate: str) -> dict:
    keycloak_fqdn = keycloak_fqdn.rstrip("/")
    return {
        "alias": "saml",
        "providerId": "saml",
        "enabled": True,
        "updateProfileFirstLoginMode": "on",
        "trustEmail": False,
        "storeToken": False,
        "addReadTokenRoleOnCreate": False,
        "authenticateByDefault": False,
        "linkOnly": False,
        "firstBrokerLoginFlowAlias": "Univention-Authenticator ad-hoc federation flow",
        "config": {
            "allowCreate": "true",
            "nameIDPolicyFormat": "urn:oasis:names:tc:SAML:1.1:nameid-format:unspecified",
            "principalAttribute": "sAMAccountName",
            "principalType": "ATTRIBUTE",
            "syncMode": "IMPORT",
            "postBindingAuthnRequest": "true",
            "postBindingLogout": "false",
            "postBindingResponse": "true",
            "authnContextComparisonType": "exact",
            "entityId": f"{keycloak_fqdn}/realms/dummy",
            "singleSignOnServiceUrl": f"{keycloak_fqdn}/realms/dummy/protocol/saml",
            "xmlSigKeyInfoKeyNameTransformer": "KEY_ID",
            "signatureAlgorithm": "RSA_SHA256",
            "signingCertificate": certificate,
            "validateSignature": "false",
            "wantAuthnRequestsSigned": "true",
            "useJwksUrl": "true",
        },
    }


def _create_idp(keycloak_admin_connection: KeycloakAdmin, ucr: ConfigRegistry, keycloak_fqdn: str, realm: str) -> None:
    # auth flow
    payload_authflow = {"newName": "Univention-Authenticator ad-hoc federation flow"}
    try:
        keycloak_admin_connection.copy_authentication_flow(payload=json.dumps(payload_authflow), flow_alias='first broker login')
    except KeycloakGetError as exc:
        if exc.response_code != 409:
            raise (exc)
    # execution
    payload_exec_flow = {"provider": "univention-authenticator"}
    keycloak_admin_connection.create_authentication_flow_execution(payload=json.dumps(payload_exec_flow), flow_alias='Univention-Authenticator ad-hoc federation flow')
    execution_list = keycloak_admin_connection.get_authentication_flow_executions("Univention-Authenticator ad-hoc federation flow")
    ua_execution = list(filter(lambda flow: flow["displayName"] == 'Univention Authenticator', execution_list))[0]
    payload_exec_flow = {
        "id": ua_execution["id"],
        "requirement": "REQUIRED",
        "displayName": "Univention Authenticator",
        "requirementChoices": [
            "REQUIRED",
            "DISABLED",
        ],
        "configurable": "true",
        "providerId": "univention-authenticator",
        "level": 0,
        "index": 2,
    }
    try:
        keycloak_admin_connection.update_authentication_flow_executions(payload=json.dumps(payload_exec_flow), flow_alias='Univention-Authenticator ad-hoc federation flow')
    except KeycloakError as e:
        if e.response_code != 202:  # FIXME: function expected 204 response it gets 202
            raise e
    # config_id from 'authenticationConfig' in get_authentication_flow_executions
    hostname = ucr["hostname"]
    domain = ucr["domainname"]
    config_ua = {
        "config": {
            "udm_endpoint": "http://{}.{}/univention/udm".format(hostname, domain),
            "udm_user": "Administrator",
            "udm_password": "univention",
        },
        "alias": "localhost config",
    }
    keycloak_admin_connection.raw_post("admin/realms/{}/authentication/executions/{}/config".format(realm, ua_execution["id"]), json.dumps(config_ua))
    # create idp
    run_command(["univention-keycloak", "saml/idp/cert", "get", "--output", "/root/sign.cert"])
    with open("/root/sign.cert") as fd:
        certificate = fd.read()
    payload_idp = get_idp_payload(keycloak_fqdn, certificate)
    try:
        keycloak_admin_connection.create_idp(payload_idp)
    except KeycloakGetError as exc:
        if exc.response_code != 409:
            raise (exc)
    new_idp = list(filter(lambda idp: idp["alias"] == "saml", keycloak_admin_connection.get_idps()))[0]

    # mappers
    idp_mapper_payload = {
        "id": new_idp["internalId"],
        "name": "email_importer",
        "identityProviderAlias": "saml",
        "identityProviderMapper": "saml-user-attribute-idp-mapper",
        "config": {
            "syncMode": "IMPORT",
            "user.attribute": "email",
            "attributes": "[]",
            "attribute.name": "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress",
        },
    }
    keycloak_admin_connection.add_mapper_to_idp(idp_alias="saml", payload=idp_mapper_payload)

    idp_mapper_payload = {
        "config": {
            "attributes": "[]",
            "syncMode": "IMPORT",
            "target": "LOCAL",
            "template": "external-${ALIAS}-${ATTRIBUTE.sAMAccountName}",
        },
        "identityProviderAlias": "saml",
        "identityProviderMapper": "saml-username-idp-mapper",
        "name": "uid_importer",
    }
    keycloak_admin_connection.add_mapper_to_idp(idp_alias="saml", payload=idp_mapper_payload)

    idp_mapper_payload = {
        "id": new_idp["internalId"],
        "name": "firstname_importer",
        "identityProviderAlias": "saml",
        "identityProviderMapper": "saml-user-attribute-idp-mapper",
        "config": {
            "syncMode": "IMPORT",
            "user.attribute": "firstName",
            "attributes": "[]",
            "attribute.name": "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/givenname",
        },
    }
    keycloak_admin_connection.add_mapper_to_idp(idp_alias="saml", payload=idp_mapper_payload)

    idp_mapper_payload = {
        "id": new_idp["internalId"],
        "name": "lastname_importer",
        "identityProviderAlias": "saml",
        "identityProviderMapper": "saml-user-attribute-idp-mapper",
        "config": {
            "syncMode": "IMPORT",
            "user.attribute": "lastName",
            "attributes": "[]",
            "attribute.name": "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/surname",
        },
    }
    keycloak_admin_connection.add_mapper_to_idp(idp_alias="saml", payload=idp_mapper_payload)

    idp_mapper_payload = {
        "id": new_idp["internalId"],
        "name": "univentionObjectId_importer",
        "identityProviderAlias": "saml",
        "identityProviderMapper": "saml-user-attribute-idp-mapper",
        "config": {
            "syncMode": "IMPORT",
            "user.attribute": "objectGUID",
            "attributes": "[]",
            "attribute.name": "objectGUID",
        },
    }
    keycloak_admin_connection.add_mapper_to_idp(idp_alias="saml", payload=idp_mapper_payload)

    idp_mapper_customer = {
        "identityProviderAlias": "saml",
        "config": {
            "syncMode": "IMPORT",
            "attributes": "[]",
            "attribute": "univentionSourceIAM",
            "attribute.value": "Dummy realm",
        },
        "name": "univentionSourceIAM_importer",
        "identityProviderMapper": "hardcoded-attribute-idp-mapper",
    }
    keycloak_admin_connection.add_mapper_to_idp(idp_alias="saml", payload=idp_mapper_customer)


def _test_sso_login(selenium: WebDriver, portal_config: SimpleNamespace, keycloak_config: SimpleNamespace) -> None:
    selenium.get(portal_config.url)
    wait_for_id(selenium, portal_config.categories_id)
    assert selenium.title == portal_config.title
    get_portal_tile(selenium, portal_config.sso_login_tile_de, portal_config).click()
    wait_for_id(selenium, "social-saml").click()
    keycloak_login(selenium, keycloak_config, "test_user1", "univention")
    wait_for_id(selenium, portal_config.header_menu_id).click()
    wait_for_id(selenium, "loginButton").click()
    wait_for_id(selenium, portal_config.categories_id)
    assert get_portal_tile(selenium, portal_config.sso_login_tile_de, portal_config)


def get_udm_user_obj(username: str) -> Optional[UsersUserObject]:
    udm_users = UDM.admin().version(2).get("users/user")
    user = list(udm_users.search(f"uid={username}"))
    if len(user) == 1:
        return user[0]
    else:
        return None


def _test_federated_user(keycloak_admin_connection: KeycloakAdmin, ucr: ConfigRegistry) -> None:
    udm_user = get_udm_user_obj("external-saml-test_user1")
    assert udm_user
    assert udm_user.props.username == 'external-saml-test_user1'
    assert udm_user.props.lastname == 'Example'
    assert udm_user.props.firstname == 'Test'
    assert udm_user.props.description == 'Shadow copy of user'
    kc_user_id = keycloak_admin_connection.get_user_id(username="external-saml-test_user1")
    kc_user = keycloak_admin_connection.get_user(user_id=kc_user_id)
    assert kc_user["username"] == "external-saml-test_user1"
    assert kc_user["email"] == "test_user1@univention.de"
    assert kc_user["firstName"] == "Test"
    assert kc_user["lastName"] == "Example"


@pytest.mark.skipif(not os.path.isfile("/etc/keycloak.secret"), reason="fails on hosts without keycloak.secret")
def test_adhoc_federation(keycloak_admin_connection: KeycloakAdmin, ucr: ConfigRegistry, keycloak_config: SimpleNamespace, selenium: WebDriver, portal_config: SimpleNamespace):

    realm = "dummy"

    try:
        # create realm
        locales_ucr = ucr.get("locale").split()
        locales_format = [locale[:locale.index("_")] for locale in locales_ucr]
        default_locale_ucr = ucr.get("locale/default")
        default_locale = default_locale_ucr[:default_locale_ucr.index("_")]
        realm_payload = get_realm_payload(realm, locales_format, default_locale, keycloak_config.url)
        keycloak_admin_connection.create_realm(payload=realm_payload, skip_exists=True)
        # create client in dummy realm
        keycloak_admin_connection.realm_name = "dummy"
        client_id_location = f"/realms/{realm}"
        valid_redirect_urls = [keycloak_config.url.rstrip("/") + "/realms/ucs/broker/saml/endpoint"]
        client_id = keycloak_config.url.rstrip("/") + client_id_location
        client_payload = get_client_payload(client_id, valid_redirect_urls)
        keycloak_admin_connection.create_client(payload=client_payload, skip_exists=True)
        # create dummy users
        keycloak_admin_connection.create_user(get_user_payload("test_user1"))
        keycloak_admin_connection.create_user(get_user_payload("test_user2"))
        # create IdP federation in ucs realm
        keycloak_admin_connection.realm_name = "ucs"
        _create_idp(keycloak_admin_connection, ucr, keycloak_config.url, "ucs")
        # do some tests
        keycloak_admin_connection.realm_name = "ucs"
        _test_sso_login(selenium, portal_config, keycloak_config)
        _test_federated_user(keycloak_admin_connection, ucr)
    finally:
        udm_user = get_udm_user_obj("external-saml-test_user1")
        if udm_user:
            udm_user.delete()
        kc_user_id = keycloak_admin_connection.get_user_id(username="external-saml-test_user1")
        if kc_user_id:
            keycloak_admin_connection.delete_user(kc_user_id)
        keycloak_admin_connection.delete_idp("saml")
        keycloak_admin_connection.delete_realm(realm_name="dummy")
        # function not present in our version, workaround
        keycloak_admin_connection.realm_name = "ucs"
        flow_id = [
            x for x in keycloak_admin_connection.get_authentication_flows()
            if x["alias"] == "Univention-Authenticator ad-hoc federation flow"
        ][0]["id"]
        params_path = {"realm-name": keycloak_admin_connection.realm_name, "id": flow_id}
        keycloak_admin_connection.raw_delete("admin/realms/{realm-name}/authentication/flows/{id}".format(**params_path))
