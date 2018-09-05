#!/bin/bash

set -x -e
export KVM_USER="build"

cd test

# update packages
#./build-branch-packages -g $GIT_BRANCH
export APT_REPO="$(ls -la)"

declare -a cmd=("./ucs-ec2-tools/ucs-kvm-create" "-c" "branch-tests/base/$CFG_FILE")
"$HALT" && cmd+=("-t")
"${cmd[@]}"
test -e "./COMMAND_SUCCESS"
