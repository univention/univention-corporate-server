#!/bin/bash

# start with
#  -> export UCS_ENV_SELFDISCLOSURE_IP=10.207...
#     export UCS_ENV_PRIMARY_IP=10.207...
#     export UCS_ENV_PROVISIONING_IP=10.207...
#     export UCS_ENV_TRAEGER1_IP=10.207...
#     export UCS_ENV_TRAEGER2_IP=10.207...
#     export UCS_ENV_KEYCLOAK_IP=10.207...
#     ./utils/start-id-broker-performance-tests-local.sh

export UCS_ENV_ID_BROKER_STAGING=local
export UCS_TEST_RUN=false
export UCS_ENV_IDBROKER_DOMAIN=broker.local
export UCS_ENV_TRAEGER1_DOMAIN=traeger1.local
export UCS_ENV_TRAEGER2_DOMAIN=traeger2.local
export UCS_ENV_PASSWORD=univention
export KVM_KEYPAIR_PASSPHRASE=univention
export DOCKER=true

cfg_file="$(mktemp)"
python3 ./utils/create-id-broker-performance-test-cfg.py > "$cfg_file"
exec ./utils/start-test.sh "$cfg_file"
