#!/bin/bash

set -x

export RELEASE_UPDATE="${release_update:-public}"
export ERRATA_UPDATE="${errata_update:-testing}"
export TARGET_VERSION=${TARGET_VERSION:-4.4-0}
export UCS_VERSION=${UCS_VERSION:-4.4-0}
export TEMPLATE_VERSION=${TEMPLATE_VERSION:-$TARGET_VERSION}
export KVM_BUILD_SERVER=${KVM_BUILD_SERVER:-lattjo.knut.univention.de}
export KVM_USER=${KVM_USER:-$USER}
export HALT=${HALT:-true}
export CFG=$1

# create the command and run in ec2 or kvm depending on cfg
grep -q kvm_template "$CFG"
if [ "$?" -eq 1 ]; then
	declare -a cmd=("./ucs-ec2-tools/ucs-ec2-create" "-c")
else
	declare -a cmd=("./ucs-ec2-tools/ucs-kvm-create" "-c")
fi
cmd+=($CFG)
"$HALT" && cmd+=("-t")
"${cmd[@]}"
test -e "./COMMAND_SUCCESS"
