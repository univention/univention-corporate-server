#!/bin/bash
#
# Execute UCS product tests in EC2 or KVM environment
#

set -x

if command -v git >/dev/null 2>&1
then
	head="$(git describe --tags --match 'release-[1-9].[0-9]-[0-9]')" && release="${head:8:5}"
fi
[ -n "${release:-}" ] || release='4.4-0'

export RELEASE_UPDATE="${release_update:-public}"
export ERRATA_UPDATE="${errata_update:-testing}"
export TARGET_VERSION="${TARGET_VERSION:=$release}"
export UCS_VERSION="${UCS_VERSION:=$release}"
export TEMPLATE_VERSION="${TEMPLATE_VERSION:=$UCS_VERSION}"
export UCSSCHOOL_RELEASE=${UCSSCHOOL_RELEASE:=scope}
export KVM_BUILD_SERVER="${KVM_BUILD_SERVER:=lattjo.knut.univention.de}"
export KVM_USER="${KVM_USER:=$USER}"
if [ "$KVM_USER" = "jenkins" ]; then
	KVM_USER="build"
fi
export HALT="${HALT:=true}"
export CFG="$1"

# create the command and run in ec2 or kvm depending on cfg
if ! grep -Fq kvm_template "$CFG"
then
	exe='ucs-ec2-create'
else
	exe='ucs-kvm-create'
fi
declare -a cmd=("$exe" -c "$CFG")
"$HALT" && cmd+=("-t")
# shellcheck disable=SC2123
PATH="${PATH:+$PATH:}./ucs-ec2-tools"
"${cmd[@]}" &&
[ -e "./COMMAND_SUCCESS" ]
