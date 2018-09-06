#!/bin/bash

set -x -e
export KVM_USER="build"

cd test

# update packages
ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no jenkins@10.200.18.180 python3 /home/jenkins/build -r "https://gitlab+deplay-token-2:FAd2WHRZQqYFzLMZd5Q1@git.knut.univention.de/univention/ucs.git" -b "$GIT_BRANCH" > utils/apt-get-branch-repo.list
# echo "# ignore" > utils/apt-get-branch-repo.list

declare -a cmd=("./ucs-ec2-tools/ucs-kvm-create" "-c" "branch-tests/base/$CFG_FILE")
"$HALT" && cmd+=("-t")
"${cmd[@]}"
test -e "./COMMAND_SUCCESS"
