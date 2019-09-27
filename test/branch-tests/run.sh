#!/bin/bash

set -e
set -x

env

getGitlabURL () {
	local fn
	local product="$1"
	fn="${HOME}/secrets/gitlab_${product}.url"
	if [ ! -f "$fn" ] ; then
		echo "ERROR: the gitlab secret file for $product ($fn) does not exist or is no file!"
		exit 1
	fi
	cat "$fn"
}

get_ucsschool_git_checkout () {
	if [ -z "$WORKSPACE" ] ; then
		echo "ERROR: \$WORKSPACE is empty"
		exit 1
	fi
	echo ">>> performing cleanup"
	[ -n "$WORKSPACE" ] && rm -Rf "${WORKSPACE}/${GIT_DIR_UCSSCHOOL}"
	echo ">>> create repo"
	git init "${WORKSPACE}/${GIT_DIR_UCSSCHOOL}"
	echo ">>> set referenced repo / reuse local repo"
	echo "/var/lib/jenkins/LOCAL/ucsschool.git/objects" > "${WORKSPACE}/${GIT_DIR_UCSSCHOOL}/.git/objects/info/alternates"
	echo ">>> fetch UCS@school (feature) branch"
	(
		cd "${WORKSPACE}/${GIT_DIR_UCSSCHOOL}"
		git fetch --no-tags --progress "$REPO_UCSSCHOOL" "+refs/heads/${UCSSCHOOL_BRANCH}:refs/remotes/origin/${UCSSCHOOL_BRANCH}" --depth=1
		echo ">>> perform a sparse checkout"
		git config core.sparsecheckout true
		echo "test/*" >> .git/info/sparse-checkout
		git checkout -b "$UCSSCHOOL_BRANCH" "origin/$UCSSCHOOL_BRANCH"
		echo ">>> UCS@school checkout done"
	)
}


export KVM_USER="build"
REPO_UCS="$(getGitlabURL ucs)"
REPO_UCSSCHOOL="$(getGitlabURL ucsschool)"
GIT_DIR_UCSSCHOOL="ucsschool.git"
BUILD_HOST="10.200.18.180"

# if the default branch of UCS@school is given, then build UCS else build UCS@school
if echo "$UCSSCHOOL_BRANCH" | egrep -q "^[0-9].[0-9]$" ; then
	BUILD_BRANCH="$UCS_BRANCH"
	BUILD_REPO="$REPO_UCS"
else
	BUILD_BRANCH="$UCSSCHOOL_BRANCH"
	BUILD_REPO="$REPO_UCSSCHOOL"
fi

get_ucsschool_git_checkout

# copy UCS@school specific files to UCS test directory
[ -d "$GIT_DIR_UCSSCHOOL/test" ] && cp -Rav "$GIT_DIR_UCSSCHOOL/test/"* "test/"

cd test

# update packages
ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no "jenkins@${BUILD_HOST}" python3 /home/jenkins/build -r "${BUILD_REPO}" -b "${BUILD_BRANCH}" > utils/apt-get-branch-repo.list || exit 1

# replace non deb lines
sed -i '/^deb /!d' utils/apt-get-branch-repo.list

release=4.4-2

export TEMPLATE_VERSION="${TEMPLATE_VERSION:=$release}"
export TEMPLATE_NAME="${TEMPLATE_NAME:=generic-unsafe}"
export UCS_VERSION="${UCS_VERSION:=$release}"
export TARGET_VERSION="${UCS_VERSION}"
export RELEASE_UPDATE="${release_update:=public}"
export ERRATA_UPDATE="${errata_update:=testing}"

declare -a cmd=("./ucs-ec2-tools/ucs-kvm-create" "-c" "$CFG_FILE")
"$HALT" && cmd+=("-t")
"${cmd[@]}"
test -e "./COMMAND_SUCCESS"
