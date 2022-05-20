#!/bin/bash

set -e

cfg_file="$(mktemp)"
export UCS_ENV_VEYON_WINDOWS_HOST="${UCS_ENV_VEYON_WINDOWS_HOST:=3}"
export KVM_BUILD_SERVER="EC2"

# shellcheck disable=SC1091
. scenarios/veyon/utils-veyon.sh

veyon_env=$(get_veyon_aws_instances)

# check for running ec2 instances
if [ -n "$veyon_env" ]; then
	echo "Veyon AWS instances still running!"
	echo "Will not start new instances until the old environment is deleted!"
	echo "$veyon_env"
	exit 1
fi

# start
#./scenarios/veyon/create_veyon_cfg.py  \
#	-w "$UCS_ENV_VEYON_WINDOWS_HOST" \
#	-v kvm > "$cfg_file"
#exec ./utils/start-test.sh "$cfg_file"
