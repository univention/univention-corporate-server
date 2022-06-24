#!/bin/bash

set -x
set -e

export KVM_BUILD_SERVER="${KVM_BUILD_SERVER:=ranarp.knut.univention.de}"
export HALT=false
export DOCKER=true
export UCS_ENV_IDBROKER_DOMAIN=broker.local
export UCS_ENV_TRAEGER1_DOMAIN=traeger1.local
export UCS_ENV_TRAEGER2_DOMAIN=traeger2.local
export KVM_KEYPAIR_PASSPHRASE=univention
export UCS_ENV_PASSWORD=univention
export UCS_TEST_RUN=false

# TODO remove
export DIMAGE="docker-registry.knut.univention.de/ucs-ec2-tools:branch-fbotner-issue-13"

# extra label for instances names so that the instances
# are user specific
if [ -n "$BUILD_URL" ]; then
	my_name="$(curl -k -s "$BUILD_URL/api/json" | awk -F '"userId":"' '{print $2}'| awk -F '"' '{print $1}')"
	export UCS_ENV_UCS_KT_GET_USERNAME="${my_name}"
fi

exec ./utils/start-test.sh scenarios/autotest-247-ucsschool-id-broker.cfg
