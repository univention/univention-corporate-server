#!/bin/bash
#
# Execute UCS tests in EC2 or KVM environment
#

release='4.4-5'
old_release='4.3-5'
kvm_template_version='4.4-5+e652'
image=docker-registry.knut.univention.de/ucs-ec2-tools
debug="${DEBUG:=false}"
docker="${DOCKER:=false}"
docker_env_file="$(mktemp)"

die () {
	echo "$*" >&2
	exit 1
}

cleanup () {
	if "$debug"; then
		[ -f "$docker_env_file" ] && rm "$docker_env_file"
	fi
}

trap cleanup EXIT

[ -f "$1" ] || die "Missing test config file!"
[ -f ~/.boto ] || die "Missing ~/.boto file for ec2 access!"
[ -f ~/ec2/scripts/activate-errata-test-scope.sh ] || "Missing script ~/ec2/scripts/activate-errata-test-scope.sh to activate test errata repo!"
[ -f ~/ec2/license/license.secret ] || "Missing secret file ~/ec2/license/license.secret for getting test license!"
[ -f ~/ec2/keys/tech.pem ] || "Missing key file ~/ec2/keys/tech.pem for access to ec2 instances!"
[ -d ./utils ] || die "./utils dir is missing!"

# a list of important env vars that are passed to the docker container
env_vars="USER KVM_USER CURRENT_AMI OLD_AMI UCS_MINORRELEASE TARGET_VERSION UCS_VERSION OLD_VERSION KVM_TEMPLATE KVM_UCSVERSION KVM_OLDUCSVERSION KVM_BUILD_SERVER KVM_MEMORY KVM_CPUS EXACT_MATCH SHUTDOWN RELEASE_UPDATE ERRATA_UPDATE UCSSCHOOL_RELEASE CFG UCS_TEST_RUN HALT TERMINATE_ON_SUCCESS REPLACE BUILD_BRANCH BUILD_REPO NETINSTALL_IP1 NETINSTALL_IP2"

# AMI: Univention Corporate Server (UCS) 4.4 (official image) rev. 7 - ami-0bbba0e6b007e1980
export CURRENT_AMI=ami-0bbba0e6b007e1980
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
export EXACT_MATCH="${EXACT_MATCH:=false}"
export SHUTDOWN="${SHUTDOWN:=false}"
export RELEASE_UPDATE="${release_update:=public}"
export ERRATA_UPDATE="${errata_update:=testing}"
export UCSSCHOOL_RELEASE=${UCSSCHOOL_RELEASE:=scope}
export CFG="$1"

# TODO, find a better way
# special ip's for net-install tests, we can't use kvm_dhcp as we need
# our own dhcp server for pxe, so create two ip adresses based on the
# ucs patch level version
export NETINSTALL_IP1=$(((${release##*-} + 3) * 2 ))
export NETINSTALL_IP2=$(($NETINSTALL_IP1 +1))

# Jenkins defaults
if [ "$USER" = "jenkins" ]; then
	export UCS_TEST_RUN="${UCS_TEST_RUN:=true}"
	export HALT="${HALT:=true}"
	export KVM_USER="build"
	# in Jenkins do not terminate VMs if setup is broken,
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
exe='ucs-ec2-create'
"$KVM" && exe='ucs-kvm-create'

# start the test
if "$docker"; then
	# get the image
	docker pull $image >/dev/null
	# create env file
	for env_var in $env_vars; do
		echo $env_var=${!env_var} >> $docker_env_file
	done
	# get aws credentials
	echo AWS_ACCESS_KEY_ID="$(cat ~/.boto | sed -n 's/^\w*aws_access_key_id *= *\(.*\)/\1/p')" >> $docker_env_file
	echo AWS_SECRET_ACCESS_KEY="$(cat ~/.boto | sed -n 's/^\w*aws_secret_access_key *= *\(.*\)/\1/p')" >> $docker_env_file
	# TODO add ~/ec2/keys/tech.pem via env
	# TODO add personal ssh key for kvm server access via env
	# docker command
	declare -a cmd=("docker" "run")
	cmd+=("-v" "$(pwd):/test" "-v" ~/ec2:/ec2:ro "-v" ~/.ssh/id_rsa:/.ssh/id_rsa:ro)
	cmd+=("--dns" "192.168.0.3" "--dns-search=knut.univention.de")
	cmd+=(-w /test)
	cmd+=(-u "$(id -u)")
	cmd+=(--rm)
	cmd+=(--env-file "$docker_env_file")
	cmd+=($image)
	cmd+=($exe -c $CFG)
else
	declare -a cmd=("$exe" -c "$CFG")
	# shellcheck disable=SC2123
	PATH="./ucs-ec2-tools${PATH:+:$PATH}"
fi

"$HALT" && cmd+=("-t")
"$REPLACE" && cmd+=("--replace")
"$TERMINATE_ON_SUCCESS" && cmd+=("--terminate-on-success")
"$EXACT_MATCH" && cmd+=("-e")
"$SHUTDOWN" && cmd+=("-s")

echo "starting test with ${cmd[*]}"
for env_var in $env_vars; do
	echo "  $env_var=${!env_var}"
done

"$debug" && exit 0

"${cmd[@]}" &&
	[ -e "./COMMAND_SUCCESS" ]
