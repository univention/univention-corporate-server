#!/bin/bash

set -x

export RELEASE_UPDATE="${release_update:-public}"
export ERRATA_UPDATE="${errata_update:-testing}"
export TARGET_VERSION=${TARGET_VERSION:-4.4-0}
export UCS_VERSION=${UCS_VERSION:-4.4-0}
export HALT=${HALT:-true}
export CFG=$1

# create the command and run ucs ec2
declare -a cmd=("./ucs-ec2-tools/ucs-ec2-create" "-c")
cmd+=($CFG)
"$HALT" && cmd+=("-t")
"${cmd[@]}"
test -e "./COMMAND_SUCCESS"
