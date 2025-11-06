#!/bin/bash
# SPDX-License-Identifier: AGPL-3.0-only
# SPDX-FileCopyrightText: 2023-2024 Univention GmbH

set -euo pipefail

# require environment variables to be set
if [[ -z "${LDAP_HOST:-}" ]]; then
  echo "Please set the environment variable LDAP_HOST"
  exit 126
fi

if [[ -z "${LDAP_PORT:-}" ]]; then
  echo "Please set the environment variable LDAP_PORT"
  exit 126
fi

if [[ -f /run/secrets/idp_ldap_user_secret ]]; then
  LDAP_SECRET=$(cat /run/secrets/idp_ldap_user_secret)
elif [[ -z "${LDAP_SECRET:-}" ]]; then
  echo "Please either provide the file /run/secrets/idp_ldap_user_secret"
  echo "or set the environment variable LDAP_SECRET."
  exit 126
fi

if [[ -z "${LDAP_BASE_DN:-}" ]]; then
  echo "Please set the environment variable LDAP_BASE_DN"
  exit 126
fi

if [ ! -d /opt/keycloak/data/h2 ]; then
    # Keycloak has not run before.
    # Prepare realm import.
    mkdir --parents /opt/keycloak/data/import
    jq  " \
          .components.\"org.keycloak.storage.UserStorageProvider\"[0].config.bindDn = [\"uid=sys-idp-user,cn=users,$LDAP_BASE_DN\"] \
        | .components.\"org.keycloak.storage.UserStorageProvider\"[0].config.bindCredential = [\"$LDAP_SECRET\"] \
        | .components.\"org.keycloak.storage.UserStorageProvider\"[0].config.connectionUrl = [\"ldap://$LDAP_HOST:$LDAP_PORT\"] \
        | .components.\"org.keycloak.storage.UserStorageProvider\"[0].config.usersDn = [\"$LDAP_BASE_DN\"] \
        " \
        /opt/keycloak/realm-export.json \
        > /opt/keycloak/data/import/realm-import.json
else
    # Keycloak has run before.
    # Remove realm import, so that it does not overwrite custom settings.
    rm -rf /opt/keycloak/data/import
fi

exec "$@"
