# SPDX-License-Identifier: AGPL-3.0-only
# SPDX-FileCopyrightText: 2025-2026 Univention GmbH

"""
Keycloak Ad-Hoc Federation Setup Tool
This script automates the setup of Keycloak ad-hoc federation between realms, including:
- Creates a dummy realm with a test user (test_adhoc:univention)
- Configures federation client and authentication flow
- Sets up Identity Provider (IDP) with OIDC
- Configures Univention Authenticator and UDM connection
- Establishes IDP mappers for user attributes
"""

import json
import logging
from typing import Any

from keycloak import KeycloakAdmin
from keycloak.exceptions import KeycloakError, KeycloakPostError


class AdHocProvisioning:
    def __init__(
        self,
        keycloak_url: str,
        admin_username: str,
        admin_password: str,
        udm_url: str,
        udm_username: str,
        udm_password: str,
        existing_realm: str = "nubus",
        dummy_realm: str = "adhoc",
        path: str = "",
    ):
        """Initialize AdHocProvisioning with configuration parameters."""
        self.keycloak_url = keycloak_url
        self.admin_username = admin_username
        self.admin_password = admin_password
        self.udm_url = udm_url
        self.udm_username = udm_username
        self.udm_password = udm_password
        self.existing_realm = existing_realm
        self.dummy_realm = dummy_realm
        self.path = path

        # Set up logging
        self.logger = logging.getLogger(__name__)
        if not self.logger.handlers:
            logging.basicConfig(
                level=logging.INFO,
                format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            )

        # Initialize Keycloak admin connections
        self.kc_master = self._create_keycloak_admin("master", "master")
        self.kc_dummy = None
        self.kc_existing = None

    def _create_keycloak_admin(self, realm_name: str, user_realm_name: str) -> KeycloakAdmin:
        """Create a KeycloakAdmin instance."""
        return KeycloakAdmin(
            server_url=self.keycloak_url,
            username=self.admin_username,
            password=self.admin_password,
            realm_name=realm_name,
            client_id="admin-cli",
            verify=True,
            user_realm_name=user_realm_name,
        )

    def _get_realm_payload(self, realm: str) -> dict[str, Any]:
        """Get realm configuration payload."""
        return {
            "id": realm,
            "realm": realm,
            "enabled": True,
            "loginTheme": "keycloak",
            "browserSecurityHeaders": {
                "contentSecurityPolicyReportOnly": "",
                "xContentTypeOptions": "nosniff",
                "xRobotsTag": "none",
                "xFrameOptions": "SAMEORIGIN",
                "contentSecurityPolicy": f"frame-src 'self'; frame-ancestors 'self' {self.keycloak_url}; object-src 'none';",
                "xXSSProtection": "1; mode=block",
                "strictTransportSecurity": "max-age=31536000; includeSubDomains",
            },
        }

    def _get_test_user_payload(
        self,
        username: str,
        password: str,
        uuid_remote: str,
        email_verified: bool = True,
        temporary_password: bool = False,
    ) -> dict[str, Any]:
        """Get test user configuration payload."""
        # TODO: Create random uuid_remote

        return {
            "username": username,
            "enabled": True,
            "firstName": "Test",
            "lastName": "User",
            "email": f"{username}@adhoc.test",
            "emailVerified": email_verified,
            "credentials": [
                {
                    "type": "password",
                    "value": password,
                    "temporary": temporary_password,
                },
            ],
            "attributes": {
                "uuid_remote": uuid_remote,
                "uid": username,
            },
        }

    def _get_idp_payload(self, client_secret: str = "") -> dict[str, Any]:
        """Get IDP configuration payload."""
        return {
            "alias": f"oidc-{self.dummy_realm}",
            "displayName": f"OIDC {self.dummy_realm}",
            "providerId": "oidc",
            "enabled": True,
            "trustEmail": True,
            "storeToken": False,
            "addReadTokenRoleOnCreate": False,
            "firstBrokerLoginFlowAlias": "adhoc",
            "config": {
                "clientId": "federation-client",
                "clientSecret": client_secret,
                "tokenUrl": f"{self.keycloak_url}realms/{self.dummy_realm}/protocol/openid-connect/token",
                "authorizationUrl": f"{self.keycloak_url}realms/{self.dummy_realm}/protocol/openid-connect/auth",
                "userInfoUrl": f"{self.keycloak_url}realms/{self.dummy_realm}/protocol/openid-connect/userinfo",
                "defaultScope": "openid profile email",
                "validateSignature": "true",
                "useJwksUrl": "true",
                "jwksUrl": f"{self.keycloak_url}realms/{self.dummy_realm}/protocol/openid-connect/certs",
            },
        }

    def setup_univention_auth_flow(self) -> None:
        """Set up the Univention authentication flow."""
        flow_alias = "adhoc"

        if not self.kc_existing:
            raise KeycloakError("Keycloak admin connection to existing realm not initialized")

        # Copy the first broker login flow
        self.logger.info("Creating authentication flow by copying 'first broker login'")
        payload_authflow = {"newName": flow_alias}
        try:
            self.kc_existing.copy_authentication_flow(
                payload=payload_authflow,
                flow_alias="first broker login",
            )
        except KeycloakError as e:
            if e.response_code != 409:  # Ignore if already exists
                raise
            self.logger.info("Flow already exists, continuing with configuration")

        # Get the flow executions
        executions = self.kc_existing.get_authentication_flow_executions(flow_alias)

        # Configure Review Profile to DISABLED
        review_profile = next(
            (e for e in executions if e["displayName"] == "Review Profile"),
            None,
        )
        if review_profile:
            self.logger.info("Configuring Review Profile")
            config = {
                "id": review_profile["id"],
                "requirement": "DISABLED",
                "displayName": review_profile["displayName"],
                "requirementChoices": review_profile["requirementChoices"],
                "configurable": review_profile.get("configurable", True),
                "providerId": review_profile["providerId"],
                "level": review_profile.get("level", 0),
                "index": review_profile.get("index", 0),
            }
            self.kc_existing.update_authentication_flow_executions(
                payload=config,
                flow_alias=flow_alias,
            )

        # Add and configure Univention authenticator
        self.logger.info("Adding Univention Authenticator execution")
        exec_payload = {"provider": "univention-authenticator"}
        self.kc_existing.create_authentication_flow_execution(
            payload=exec_payload,
            flow_alias=flow_alias,
        )

        # Get updated executions
        executions = self.kc_existing.get_authentication_flow_executions(flow_alias)
        ua_execution = next(
            (e for e in executions if e["displayName"] == "Univention Authenticator"),
            None,
        )
        if not ua_execution:
            raise KeycloakError(
                "Univention Authenticator execution not found after creation",
            )

        # Configure Univention Authenticator
        self.logger.info("Configuring Univention Authenticator")
        config = {
            "id": ua_execution["id"],
            "requirement": "REQUIRED",
            "displayName": "Univention Authenticator",
            "requirementChoices": ["REQUIRED", "DISABLED"],
            "configurable": True,
            "providerId": "univention-authenticator",
            "level": 0,
            "index": 2,
            "priority": 30,
        }
        self.kc_existing.update_authentication_flow_executions(
            payload=config,
            flow_alias=flow_alias,
        )

        # Configure UDM connection
        self.logger.info("Configuring UDM connection")
        udm_config = {
            "alias": "udm-config",
            "config": {
                "udm_endpoint": self.udm_url,
                "udm_user": self.udm_username,
                "udm_password": self.udm_password,
                "keycloak_federation_source_identifier": "univentionSourceIAM",
                "keycloak_federation_remote_identifier": "univentionObjectIdentifier",
            },
        }
        try:
            self.kc_existing.connection.raw_post(
                self.path + f'/admin/realms/{self.existing_realm}/authentication/executions/{ua_execution["id"]}/config',
                data=json.dumps(udm_config),
            )
        except KeycloakPostError as e:
            self.logger.error("Failed to configure UDM connection: %s", e)
            raise

    def setup_user_profile_attributes(self, realm: str, is_dummy_realm: bool) -> None:
        """Set up user profile attributes for a realm."""
        self.logger.info("Setting up user profile attributes for realm: %s", realm)
        kc = self.kc_dummy if is_dummy_realm else self.kc_existing

        if not kc:
            raise KeycloakError("Keycloak admin connection not initialized")

        try:
            user_profile = kc.connection.raw_get(self.path + f"/admin/realms/{realm}/users/profile").json()
        except KeycloakError as e:
            self.logger.error("Failed to get user profile for realm %s: %s", realm, e)
            raise

        attributes_to_add = []
        if is_dummy_realm:
            attributes_to_add = [
                {
                    "name": "uid",
                    "displayName": "${profile.attributes.uid}",
                    "permissions": {"view": [], "edit": ["admin"]},
                    "validations": {},
                    "annotations": {},
                    "multivalued": False,
                },
                {
                    "name": "uuid_remote",
                    "displayName": "${profile.attributes.uuid_remote}",
                    "permissions": {"view": [], "edit": ["admin"]},
                    "validations": {},
                    "annotations": {},
                    "multivalued": False,
                },
            ]
        else:
            attributes_to_add = [
                {
                    "name": "univentionSourceIAM",
                    "displayName": "${profile.attributes.univentionSourceIAM}",
                    "permissions": {"view": [], "edit": ["admin"]},
                    "validations": {},
                    "annotations": {},
                    "multivalued": False,
                },
                {
                    "name": "objectGUID",
                    "displayName": "${profile.attributes.objectGUID}",
                    "permissions": {"view": [], "edit": ["admin"]},
                    "validations": {},
                    "annotations": {},
                    "multivalued": False,
                },
            ]

        existing_attributes = user_profile.get("attributes", [])
        for attr in attributes_to_add:
            if not any(existing_attr["name"] == attr["name"] for existing_attr in existing_attributes):
                existing_attributes.append(attr)
            else:
                self.logger.info("Attribute %s already exists in realm %s", attr["name"], realm)

        user_profile["attributes"] = existing_attributes
        try:
            kc.connection.raw_put(self.path + f"/admin/realms/{realm}/users/profile", data=json.dumps(user_profile))
            self.logger.info("User profile updated for realm %s", realm)
        except KeycloakError as e:
            self.logger.error("Failed to update user profile for realm %s: %s", realm, e)
            raise

    def setup_user_attributes(self) -> None:
        """Set up user attributes in the existing realm."""
        if not self.kc_existing:
            raise KeycloakError("Keycloak admin connection to existing realm not initialized")
        attributes = [
            {"name": "username", "displayName": "${username}"},
            {"name": "email", "displayName": "${email}"},
            {"name": "firstName", "displayName": "${firstName}"},
            {"name": "lastName", "displayName": "${lastName}"},
            {"name": "univentionSourceIAM", "displayName": "${profile.attributes.univentionSourceIAM}"},
            {"name": "objectGUID", "displayName": "${profile.attributes.objectGUID}"},
        ]

        for attr in attributes:
            scope_name = attr["name"]
            try:
                client_scopes = self.kc_existing.get_client_scopes()
                existing_scope = next((scope for scope in client_scopes if scope["name"] == scope_name), None)

                if existing_scope:
                    self.logger.info("Client scope '%s' already exists", scope_name)
                    scope_id = existing_scope["id"]
                else:
                    scope_payload = {
                        "name": scope_name,
                        "protocol": "openid-connect",
                        "attributes": {
                            "include.in.token.scope": "true",
                            "display.on.consent.screen": "true",
                        },
                    }
                    scope_id = self.kc_existing.create_client_scope(scope_payload)
                    self.logger.info("Created client scope: %s", scope_name)

                existing_mappers = self.kc_existing.get_mappers_from_client_scope(scope_id)
                mapper_exists = any(m["name"] == attr["name"] for m in existing_mappers)

                if not mapper_exists:
                    mapper_payload = {
                        "name": attr["name"],
                        "protocol": "openid-connect",
                        "protocolMapper": "oidc-usermodel-attribute-mapper",
                        "consentRequired": False,
                        "config": {
                            "userinfo.token.claim": "true",
                            "user.attribute": attr["name"],
                            "id.token.claim": "true",
                            "access.token.claim": "true",
                            "claim.name": attr["name"],
                            "jsonType.label": "String",
                        },
                    }
                    self.kc_existing.add_mapper_to_client_scope(scope_id, mapper_payload)
                    self.logger.info("Added mapper to client scope: %s", attr)
                else:
                    self.logger.info("Mapper '%s' already exists for client scope '%s'", attr["name"], scope_name)
            except KeycloakError as e:
                self.logger.error("Failed to setup attribute %s: %s", attr, e)
                raise

    def setup_idp_mappers(self) -> None:
        """Set up IDP mappers in the existing realm."""
        if not self.kc_existing:
            raise KeycloakError("Keycloak admin connection to existing realm not initialized")
        mappers = [
            {
                "name": "uid",
                "identityProviderMapper": "oidc-username-idp-mapper",
                "config": {
                    "template": "external-${ALIAS}-${CLAIM.sAMAccountName}",
                    "syncMode": "IMPORT",
                },
            },
            {
                "name": "email",
                "identityProviderMapper": "oidc-user-attribute-idp-mapper",
                "config": {
                    "claim": "email",
                    "user.attribute": "email",
                    "syncMode": "INHERIT",
                },
            },
            {
                "name": "firstName",
                "identityProviderMapper": "oidc-user-attribute-idp-mapper",
                "config": {
                    "claim": "given_name",
                    "user.attribute": "firstName",
                    "syncMode": "INHERIT",
                },
            },
            {
                "name": "lastName",
                "identityProviderMapper": "oidc-user-attribute-idp-mapper",
                "config": {
                    "claim": "family_name",
                    "user.attribute": "lastName",
                    "syncMode": "INHERIT",
                },
            },
            {
                "name": "source_iam",
                "identityProviderMapper": "hardcoded-attribute-idp-mapper",
                "config": {
                    "attribute": "univentionSourceIAM",
                    "attribute.value": f"Federation from {self.dummy_realm}",
                },
            },
            {
                "name": "objectid",
                "identityProviderMapper": "oidc-user-attribute-idp-mapper",
                "config": {
                    "claim": "uuid_remote",
                    "user.attribute": "objectGUID",
                    "syncMode": "IMPORT",
                },
            },
        ]

        idp_alias = f"oidc-{self.dummy_realm}"
        try:
            existing_mappers = self.kc_existing.get_idp_mappers(idp_alias)
            existing_mapper_names = {mapper["name"] for mapper in existing_mappers}
        except Exception as e:
            self.logger.warning("Could not retrieve existing mappers: %s", e)
            existing_mapper_names = set()

        for mapper in mappers:
            mapper["identityProviderAlias"] = idp_alias
            if mapper["name"] not in existing_mapper_names:
                try:
                    self.kc_existing.add_mapper_to_idp(
                        idp_alias=idp_alias,
                        payload=mapper,
                    )
                    self.logger.info("Added IDP mapper: %s", mapper["name"])
                except KeycloakError as e:
                    self.logger.error("Failed to add mapper %s: %s", mapper["name"], e)
            else:
                self.logger.info("IDP mapper %s already exists, skipping", mapper["name"])

    def setup_client_mappers(self, client_id: str) -> None:
        """Set up client mappers for the federation client."""
        if not self.kc_dummy:
            raise KeycloakError("Keycloak admin connection to dummy realm not initialized")
        mappers = [
            {
                "name": "uid",
                "protocol": "openid-connect",
                "protocolMapper": "oidc-usermodel-attribute-mapper",
                "config": {
                    "user.attribute": "uid",
                    "claim.name": "sAMAccountName",
                    "jsonType.label": "String",
                    "access.token.claim": "true",
                    "id.token.claim": "true",
                },
            },
            {
                "name": "uuid_remote",
                "protocol": "openid-connect",
                "protocolMapper": "oidc-usermodel-attribute-mapper",
                "config": {
                    "user.attribute": "uuid_remote",
                    "claim.name": "uuid_remote",
                    "jsonType.label": "String",
                    "access.token.claim": "true",
                    "id.token.claim": "true",
                },
            },
        ]

        try:
            existing_mappers = self.kc_dummy.get_mappers_from_client(client_id)
            existing_mapper_names = {mapper["name"] for mapper in existing_mappers}
        except Exception as e:
            self.logger.warning("Could not retrieve existing client mappers: %s", e)
            existing_mapper_names = set()

        for mapper in mappers:
            if mapper["name"] not in existing_mapper_names:
                try:
                    self.kc_dummy.add_mapper_to_client(client_id, mapper)
                    self.logger.info("Added client mapper: %s", mapper["name"])
                except KeycloakError as e:
                    self.logger.error("Failed to add client mapper %s: %s", mapper["name"], e)
            else:
                self.logger.info("Client mapper %s already exists, skipping", mapper["name"])

    def remove_dummy_realm(self) -> None:
        """Remove the dummy realm created during setup."""
        self.logger.info("Removing dummy realm: %s", self.dummy_realm)
        try:
            self.kc_master.delete_realm(self.dummy_realm)
            self.logger.info("Successfully removed dummy realm: %s", self.dummy_realm)
        except KeycloakError as e:
            if e.response_code == 404:
                self.logger.info("Dummy realm '%s' doesn't exist, nothing to remove", self.dummy_realm)
            else:
                self.logger.error("Failed to remove dummy realm '%s': %s", self.dummy_realm, e)
                raise

    def remove_identity_provider(self) -> None:
        """Remove the Identity Provider (IDP) from the existing realm."""
        if not self.kc_existing:
            self.kc_existing = self._create_keycloak_admin(self.existing_realm, "master")

        idp_alias = f"oidc-{self.dummy_realm}"
        self.logger.info("Removing identity provider: %s from realm: %s", idp_alias, self.existing_realm)

        try:
            self.kc_existing.delete_idp(idp_alias)
            self.logger.info("Successfully removed identity provider: %s", idp_alias)
        except KeycloakError as e:
            if e.response_code == 404:
                self.logger.info("Identity provider '%s' doesn't exist, nothing to remove", idp_alias)
            else:
                self.logger.error("Failed to remove identity provider '%s': %s", idp_alias, e)
                raise

    def remove_authentication_flow(self) -> None:
        """Remove the authentication flow from the existing realm."""
        if not self.kc_existing:
            self.kc_existing = self._create_keycloak_admin(self.existing_realm, "master")

        flow_alias = "adhoc"
        self.logger.info("Removing authentication flow: %s from realm: %s", flow_alias, self.existing_realm)

        try:
            # First, get all authentication flows to find the ID
            flows = self.kc_existing.get_authentication_flows()
            flow = next((f for f in flows if f["alias"] == flow_alias), None)

            if flow:
                flow_id = flow["id"]
                self.kc_existing.connection.raw_delete(
                    self.path + f"/admin/realms/{self.existing_realm}/authentication/flows/{flow_id}",
                )
                self.logger.info("Successfully removed authentication flow: %s", flow_alias)
            else:
                self.logger.info("Authentication flow '%s' doesn't exist, nothing to remove", flow_alias)
        except KeycloakError as e:
            self.logger.error("Failed to remove authentication flow '%s': %s", flow_alias, e)
            raise

    def setup(self) -> None:
        """Main setup method to configure the ad-hoc federation."""
        try:
            self.logger.info("Starting Keycloak federation setup")

            # Create dummy realm
            self.logger.info("Creating dummy realm: %s", self.dummy_realm)
            self.kc_master.create_realm(
                payload=self._get_realm_payload(self.dummy_realm),
                skip_exists=True,
            )

            # Initialize connections to other realms
            self.kc_dummy = self._create_keycloak_admin(self.dummy_realm, "master")
            self.kc_existing = self._create_keycloak_admin(self.existing_realm, "master")

            # Set up user profile attributes for dummy realm
            self.setup_user_profile_attributes(self.dummy_realm, is_dummy_realm=True)

            # Create test user in dummy realm
            self.logger.info("Creating test user in dummy realm")
            try:
                self.kc_dummy.create_user(
                    self._get_test_user_payload("test_adhoc", "univention", "RSlyYLgv5Em10MKDijkDZQ=="),
                )
            except KeycloakError as e:
                if e.response_code != 409:  # Ignore if user already exists
                    raise

            # Create federation client in dummy realm
            self.logger.info("Creating federation client")
            client_payload = {
                "clientId": "federation-client",
                "enabled": True,
                "protocol": "openid-connect",
                "publicClient": False,
                "directAccessGrantsEnabled": True,
                "standardFlowEnabled": True,
                "implicitFlowEnabled": False,
                "serviceAccountsEnabled": False,
                "redirectUris": ["*"],
            }
            try:
                self.kc_dummy.create_client(client_payload)
            except KeycloakError as e:
                if e.response_code != 409:
                    raise

            # Get client secret
            clients = self.kc_dummy.get_clients()
            client = next(c for c in clients if c["clientId"] == "federation-client")
            client_secret = self.kc_dummy.get_client_secrets(client["id"])["value"]

            # Set up user profile attributes for existing realm
            self.setup_user_profile_attributes(self.existing_realm, is_dummy_realm=False)

            # Set up user attributes
            self.setup_user_attributes()

            # Set up authentication flow
            self.logger.info("Setting up Univention authenticator flow")
            self.setup_univention_auth_flow()

            # Set up IDP
            self.logger.info("Setting up Identity Provider in realm: %s", self.existing_realm)
            idp_payload = self._get_idp_payload(client_secret)
            try:
                self.kc_existing.create_idp(idp_payload)
            except KeycloakError as e:
                if e.response_code != 409:
                    raise

            # Set up IDP mappers
            self.logger.info("Setting up IDP mappers")
            self.setup_idp_mappers()

            # Set up client mappers
            client_id = self.kc_dummy.get_client_id("federation-client")
            self.setup_client_mappers(client_id)

            self.logger.info("Keycloak federation setup completed successfully")

        except Exception as e:
            self.logger.exception("Setup failed: %s", e)
            raise

    def cleanup(self) -> None:
        """Main cleanup method to remove all federation components."""
        try:
            self.logger.info("Starting Keycloak federation cleanup")
            self.remove_identity_provider()
            self.remove_authentication_flow()
            self.remove_dummy_realm()
            self.logger.info("Keycloak federation cleanup completed successfully")
        except Exception as e:
            self.logger.exception("Cleanup failed: %s", e)
            raise


def main():
    """Example usage of AdHocProvisioning class."""
    import argparse

    parser = argparse.ArgumentParser(description="Setup Keycloak federation")
    parser.add_argument("--keycloak-url", required=True, help="Base Keycloak URL")
    parser.add_argument("--admin-username", default="admin", help="Keycloak admin username")
    parser.add_argument("--admin-password", required=True, help="Keycloak admin password")
    parser.add_argument("--existing-realm", default="nubus", help="Existing realm name")
    parser.add_argument("--dummy-realm", default="adhoc", help="Dummy realm name")
    parser.add_argument("--udm-url", required=True, help="UDM API URL")
    parser.add_argument("--udm-username", required=True, help="UDM username")
    parser.add_argument("--udm-password", required=True, help="UDM password")

    args = parser.parse_args()

    provisioner = AdHocProvisioning(
        keycloak_url=args.keycloak_url,
        admin_username=args.admin_username,
        admin_password=args.admin_password,
        udm_url=args.udm_url,
        udm_username=args.udm_username,
        udm_password=args.udm_password,
        existing_realm=args.existing_realm,
        dummy_realm=args.dummy_realm,
    )
    provisioner.setup()


if __name__ == "__main__":
    main()
