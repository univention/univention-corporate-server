#!/bin/bash

set -e -u # -x

# LOCAL_UCS='/var/lib/jenkins/LOCAL/ucs.git'
LOCAL_UAS='/var/lib/jenkins/LOCAL/ucsschool.git'

die () {
	echo "${0##*/} ERROR: $*" >&2
	exit 1
}

[ -n "${WORKSPACE:-}" ] ||
	die "\$WORKSPACE is empty"

getGitlabURL () {
	local product="$1"
	local fn="${HOME}/secrets/gitlab_${product}.url"
	[ -f "$fn" ] ||
		die "the gitlab secret file for $product ($fn) does not exist or is no file!"
	cat "$fn"
}

case "${UCSSCHOOL_BRANCH:-}" in
''|[0-9].[0-9])
	;;
*)
	REPO_UCSSCHOOL="$(getGitlabURL ucsschool)"
	GIT_DIR_UCSSCHOOL="ucsschool.git"
	UAS="${WORKSPACE}/${GIT_DIR_UCSSCHOOL}"
	echo ">>> performing cleanup"
	rm -rf "$UAS"
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
	[ -d "$GIT_DIR_UCSSCHOOL/test" ] && cp -Rav "$GIT_DIR_UCSSCHOOL/test/"* "test/"
	;;
esac

cd test

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
export TEST_SECTIONS="${sections}"

exec utils/start-test.sh "$CFG_FILE"
