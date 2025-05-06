#!/bin/bash
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2022-2025 Univention GmbH
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

set -x
set -e

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
    TOKEN=$(curl -d "client_id=$CLIENT_ID" \
         -d "username=$BINDUSER" \
         -d "password=$BINDPWD" \
         -d "grant_type=password" \
         "$KEYCLOAK_URL" | sed 's/.*"access_token":"\([[:alnum:]\.-_-]*\)".*/\1/')
    # create app
    curl -X POST \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $TOKEN" \
        -d '{"name":"udm", "display_name":"UDM"}' \
        "$MANAGEMENT_SERVER/apps/register"
    # create namespace
    curl -X POST \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $TOKEN" \
        -d '{"name":"default", "display_name":"Default"}' \
        "$MANAGEMENT_SERVER/namespaces/udm"
    # roles
    curl -X POST \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $TOKEN" \
        -d '{"name":"ouadmin", "display_name":"OU admin"}' \
        "$MANAGEMENT_SERVER/roles/udm/default"
    curl -X POST \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $TOKEN" \
        -d '{"name":"create_target", "display_name":"Create target object"}' \
        "$MANAGEMENT_SERVER/permissions/udm/default"
    curl -X POST \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $TOKEN" \
        -d '{
              "name": "ouadmin_can_create_object",
              "display_name": "OU admin can create object",
              "role": {
                "app_name": "udm",
                "namespace_name": "default",
                "name": "ouadmin"
              },
              "conditions": [],
              "relation": "AND",
              "permissions": [
                {
                  "app_name": "udm",
                  "namespace_name": "default",
                  "name": "create_target"
                }
               ]
            }' \
        "$MANAGEMENT_SERVER/capabilities/udm/default"
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

    token=$(curl -d "client_id=$CLIENT_ID" \
        -d "username=$BINDUSER" \
        -d "password=$BINDPWD" \
        -d "grant_type=password" \
     "$KEYCLOAK_URL" | sed 's/.*"access_token":"\([[:alnum:]\.-_-]*\)".*/\1/')

    # check permission
    time curl -X POST \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $token" \
        -d '{
              "namespaces": [
                {
                  "app_name": "udm",
                  "name": "default"
                }
              ],
              "actor": {
                "id": "ariel",
                "roles": [
                  {
                    "app_name": "udm",
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
                    "app_name": "udm",
                    "namespace_name": "default",
                    "name": "create_target"
                  }
                ],
              "general_permissions_to_check": [
                  {
                    "app_name": "udm",
                    "namespace_name": "default",
                    "name": "create_target"
                  }
              ],
              "extra_request_data": {}
            }' \
    "$AUTHORIZATION_SERVER/permissions/check"
}
