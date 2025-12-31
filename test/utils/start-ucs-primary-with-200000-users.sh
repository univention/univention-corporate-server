#!/bin/bash
# SPDX-FileCopyrightText: 2025-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

set -x
set -e

export KVM_BUILD_SERVER="${KVM_BUILD_SERVER:=tross.knut.univention.de}"
export TERMINATE=false
export DOCKER=true
export REPLACE=true
export UCS_TEST_RUN=false

# user specific instances "username_..."
export KVM_OWNER="${BUILD_USER_ID:=$USER}"
export JOB_BASE_NAME="${JOB_BASE_NAME:=ucs-primary-with-200000-users}"

exec ./utils/start-test.sh scenarios/base/ucs-primary-with-200000-users.cfg
