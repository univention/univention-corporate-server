#!/bin/bash
#
# Execute UCS tests in EC2 or KVM or OS environment
#

# defaults for release
release='5.2-2'  #
export CURRENT_AMI="${CURRENT_AMI:=ami-039f255d4476078f3}"  # AMI: Univention Corporate Server (UCS) 5.2 (official image) rev. 3
old_release='5.0-10'  #
export OLD_AMI="${OLD_AMI:=ami-00c198b3f9bb2c1ba}"  # AMI: Univention Corporate Server (UCS) 5.0 (official image) rev. 11
export KVM_UCSVERSION="${KVM_UCSVERSION:=5.2-2+e118}"  #
export OPENSTACK_IMAGE_VERSION="${OPENSTACK_IMAGE_VERSION:=5.2-1}"  # version for the openstack image
export OPENSTACK_IMAGE_NAME="${OPENSTACK_IMAGE_NAME:=UCS $OPENSTACK_IMAGE_VERSION}"  # name of the default openstack image
export OPENSTACK_IMAGE_NAME_OLD="UCS $old_release"
export UCS_MINORRELEASE="${release%%-*}"
export RANDOM_UCS_ROOT_PASSWORD="${RANDOM_UCS_ROOT_PASSWORD:=$(shuf -zern32 {A..Z} {a..z} {0..9})}"  # used in some scenarios to hide the password. access by certificate (or pass it yourself or look at the environment)
export TARGET_VERSION="${TARGET_VERSION:=$release}"
export UCS_VERSION="${UCS_VERSION:=$release}"
export OLD_VERSION="${OLD_VERSION:=$old_release}"
export KVM_OPERATING_SYSTEM="${KVM_OPERATING_SYSTEM:=Others}"
export KVM_TEMPLATE="${KVM_TEMPLATE:=generic-unsafe}"
export KVM_OLDUCSVERSION="${KVM_OLDUCSVERSION:=$old_release}"
export KVM_BUILD_SERVER="${KVM_BUILD_SERVER:=tross.knut.univention.de}"
export KVM_MEMORY="${KVM_MEMORY:=4096M}"
export KVM_CPUS="${KVM_CPUS:=1}"
export KVM_LABEL_SUFFIX="${KVM_LABEL_SUFFIX:=}"
export EXACT_MATCH="${EXACT_MATCH:=false}"
export SHUTDOWN="${SHUTDOWN:=false}"
export TERMINATE_ON_SUCCESS="${TERMINATE_ON_SUCCESS:=false}"
export RELEASE_UPDATE="${release_update:=public}"
export ERRATA_UPDATE="${errata_update:=testing}"
export COMPONENT_VERSION="${COMPONENT_VERSION:=testing}"
export UCSSCHOOL_RELEASE=${UCSSCHOOL_RELEASE:=scope}
export SOURCE_ISO="${SOURCE_ISO:=/var/univention/buildsystem2/isotests/ucs_${release}-latest-amd64.iso}"
_jenkins () { if [ -n "${JENKINS_HOME:-}" ]; then echo "${1:-true}"; else echo "${2:-false}"; fi; }
export KVM_USER="$(_jenkins build "${KVM_USER:=$USER}")"
export REPLACE="${REPLACE:=$(_jenkins)}"
export UCS_TEST_RUN="${UCS_TEST_RUN:=$(_jenkins)}"
export TERMINATE="${TERMINATE:=$(_jenkins)}"
export OS_CLOUD="${OS_CLOUD:=univention-development}"

# some internal stuff
image="${DIMAGE:-gitregistry.knut.univention.de/univention/infrastructure/ucs-ec2-tools:latest}"
: "${DEBUG:=false}"
: "${DOCKER:=true}"

docker_env_file="$(mktemp)"

have () {
	command -v "$1" >/dev/null 2>&1
}

RED='' GREEN='' BLUE='' NORM=''
if [ -n "${TERM:-}" ] && [ -t 1 ] && have tput
then
	term () {
		tput "$@"
	}
	RED="$(term setaf 1)"
	GREEN="$(term setaf 2)"
	BLUE="$(term setaf 4)"
	BOLD="$(term bold)"
	NORM="$(term sgr0)"
fi

usage () {
	echo "${GREEN}Usage:${NORM} [ENV_VAR=setting] ... ${0##*/} [options] <scenario.cfg>"
	echo ""
	echo "Start scenario defined in <scenario.cfg> in AWS-EC2, OpenStack or KVM"
	echo ""
	echo "${GREEN}Options:${NORM}"
	echo "  ${BOLD}-h${NORM}, ${BOLD}--help${NORM}    show this help message and exit"
	echo "  ${BOLD}-I${NORM}, ${BOLD}--ignore${NORM}  Ignore missing files"
	echo ""
	echo "${GREEN}Example:${NORM}"
	echo "  # start scenario with default options"
	echo "  ./utils/start-test.sh scenarios/autotest-090-master-no-samba.cfg"
	echo ""
	echo "  # start scenario with docker mode on KVM server 'tross'"
	echo "  KVM_BUILD_SERVER=tross DOCKER=true ./utils/start-test.sh scenarios/autotest-090-master-no-samba.cfg"
	echo ""
	echo "${GREEN}Environment variables:${NORM}"
	echo "  Environment variables marked '<' are used to modify the default behavior."
	echo "  Several additional variables marked '>' get derived and exported."
	echo "  Other variables marked '|' get just passed through."
	echo "  All can also be referenced in the .cfg file via [ENV:name]."
	echo "  The key 'environment:' in each VM section gets exported to the VM (UCS)."
	echo ""
	echo "  UCS"
	echo "    <>${BOLD}OLD_VERSION${NORM}          - previous UCS minor release [${BOLD}$OLD_VERSION${NORM}]"
	echo "    <>${BOLD}UCS_VERSION${NORM}          - current UCS release [${BOLD}$UCS_VERSION${NORM}]"
	echo "     >${BOLD}UCS_MINORRELEASE${NORM}     - current UCS minor release [${BOLD}$UCS_MINORRELEASE${NORM}]"
	echo "    <>${BOLD}TARGET_VERSION${NORM}       - UCS release to expect to update during update tests [${BOLD}$TARGET_VERSION${NORM}]"
	echo ""
	echo "  EC2"
	echo "    <>${BOLD}OLD_AMI${NORM}              - EC2 AMI for previous UCS minor release [${BOLD}$OLD_AMI${NORM}]"
	echo "    <>${BOLD}CURRENT_AMI${NORM}          - EC2 AMI for current UCS release [${BOLD}$CURRENT_AMI${NORM}]"
	echo ""
	echo "  KVM"
	echo "    <>${BOLD}KVM_TEMPLATE${NORM}         - KVM template name [${BOLD}$KVM_TEMPLATE${NORM}]"
	echo "    <>${BOLD}KVM_OLDUCSVERSION${NORM}    - KVM template version for previous minor release [${BOLD}$KVM_OLDUCSVERSION${NORM}]"
	echo "    <>${BOLD}KVM_UCSVERSION${NORM}       - KVM template version [${BOLD}$KVM_UCSVERSION${NORM}]"
	echo "    <>${BOLD}KVM_MEMORY${NORM}           - KVM RAM [${BOLD}$KVM_MEMORY${NORM}]"
	echo "    <>${BOLD}KVM_CPUS${NORM}             - KVM CPU's [${BOLD}$KVM_CPUS${NORM}]"
	echo "    <>${BOLD}KVM_LABEL_SUFFIX${NORM}     - additional label for KVM name [${BOLD}$KVM_LABEL_SUFFIX${NORM}]"
	echo "    | ${BOLD}KVM_KEYPAIR_PASSPHRASE${NORM} - ssh key passphrase and/or password for ssh VM connection"
	echo "    <>${BOLD}SOURCE_ISO${NORM}           - an ISO to mount [${BOLD}$SOURCE_ISO${NORM}]"
	echo ""
	echo "  OpenStack"
	echo "    <>${BOLD}OPENSTACK_IMAGE_NAME${NORM} - OS template name [${BOLD}$OPENSTACK_IMAGE_NAME${NORM}]"
	echo ""
	echo "  ucs-*-create"
	echo "    <>${BOLD}KVM_BUILD_SERVER${NORM}     - KVM build server|'EC2'|'OpenStack'|'Openstack'|'OS' [${BOLD}$KVM_BUILD_SERVER${NORM}]"
	echo "                             Overwritten by '*build_server:' from '.cfg'!"
	echo "    <>${BOLD}EXACT_MATCH${NORM}          - do --exact-match to exactly match template names [${BOLD}$EXACT_MATCH${NORM}]"
	echo "    <>${BOLD}SHUTDOWN${NORM}             - --shutdown VM after run [${BOLD}$SHUTDOWN${NORM}]"
	echo "    <>${BOLD}TERMINATE${NORM}            - --terminate-always VMs after run [${BOLD}$TERMINATE${NORM}][Jenkins:true]"
	echo "    <>${BOLD}TERMINATE_ON_SUCCESS${NORM} - --terminate-on-success VMs after run iff setup has been successful [${BOLD}$TERMINATE_ON_SUCCESS${NORM}]"
	echo "    <>${BOLD}REPLACE${NORM}              - --replace existing VM with same name [${BOLD}$REPLACE${NORM}][Jenkins:true]"
	echo ""
	echo "  update behaviour/dev or released version"
	echo "    < ${BOLD}release_update${NORM}       - 'public', 'testing' or 'none' for release updates [${BOLD}$RELEASE_UPDATE${NORM}]"
	echo "     >${BOLD}RELEASE_UPDATE${NORM}"
	echo "    < ${BOLD}errata_update${NORM}        - 'public', 'testing' or 'none' for errata updates [${BOLD}$ERRATA_UPDATE${NORM}]"
	echo "     >${BOLD}ERRATA_UPDATE${NORM}"
	echo "    <>${BOLD}UCSSCHOOL_RELEASE${NORM}    - U@S release [${BOLD}$UCSSCHOOL_RELEASE${NORM}]"
	echo "    <>${BOLD}COMPONENT_VERSION${NORM}    - update component? should indicate dev/released version of non UCS component (app, ...) [${BOLD}$COMPONENT_VERSION${NORM}]"
	echo "    | ${BOLD}SCOPE${NORM}                - extra APT repo/scope that can be included during test"
	echo "    | ${BOLD}TESTING${NORM}              - indicates unreleased UCS (e.g. testing)"
	echo ""
	echo "  ucs-test/fetch-results"
	echo "    <>${BOLD}UCS_TEST_RUN${NORM}         - start 'ucs-test' in 'utils/utils.sh::run_tests' and copy log files from VM"
	echo "                             in 'utils/utils-local.sh::fetch-results' [${BOLD}$UCS_TEST_RUN${NORM}][Jenkins:true]"
	echo ""
	echo "  internal"
	echo "    < ${BOLD}DOCKER${NORM}               - use docker container instead if local ucs-ec2-tools [${BOLD}$DOCKER${NORM}]"
	echo "    < ${BOLD}DIMAGE${NORM}               - docker image [${BOLD}${DIMAGE:--}${NORM}]"
	echo "    < ${BOLD}DEBUG${NORM}                - debug mode [${BOLD}${DEBUG:--}${NORM}]"
	echo ""
	echo "  apps"
	echo "    | ${BOLD}APP_ID${NORM}               - An app ID, wekan"
	echo "    | ${BOLD}COMBINED_APP_ID${NORM}      - ???"
}

die () {
	echo "${RED}$*${NORM}" >&2
	exit 1
}

cleanup () {
	"$DEBUG" ||
		rm -f "$docker_env_file"
}

trap cleanup EXIT

# read arguments
opts=$(getopt \
	--longoptions "help,ignore" \
	--name "$(basename "$0")" \
	--options "hI" \
	-- "$@"
) || die "see -h|--help"
eval set -- "$opts"
check_missing=true
while true
do
	case "$1" in
		-h|--help)
			usage
			exit 0
			;;
		-I|--ignore)
			check_missing=false
			shift
			;;
		--)
			shift
			break
			;;
	esac
done
[ -n "${1:-}" ] ||
	die "Missing test configuration file!"
CFG="$(readlink -f "$1")"
[ -s "$CFG" ] ||
	die "Missing test configuration file '$CFG'!"

# set JOB_NAME if empty to the basename of the cfg
if [ -z "$JOB_NAME" ]; then
	job_name="$(basename "$CFG")"
	export JOB_NAME="${job_name%.cfg}"
fi

# set JOB_BASE_NAME if empty to the basename of the cfg
if [ -z "$JOB_BASE_NAME" ]; then
	job_name="$(basename "$CFG")"
	export JOB_BASE_NAME="${job_name%.cfg}"
fi



if "$check_missing"
then
	[ -f ~/ec2/scripts/activate-errata-test-scope.sh ] ||
		die "Missing script ~/ec2/scripts/activate-errata-test-scope.sh to activate test errata repo!"
	[ -f ~/ec2/license/license.secret ] ||
		die "Missing secret file ~/ec2/license/license.secret for getting test license!"
	[ -f ~/ec2/keys/tech.pem ] ||
		die "Missing key file ~/ec2/keys/tech.pem to access instances!"
fi
[ -d ./utils ] ||
	cd "${0%/*}/../utils/.." ||
	! "$check_missing" ||
	die "./utils dir is missing!"

# get image from cfg if not explicitly as env var
if [ -z "$DIMAGE" ]; then
	i="$(sed -n 's/^docker_image: //p' "$CFG")"
	[ -n "$i" ] && image="$i"
fi

openstack_cfg () {
	for os_cfg in ${OS_CLIENT_CONFIG_FILE:+"$OS_CLIENT_CONFIG_FILE"} "${PWD}/clouds.yaml" "${HOME}/.config/openstack/clouds.yaml" /etc/openstack/clouds.yaml
	do
		[ -r "$os_cfg" ] && return
	done
	die "Missing clouds.yaml file for OS access!"
}


# build server can be overwritten per cfg file `build_server`
build_server="$(awk -F ": " '/^\w*build_server:/{print $2}' "$CFG")"
[ -n "$build_server" ] && KVM_BUILD_SERVER="$build_server"

# some jobs start KVM instances but need access to openstack
needs_openstack="$(awk -F ": " '/^\w*needs_openstack:/{print $2}' "$CFG")"
[ "$needs_openstack" = "true" ] && openstack_cfg

case "$KVM_BUILD_SERVER" in
EC2)
	[ -f ~/.boto ] ||
		die "Missing ~/.boto file for EC2 access!"
	exe="ucs-ec2-create"
	;;
Openstack|OpenStack|OS)
	openstack_cfg
	exe="ucs-openstack-create"
	;;
KVM|*)
	exe="ucs-kvm-create"
	;;
esac

# start the test
declare -a cmd=()
if "$DOCKER"
then
	# get latest version of image
	case "$image" in *.*/*) docker pull "$image" ;; esac
	# create env file
	{
		# get aws credentials
		[ "$exe" = "ucs-ec2-create" ] &&
			sed -rne '/^\[Credentials\]/,${/^\[Credentials\]/d;s/^ *(aws_(secret_)?access_key(_id)?) *= *(.*)/\U\1\E=\4/p;/^\[/q}' ~/.boto
		echo "AWS_DEFAULT_REGION=eu-west-1"
		env |
			grep -Eve '^(HOSTNAME|PATH|PWD|OLDPWD|SHELL|SHLVL|TEMP|TEMPDIR|TMPDIR)=|^(KDE|GTK[0-9]*|QT|XDG)_'
	} >"$docker_env_file"
	# TODO add ~/ec2/keys/tech.pem via env
	# TODO add personal ssh key for kvm server access via env

	# docker command
	cmd+=(
		"docker" "run"
		--rm
		-w /test
		-v "${PWD:-$(pwd)}:/test"
		-v "$HOME/ec2:$HOME/ec2:ro"
		-v "$CFG:$CFG:ro"
		--network host
		-u "${UID:-$(id -u)}"
		--env-file "$docker_env_file"
		--security-opt seccomp:unconfined
	)
	# paramiko-2.4 from Debian-10-Buster is too old to handle the new OpenSSH-7.x private key format generated by default by `ssh-keygen`.
	# Use `ssh-keygen -m PEM` or update to Paramiko-2.7!
	# If the private key is encrypted, KVM_PASSWORD must be passed with the passphrase. Because of that default to pass the ssh-agent into the Docker container.
	if [ -n "${SSH_AUTH_SOCK:-}" ]
	then
		cmd+=(
			-v "$SSH_AUTH_SOCK:/.ssh"
			-e 'SSH_AUTH_SOCK=/.ssh'
		)
	else
		cmd+=(
			-v "$HOME/.ssh:$HOME/.ssh:ro"
		)
	fi
	cmd+=(${os_cfg:+-v "$os_cfg:/etc/openstack/clouds.yml:ro"})
	# interactive mode for debug
	$DEBUG && cmd+=("-it")
	# the image to start
	cmd+=("$image")
fi

"$DEBUG" && "$DOCKER" && cmd+=("bash" '-s' '--')

cmd+=("$exe" -c "$CFG")
# TODO, add debug mode as switch by env variable or possibly there will be verbose modes instead
# [ "$exe" = "ucs-openstack-create" ] && cmd+=(--debug)
if "$TERMINATE_ON_SUCCESS"; then cmd+=("--terminate-on-success")
elif "$TERMINATE"; then cmd+=("--terminate-always")
elif "$SHUTDOWN"; then cmd+=("--shutdown")
fi
"$REPLACE" && cmd+=("--replace")
"$EXACT_MATCH" && cmd+=("--exact-match")

echo "${BLUE}Starting test"
sort -s -t= -k1 <"$docker_env_file"
echo "${cmd[*]}${NORM}"

if [ -n "$JOB_URL" ]; then
	header="$JOB_URL+++++++++++++++++++++++++++++++++++"
	printf "%${#header}s\n" | tr " " "+"
	echo "+ Jenkins Workspace: ${JOB_URL}ws           +"
	echo "+ Jenkins Workspace/test: ${JOB_URL}ws/test +"
	printf "%${#header}s\n" | tr " " "+"
fi

"${cmd[@]}"
