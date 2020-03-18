#!/bin/bash
#
# Execute UCS tests in EC2 or KVM environment
#

set -e -u # -x

die () {
	echo "$*" >&2
	exit 1
}

[ -f "$1" ] ||
	die "Missing test config file!"

release='4.4-4'
old_release='4.3-5'
kvm_template_version='4.4-4'

# AMI: Univention Corporate Server (UCS) 4.4 (official image) rev. 6 - ami-02f34c72ec4c3d912
export CURRENT_AMI=ami-02f34c72ec4c3d912
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
export KVM_MEMORY="${KVM_MEMORY:=2G}"
export KVM_CPUS="${KVM_CPUS:=1}"
export RELEASE_UPDATE="${release_update:=public}"
export ERRATA_UPDATE="${errata_update:=testing}"
export UCSSCHOOL_RELEASE=${UCSSCHOOL_RELEASE:=scope}
CFG="$1"

# Jenkins defaults
if [ "$USER" = "jenkins" ]; then
	export UCS_TEST_RUN="${UCS_TEST_RUN:=true}"
	HALT="${HALT:=true}"
	export KVM_USER="build"
	# in Jenkins do not terminate VMs if setup is broken,
	# so we can investigate the situation and use replace
	# to overwrite old VMs
	TERMINATE_ON_SUCCESS="${HALT:=true}"
	REPLACE="${REPLACE:=true}"
else
	HALT="${HALT:=false}"
	export UCS_TEST_RUN="${UCS_TEST_RUN:=false}"
	export KVM_USER="${KVM_USER:=$USER}"
	TERMINATE_ON_SUCCESS="${TERMINATE_ON_SUCCESS:=false}"
	REPLACE="${REPLACE:=false}"
fi


# if the default branch of UCS@school is given, then build UCS else build UCS@school
if [ -n "${UCSSCHOOL_BRANCH:-}" ] || [ -n "${UCS_BRANCH:-}" ]; then
	BUILD_HOST='10.200.18.180'
	REPO_UCS='git@git.knut.univention.de:univention/ucs.git'
	REPO_UCSSCHOOL='git@git.knut.univention.de:univention/ucsschool.git'
	case "${UCSSCHOOL_BRANCH:-}" in
	''|[0-9].[0-9])
		BUILD_BRANCH="$UCS_BRANCH"
		BUILD_REPO="$REPO_UCS"
		;;
	*)
		BUILD_BRANCH="$UCSSCHOOL_BRANCH"
		BUILD_REPO="$REPO_UCSSCHOOL"
		;;
	esac
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
"${EXACT_MATCH:=false}" && cmd+=("-e")
"${SHUTDOWN:-false}" && cmd+=("-s")
# shellcheck disable=SC2123
PATH="./ucs-ec2-tools${PATH:+:$PATH}"
echo "starting test with ${cmd[*]}"
env | sort

"${cmd[@]}" &&
	[ -e "./COMMAND_SUCCESS" ]
