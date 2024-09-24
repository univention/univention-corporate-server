#!/bin/bash

set -x
set -e

export KVM_BUILD_SERVER="${KVM_BUILD_SERVER:=tross.knut.univention.de}"
export TERMINATE=false
export DOCKER=true
export REPLACE=true
export UCS_TEST_RUN=false

# user specific instances "username_..."
export KVM_OWNER="${BUILD_USER_ID:=$USER}"
export JOB_BASE_NAME="${JOB_BASE_NAME:=ucs-adconnector-w2k19-env}"
export AD_BASE="${AD_BASE:=ad.test}"

exec ./utils/start-test.sh scenarios/base/ucs-ad-connector-w2k19.cfg
