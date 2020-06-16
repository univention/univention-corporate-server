#!/bin/bash
#
# Execute UCS tests in EC2 or KVM environment
#

# defaults for release
release='5.0-0'
old_release='4.4-5'
kvm_template_version='5.0-0+e0'
# AMI: Univention Corporate Server (UCS) 5.0
current_ami=TODO
# AMI: Univention Corporate Server (UCS) 4.4 (official image) rev. 7 - ami-0bbba0e6b007e1980
old_ami=ami-0bbba0e6b007e1980

# defaults
kvm_template='generic-unsafe'
kvm_build_server='lattjo.knut.univention.de'
kvm_memory='2048M'
kvm_cpus='1'
exact_match=false
ucsschool_release='scope'
shutdown=false

# some internal stuff
image=docker-registry.knut.univention.de/ucs-ec2-tools
debug="${DEBUG:=false}"
docker="${DOCKER:=false}"
docker_env_file="$(mktemp)"

usage () {
	echo "Usage: [ENV_VAR=setting] ... $(basename $0) [options] scenario.cfg"
	echo ""
	echo "Start scenario defined in scenario.cfg"
	echo ""
	echo "Options:"
	echo "  -h, --help  show this help message and exit"
	echo ""
	echo "Example:"
	echo ""
	echo "  # start scenario with default options"
	echo "  ./utils/start-test.sh scenarios/autotest-090-master-no-samba.cfg"
	echo ""
	echo "  # start scenario with docker mode on KVM server lattjo"
	echo "  KVM_BUILD_SERVER=lattjo DOCKER=true ./utils/start-test.sh scenarios/autotest-090-master-no-samba.cfg"
	echo ""
	echo "  These ENV_VARs can than be used in the cfg file ([ENV:KVM_BUILD_SERVER]) or if added to the section"
	echo "  environment in the cfg file as env variables in the virtuale instance (ucs)."
	echo ""
	echo "ENV_VARS:"
	echo ""
	echo "  ec2"
	echo "    CURRENT_AMI          - the ec2 ami for the current UCS release (default: $current_ami)"
	echo "    OLD_AMI              - the ec2 ami for the release before the current (default: $old_ami)"
	echo ""
	echo "  ucs"
	echo "    TARGET_VERSION       - the version to we expect to update during update tests (default: $release)"
	echo "    UCS_VERSION          - the current UCS version (default: $release)"
	echo "    UCS_MINORRELEASE     - the current minor version (default: ${release%%-*})"
	echo "    OLD_VERSION          - the UCS version before the current UCS release (default: $old_release)"
	echo ""
	echo "  kvm"
	echo "    KVM_TEMPLATE         - the KVM ucs-kt-get template to use (default: $kvm_template)"
	echo "    KVM_UCSVERSION       - the KVM ucs-kt-get template version (default: $kvm_template_version)"
	echo "    KVM_OLDUCSVERSION    - the KVM ucs-kt-get template version for the UCS release before the current release (default: $old_release)"
	echo "    KVM_BUILD_SERVER     - the KVM build server to use (default: $kvm_build_server)"
	echo "    KVM_MEMORY           - ram for the KVM instance (default: $kvm_memory)"
	echo "    KVM_CPUS             - cpu's for the KVM instance (default: $kvm_cpus)"
	echo ""
	echo "  ucs-*-create"
	echo "    EXACT_MATCH          - if true, add -e (only look for exact matches in template names) option to ucs-kvm-create (default: $exact_match)"
	echo "    SHUTDOWN             - if true, add -s (shutdown VMs after run) option to ucs-*-create (default: $shutdown)"
	echo "    HALT                 - if true, add -t (Terminate VMs after run) option to ucs-*-create (default: true for jenkins, otherwise false)"
	echo "    TERMINATE_ON_SUCCESS - if true, add --terminate-on-success ( Terminate VMs after run only if setup has been successful)"
	echo "                           to ucs-*-create (default: true for jenkins, otherwise false)"
	echo "    REPLACE              - if true, add --replace (if set, tries to terminate an instance similar to the to be created one)"
	echo "                           to ucs-*-create (default: true for jenkins, otherwise false)"
	echo ""
	echo "  update behaviour/dev or released version"
	# TODO make the env var a captial letter, -> modify jenkins seed job(s) and cfg files
	echo "    release_update       - public, testing or none for release updates (default: public)"
	# TODO see RELEASE_UPDATE
	echo "    errata_update        - public, testing or none for errata updates (default: testing)"
	echo "    UCSSCHOOL_RELEASE    - ucs school release (default: $ucsschool_release)"
	echo "    COMPONENT_UPDATE     - TODO Not implemented should indicate dev/released version of non ucs component (app, ...)"
	echo ""
	echo "  ucs-test/fetch-results"
	echo "    UCS_TEST_RUN         - if true, start ucs-test in utils/utils.sh::run_tests and copy log files from instance"
	echo "                           in utils/utils-local.sh::fetch-results (default: true for jenkins, otherwise false)"
	echo ""
	echo "  internal"
	echo "    DOCKER               - use docker container instead if local ucs-ec2-tools (default: false)"
	echo "    DEBUG                - debug mode (default: false)"
	echo ""
	echo "  ???"
	echo "    BUILD_BRANCH"
	echo "    BUILD_REPO"
}

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

# read arguments
opts=$(getopt \
	--longoptions "help" \
	--name "$(basename "$0")" \
	--options "h" \
	-- "$@"
)
[ $? != 0 ] && die "see -h|--help"
eval set -- $opts
while true; do
	case "$1" in
		-h|--help)
			usage
			exit 0
			;;
		--)
			shift
			break
			;;
	esac
done

[ -f "$1" ] || die "Missing test config file!"
[ -f ~/.boto ] || die "Missing ~/.boto file for ec2 access!"
[ -f ~/ec2/scripts/activate-errata-test-scope.sh ] || "Missing script ~/ec2/scripts/activate-errata-test-scope.sh to activate test errata repo!"
[ -f ~/ec2/license/license.secret ] || "Missing secret file ~/ec2/license/license.secret for getting test license!"
[ -f ~/ec2/keys/tech.pem ] || "Missing key file ~/ec2/keys/tech.pem for access to ec2 instances!"
[ -d ./utils ] || die "./utils dir is missing!"

# a list of important env vars that are passed to the docker container
env_vars="USER KVM_USER CURRENT_AMI OLD_AMI UCS_MINORRELEASE TARGET_VERSION UCS_VERSION OLD_VERSION KVM_TEMPLATE KVM_UCSVERSION KVM_OLDUCSVERSION KVM_BUILD_SERVER KVM_MEMORY KVM_CPUS EXACT_MATCH SHUTDOWN RELEASE_UPDATE ERRATA_UPDATE UCSSCHOOL_RELEASE CFG UCS_TEST_RUN HALT TERMINATE_ON_SUCCESS REPLACE BUILD_BRANCH BUILD_REPO NETINSTALL_IP1 NETINSTALL_IP2"

export CURRENT_AMI=${CURRENT_AMI:=$current_ami}
export OLD_AMI=${OLD_AMI:=$old_ami}
export UCS_MINORRELEASE="${release%%-*}"
export TARGET_VERSION="${TARGET_VERSION:=$release}"
export UCS_VERSION="${UCS_VERSION:=$release}"
export OLD_VERSION="${OLD_VERSION:=$old_release}"
export KVM_TEMPLATE="${KVM_TEMPLATE:=$kvm_template}"
export KVM_UCSVERSION="${KVM_UCSVERSION:=$kvm_template_version}"
export KVM_OLDUCSVERSION="${KVM_OLDUCSVERSION:=$old_release}"
export KVM_BUILD_SERVER="${KVM_BUILD_SERVER:=$kvm_build_server}"
export KVM_MEMORY="${KVM_MEMORY:=$kvm_memory}"
export KVM_CPUS="${KVM_CPUS:=$kvm_cpus}"
export EXACT_MATCH="${EXACT_MATCH:=$exact_match}"
export SHUTDOWN="${SHUTDOWN:=$shutdown}"
export RELEASE_UPDATE="${release_update:=public}"
export ERRATA_UPDATE="${errata_update:=testing}"
export UCSSCHOOL_RELEASE=${UCSSCHOOL_RELEASE:=$ucsschool_release}
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
	# TODO this does not work, scp in fetch-results fails with "unknown user 109"
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
