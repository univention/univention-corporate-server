#!/bin/bash

set -x -e
export KVM_USER="build"

cd test

# update packages
#./utils/build-branch-packages -g $GIT_BRANCH
ssh jenkins@10.200.4.18 python3 build -r "https://gitlab+deplay-token-2:FAd2WHRZQqYFzLMZd5Q1@git.knut.univention.de/univention/ucs.git" -b "$GIT_BRANCH" > utils/apt-get-branch-repo.list
# echo "# ignore" > utils/apt-get-branch-repo.list

declare -a cmd=("./ucs-ec2-tools/ucs-kvm-create" "-c" "branch-tests/base/$CFG_FILE")
"$HALT" && cmd+=("-t")
"${cmd[@]}"
test -e "./COMMAND_SUCCESS"
