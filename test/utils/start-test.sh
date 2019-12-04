#!/bin/bash
#
# Execute UCS tests in EC2 or KVM environment
#

set -x

die () {
	echo "$*" >&2
	exit 1
}

[ -f "$1" ] ||
	die "Missing test config file!"

release='4.4-3'
old_release='4.3-5'
kvm_template_version='4.4-3'

# AMI: Univention Corporate Server (UCS) 4.4 (official image) rev. 5 - ami-0152c75b08efb2c99
export CURRENT_AMI=ami-0152c75b08efb2c99
# AMI: Univention Corporate Server (UCS) 4.3 (official image) rev. 6 - ami-0dd235a67a0eb9bdc
export OLD_AMI=ami-0dd235a67a0eb9bdc

export UCS_MINORRELEASE="${release%%-*}"
export TARGET_VERSION="${TARGET_VERSION:=$release}"
export UCS_VERSION="${UCS_VERSION:=$release}"
export OLD_VERSION="${OLD_VERSION:=$old_release}"
export KVM_TEMPLATE="${KVM_TEMPLATE:=generic-unsafe}"
export KVM_UCSVERSION="${KVM_UCSVERSION:=$kvm_template_version}"
export KVM_OLDUCSVERSION="${KVM_OLDUCSVERSION:=$OLD_VERSION}"
export KVM_BUILD_SERVER="${KVM_BUILD_SERVER:=lattjo.knut.univention.de}"
export KVM_MEMORY="${KVM_MEMORY:=2048M}"
export KVM_CPUS="${KVM_CPUS:=1}"
export RELEASE_UPDATE="${release_update:=public}"
export ERRATA_UPDATE="${errata_update:=testing}"
export UCSSCHOOL_RELEASE=${UCSSCHOOL_RELEASE:=scope}
export CFG="$1"

# jenkins defaults
if [ "$USER" = "jenkins" ]; then
	export UCS_TEST_RUN="${UCS_TEST_RUN:=true}"
	export HALT="${HALT:=true}"
	export KVM_USER="build"
	# in jenkins do not terminate VMs if setup is broken,
	# so we can investigate the situation and use replace
	# to overwrite old VMs
	export TERMINATE_ON_SUCCESS="${HALT:=true}"
	export REPLACE="${REPLACE:=true}"
else
	export HALT="${HALT:=false}"
	export UCS_TEST_RUN="${UCS_TEST_RUN:=false}"
	export KVM_USER="${KVM_USER:=$USER}"
	export TERMINATE_ON_SUCCESS="${TERMINATE_ON_SUCCESS:=false}"
	export REPLACE="${REPLACE:=false}"
fi


# if the default branch of UCS@school is given, then build UCS else build UCS@school
if [ -n "$UCSSCHOOL_BRANCH" ] || [ -n "$UCS_BRANCH" ]; then
	BUILD_HOST='10.200.18.180'
	REPO_UCS='git@git.knut.univention.de:univention/ucs.git'
	REPO_UCSSCHOOL='git@git.knut.univention.de:univention/ucsschool.git'
	if echo "$UCSSCHOOL_BRANCH" | grep -Eq '^[0-9].[0-9]$' ; then
		BUILD_BRANCH="$UCS_BRANCH"
		BUILD_REPO="$REPO_UCS"
	else
		BUILD_BRANCH="$UCSSCHOOL_BRANCH"
		BUILD_REPO="$REPO_UCSSCHOOL"
	fi
	# check branch test
	ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no "jenkins@${BUILD_HOST}" python3 \
		/home/jenkins/build -r "${BUILD_REPO}" -b "${BUILD_BRANCH}" \
		> utils/apt-get-branch-repo.list ||
		die 'Branch build failed'
	# replace non deb lines
	sed -i '/^deb /!d' utils/apt-get-branch-repo.list
fi

# create the command and run in ec2 or kvm depending on cfg
KVM=false
grep -q '^\w*kvm_template' "$CFG" && KVM=true # if kvm is configure in cfg, use kvm
[ "$KVM_BUILD_SERVER" = "EC2" ] && KVM=false

if "$KVM"; then
	exe='ucs-kvm-create'
else
	exe='ucs-ec2-create'
fi

# start the test
declare -a cmd=("$exe" -c "$CFG")
"$HALT" && cmd+=("-t")
"$REPLACE" && cmd+=("--replace")
"$TERMINATE_ON_SUCCESS" && cmd+=("--terminate-on-success")
# shellcheck disable=SC2123
PATH="./ucs-ec2-tools${PATH:+:$PATH}"

"${cmd[@]}" &&
	[ -e "./COMMAND_SUCCESS" ]
