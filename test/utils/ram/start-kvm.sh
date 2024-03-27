#!/bin/bash

set -x
set -e

export KVM_BUILD_SERVER="${KVM_BUILD_SERVER:=tross.knut.univention.de}"
export TERMINATE=false
export DOCKER=true
export REPLACE=true
export UCS_TEST_RUN=false
export UCS_TEST_APPCENTER="${UCS_TEST_APPCENTER:=true}"

# user specific instances "username_..."
export KVM_OWNER="${BUILD_USER_ID:=$USER}"
export JOB_BASE_NAME="${JOB_BASE_NAME:=ram-env}"

exec ./utils/start-test.sh scenarios/autotest-248-ram-rankine.cfg
