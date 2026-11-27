#!/bin/bash
set -euxo pipefail
#
# SPDX-License-Identifier: AGPL-3.0-only
# SPDX-FileCopyrightText: 2021-2026 Univention GmbH
#
# Adapted from container-udm-rest/docker/udm-rest-api/entrypoint.d/50-ldap.sh.
# Reads LDAP_HOST/LDAP_PORT/LDAP_BASE_DN/TLS_MODE from the environment instead
# of `ucr get` — this image doesn't ship the ucr CLI.

############################################################
# TLS settings
TLS_MODE="${TLS_MODE:-off}"

case "${TLS_MODE}" in
  "secure")
    TLS_REQCERT="demand"
    ;;
  "unvalidated")
    TLS_REQCERT="allow"
    ;;
  "off")
    TLS_REQCERT="never"
    ;;
  *)
    echo "TLS_MODE must be one of: off, unvalidated, secure (got: ${TLS_MODE})"
    exit 1
esac

CA_DIR=""
if [[ "${TLS_MODE}" != "off" ]]; then
  CA_CERT_FILE=${CA_CERT_FILE:-/run/secrets/ca_cert}
  CA_DIR="/etc/univention/ssl/ucsCA"

  if [[ ! -f "${CA_CERT_FILE}" ]]; then
    echo "\$CA_CERT_FILE is not a file at ${CA_CERT_FILE}"
    exit 1
  fi

  mkdir --parents "${CA_DIR}"
  ln --symbolic --force "${CA_CERT_FILE}" "${CA_DIR}/CAcert.pem"
fi

############################################################
# LDAP client config
: "${LDAP_HOST:?LDAP_HOST must be set}"
: "${LDAP_PORT:?LDAP_PORT must be set}"
: "${LDAP_BASE_DN:?LDAP_BASE_DN must be set}"

mkdir -pv /etc/ldap
cat <<EOF > /etc/ldap/ldap.conf
# This file should be world readable but not world writable.

${CA_DIR:+TLS_CACERT /etc/univention/ssl/ucsCA/CAcert.pem}
TLS_REQCERT ${TLS_REQCERT}

URI ldap://${LDAP_HOST}:${LDAP_PORT}

BASE ${LDAP_BASE_DN}
EOF
chmod 0644 /etc/ldap/ldap.conf

############################################################
# LDAP admin secret (optional — not needed for machine-account auth)
LDAP_SECRET_FILE=${LDAP_SECRET_FILE:-/run/secrets/ldap_secret}
if [[ -f "${LDAP_SECRET_FILE}" ]]; then
  echo "Using LDAP admin secret from ${LDAP_SECRET_FILE}"
  ln --symbolic --force "${LDAP_SECRET_FILE}" /etc/ldap.secret
elif [[ -n "${LDAP_SECRET:-}" ]]; then
  echo "Using LDAP admin secret from env"
  echo -n "${LDAP_SECRET}" > /etc/ldap.secret
  chmod 0600 /etc/ldap.secret
else
  echo "No LDAP admin secret provided (not required for machine-account auth)"
fi

############################################################
# Machine account secret (used by UDM to check who is authorized)
MACHINE_SECRET_FILE=${MACHINE_SECRET_FILE:-/run/secrets/machine_secret}
if [[ -f "${MACHINE_SECRET_FILE}" ]]; then
  echo "Using LDAP machine secret from ${MACHINE_SECRET_FILE}"
  ln --symbolic --force "${MACHINE_SECRET_FILE}" /etc/machine.secret
elif [[ -n "${MACHINE_SECRET:-}" ]]; then
  echo "Using LDAP machine secret from env"
  echo -n "${MACHINE_SECRET}" > /etc/machine.secret
  chmod 0600 /etc/machine.secret
else
  echo "No LDAP machine secret found at ${MACHINE_SECRET_FILE} and \$MACHINE_SECRET not set!"
  exit 1
fi
