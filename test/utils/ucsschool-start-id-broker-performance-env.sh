#!/bin/bash
# SPDX-FileCopyrightText: 2025-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

# docker can't hanlde newline in env file, so replace
# newline witch DELIM
export UCS_ENV_LOCUST_VARS="${UCS_ENV_LOCUST_VARS//$'\n'/:DELIM:}"
export KVM_BUILD_SERVER="${KVM_BUILD_SERVER:=ranarp.knut.univention.de}"
export TERMINATE=false
export DOCKER=true
export REPLACE=true
export UCS_TEST_RUN=false

# user specific instances "username_..."
if [ -n "$BUILD_USER_ID" ]; then
	export KVM_OWNER="$BUILD_USER_ID"
fi

exec "${0%/*}/start-test.sh" ./scenarios/autotest-247-ucsschool-id-broker-perf-kvm.cfg
