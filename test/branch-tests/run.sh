#!/bin/bash

set -e
set -x

env

# LOCAL_UCS='/var/lib/jenkins/LOCAL/ucs.git'
LOCAL_UAS='/var/lib/jenkins/LOCAL/ucsschool.git'

die () {
	echo "${0##*/} ERROR: $*" >&2
	exit 1
}

getGitlabURL () {
	local product="$1"
	local fn="${HOME}/secrets/gitlab_${product}.url"
	[ -f "$fn" ] ||
		die "the gitlab secret file for $product ($fn) does not exist or is no file!"
	cat "$fn"
}

get_ucsschool_git_checkout () {
	[ -n "${UCSSCHOOL_BRANCH}" ] ||
		return 0
	[ -n "${WORKSPACE:-}" ] ||
		die "\$WORKSPACE is empty"
	local UAS="${WORKSPACE}/${GIT_DIR_UCSSCHOOL}"
	echo ">>> performing cleanup"
	[ -n "$WORKSPACE" ] && rm -rf "$UAS"
	echo ">>> create repo"
	git clone \
		--progress \
		--branch "$UCSSCHOOL_BRANCH" \
		--reference "$LOCAL_UAS" \
		--single-branch \
		--no-checkout \
		--depth 1 \
		--config remote.origin.tagOpt=--no-tags \
		--config core.sparsecheckout=true \
		"$REPO_UCSSCHOOL" "$UAS"
	#	--no-tags \
	echo ">>> fetch UCS@school (feature) branch"
	(
		cd "$UAS"
		echo ">>> perform a sparse checkout"
		echo "test/*" >> .git/info/sparse-checkout
		git checkout "$UCSSCHOOL_BRANCH"
		echo ">>> UCS@school checkout done"
	)
}


export KVM_USER="build"
REPO_UCS="$(getGitlabURL ucs)"
REPO_UCSSCHOOL="$(getGitlabURL ucsschool)"
GIT_DIR_UCSSCHOOL="ucsschool.git"
BUILD_HOST='buildvm.knut.univention.de'

# if the default branch of UCS@school is given, then build UCS else build UCS@school
case "$UCSSCHOOL_BRANCH" in
''|[0-9].[0-9])
	BUILD_BRANCH="$UCS_BRANCH"
	BUILD_REPO="$REPO_UCS"
	;;
*)
	BUILD_BRANCH="$UCSSCHOOL_BRANCH"
	BUILD_REPO="$REPO_UCSSCHOOL"
	;;
esac

get_ucsschool_git_checkout

# copy UCS@school specific files to UCS test directory
[ -d "$GIT_DIR_UCSSCHOOL/test" ] && cp -Rav "$GIT_DIR_UCSSCHOOL/test/"* "test/"

cd test

# update packages
ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no "jenkins@${BUILD_HOST}" \
	python3 /home/jenkins/build -r "${BUILD_REPO}" -b "${BUILD_BRANCH}" > utils/apt-get-branch-repo.list ||
	die "Failed building packages"

# replace non deb lines
sed -i '/^deb /!d' utils/apt-get-branch-repo.list

release='5.0-1'

sections=''
parse_sections () {
	local arg
	local IFS=' ,'
	# shellcheck disable=SC2048
	for arg in $*  # IFS
	do
		case "$arg" in
			-s|--section) continue ;;
			*) sections="${sections:+$sections }-s $arg" ;;
		esac
  done
}
parse_sections "${TEST_SECTIONS:-}"

export TEMPLATE_VERSION="${TEMPLATE_VERSION:=$release}"
export TEMPLATE_NAME="${TEMPLATE_NAME:=generic-unsafe}"
export UCS_VERSION="${UCS_VERSION:=$release}"
export TARGET_VERSION="${UCS_VERSION}"
export RELEASE_UPDATE="${release_update:=public}"
export ERRATA_UPDATE="${errata_update:=testing}"
export TEST_SECTIONS="${sections}"

declare -a cmd=("ucs-kvm-create" "-c" "$CFG_FILE")
"$HALT" && cmd+=("-t")
"${cmd[@]}"
test -e "./COMMAND_SUCCESS"
