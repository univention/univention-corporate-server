#!/bin/bash

set -x
set -e

cfg_file="$(mktemp)"
export UCS_ENV_VEYON_WINDOWS_HOST="${UCS_ENV_VEYON_WINDOWS_HOST:=3}"
export KVM_BUILD_SERVER="${KVM_BUILD_SERVER:=ranarp.knut.univention.de}"
export HALT=false
export UCS_TEST_RUN=false

# 4.4 support
ucs44="${UCS44:=false}"
if $ucs44; then
	export UCS_VERSION="4.4-9"
	export KVM_TEMPLATE="generic-unsafe"
	export KVM_UCSVERSION="4.4-9"
	export TARGET_VERSION="4.4-9"
fi

# user specific instances "username_..."
if [ -n "$BUILD_USER_ID" ]; then
	export KVM_OWNER="$BUILD_USER_ID"
fi

# extra label for instances names so that the instances
# are user specific
if [ -n "$BUILD_URL" ]; then
	# -> if started via jenkins KVM_LABEL_SUFFIX="username_"
	USER="$(curl -k -s "$BUILD_URL/api/json" | awk -F '"userId":"' '{print $2}'| awk -F '"' '{print $1}')_"
	export USER="$USER"
fi

./scenarios/veyon/create_veyon_cfg.py  \
	-w "$UCS_ENV_VEYON_WINDOWS_HOST" \
	-v kvm > "$cfg_file"
exec ./utils/start-test.sh "$cfg_file"
