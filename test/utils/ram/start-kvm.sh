#!/bin/bash

set -x
set -e

export KVM_BUILD_SERVER="${KVM_BUILD_SERVER:=ranarp.knut.univention.de}"
export HALT=false
export DOCKER=true
export REPLACE=true
export UCS_TEST_RUN=false

# user specific instances "username_..."
export KVM_OWNER="$BUILD_USER_ID"

exec ./utils/start-test.sh scenarios/autotest-248-ram-rankine.cfg