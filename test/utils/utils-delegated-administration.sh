#!/bin/bash
# SPDX-FileCopyrightText: 2025-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

set -ex

guardian_curl () {
    # guardian_curl "$TOKEN" ...
    TOKEN="$1"
    shift
    curl -X POST \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $TOKEN" \
        "$@"
}

guardian_get_token () {
    # guardian_get_token "$CLIENT_ID" "$BINDUSER" "$BINDPWD" "$KEYCLOAK_URL"
    curl -d "client_id=$1" \
         -d "username=$2" \
         -d "password=$3" \
         -d "grant_type=password" \
         "$4" | sed 's/.*"access_token":"\([[:alnum:]\.-_-]*\)".*/\1/'
}

# create the configuration in guardian for delegative administration
# TODO we need to move this to some join script, this has to be part
#      of the product once we decide to use the guardian
guardian_configuration () {
    BINDUSER=Administrator
    BINDPWD=univention
    CLIENT_ID=guardian-scripts
    GUARDIAN_KEYCLOAK_URL=$(ucr get guardian-management-api/oauth/keycloak-uri)
    SYSTEM_KEYCLOAK_URL=$(ucr get keycloak/server/sso/fqdn)
    KEYCLOAK_BASE_URL=${GUARDIAN_KEYCLOAK_URL:-$SYSTEM_KEYCLOAK_URL}
    KEYCLOAK_URL="$KEYCLOAK_BASE_URL/realms/ucs/protocol/openid-connect/token"
    if [[ ! $KEYCLOAK_URL == http ]]; then
        KEYCLOAK_URL="https://$KEYCLOAK_URL"
    fi
    MANAGEMENT_SERVER="$(hostname).$(ucr get domainname)/guardian/management"
    TOKEN=$(guardian_get_token "$CLIENT_ID" "$BINDUSER" "$BINDPWD" "$KEYCLOAK_URL")
    # create app
    guardian_curl "$TOKEN" \
        -d '{"name":"demoapp", "display_name":"Univention Directory Manager"}' \
        "$MANAGEMENT_SERVER/apps/register"
    # create namespace
    guardian_curl "$TOKEN" \
        -d '{"name":"default", "display_name":"Default"}' \
        "$MANAGEMENT_SERVER/namespaces/demoapp"
    # roles
    guardian_curl "$TOKEN" \
        -d '{"name":"ouadmin", "display_name":"Organizational Unit (OU) Administrator"}' \
        "$MANAGEMENT_SERVER/roles/demoapp/default"
    guardian_curl "$TOKEN" \
        -d '{"name":"create_target", "display_name":"Create target object"}' \
        "$MANAGEMENT_SERVER/permissions/demoapp/default"
    guardian_curl "$TOKEN" \
        -d '{
              "name": "ouadmin_can_create_object",
              "display_name": "OU admin can create object",
              "role": {
                "app_name": "demoapp",
                "namespace_name": "default",
                "name": "ouadmin"
              },
              "conditions": [],
              "relation": "AND",
              "permissions": [
                {
                  "app_name": "demoapp",
                  "namespace_name": "default",
                  "name": "create_target"
                }
               ]
            }' \
        "$MANAGEMENT_SERVER/capabilities/demoapp/default"
}

# create the udm client for guardian in keycloak
# TODO we need to move this to some join script, this has to be part
#      of the product once we decide to use the guardian
guardian_service_client () {
    local password="univention"
    echo "$password" > /etc/guardian-udm-client.secret
    univention-keycloak oidc/rp create \
    --public-client --direct-access-grants --client-secret "$password" --add-guardian-audience-mapper udm-guardian
    # TODO manually add basic scope as default scope, see univention/ucs#2852
}

# just a test to see if we can ask guardian
guardian_check_permissions () {
    BINDUSER=Administrator
    BINDPWD=univention
    CLIENT_ID=udm-guardian
    GUARDIAN_KEYCLOAK_URL=$(ucr get guardian-management-api/oauth/keycloak-uri)
    SYSTEM_KEYCLOAK_URL=$(ucr get keycloak/server/sso/fqdn)
    KEYCLOAK_BASE_URL=${GUARDIAN_KEYCLOAK_URL:-$SYSTEM_KEYCLOAK_URL}
    KEYCLOAK_URL="$KEYCLOAK_BASE_URL/realms/ucs/protocol/openid-connect/token"
    if [[ ! $KEYCLOAK_URL == http ]]; then
        KEYCLOAK_URL="https://$KEYCLOAK_URL"
    fi
    AUTHORIZATION_SERVER="$(hostname).$(ucr get domainname)/guardian/authorization"

    TOKEN=$(guardian_get_token "$CLIENT_ID" "$BINDUSER" "$BINDPWD" "$KEYCLOAK_URL")

    # check permission
    time guardian_curl "$TOKEN" \
        -d '{
              "namespaces": [
                {
                  "app_name": "demoapp",
                  "name": "default"
                }
              ],
              "actor": {
                "id": "ariel",
                "roles": [
                  {
                    "app_name": "demoapp",
                    "namespace_name": "default",
                    "name": "ouadmin"
                  }
                ],
                "attributes": {
                  "id": "ariel"
                }
              },
              "targets": [
                {
                  "old_target": {
                    "id": "anniversary-cake-from-tristan",
                    "roles": [],
                    "attributes": {
                      "id": "anniversary-cake-from-tristan",
                      "orderer_id": "tristan",
                      "recipient_id": "ariel",
                      "notifications": true
                    }
                  },
                  "new_target": {
                    "id": "anniversary-cake-from-tristan",
                    "roles": [],
                    "attributes": {
                      "id": "anniversary-cake-from-tristan",
                      "orderer_id": "tristan",
                      "recipient_id": "ariel",
                      "notifications": false
                    }
                  }
                }
              ],
              "targeted_permissions_to_check": [
                  {
                    "app_name": "demoapp",
                    "namespace_name": "default",
                    "name": "create_target"
                  }
                ],
              "general_permissions_to_check": [
                  {
                    "app_name": "demoapp",
                    "namespace_name": "default",
                    "name": "create_target"
                  }
              ],
              "extra_request_data": {}
            }' \
    "$AUTHORIZATION_SERVER/permissions/check"
}
