#!/bin/bash
#
# Copyright 2014-2017 Univention GmbH
#
# http://www.univention.de/
#
# All rights reserved.
#
# The source code of this program is made available
# under the terms of the GNU Affero General Public License version 3
# (GNU AGPL V3) as published by the Free Software Foundation.
#
# Binary versions of this program provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention and not subject to the GNU AGPL V3.
#
# In the case you use this program under the terms of the GNU AGPL V3,
# the program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <http://www.gnu.org/licenses/>.

: ${SSH_KEY:=$HOME/ec2/keys/tech.pem}

fetch-files () {
	# fetch-files <IP-ADDRESS> <REMOTE-FILE(S)> <DESTINATION> [SCP-ARGS]
	#
	# Enclose globs in <REMOTE-FILE(S)> in single ticks to prevent shell
	# expansion on the client side.
	local ADDR="$1"
	local FILES="$2"
	local TARGET="$3"
	local SCP_ARGS=${4:-"-i $SSH_KEY -r -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no"}

	echo "scp $SCP_ARGS $ADDR:$FILES $TARGET"
	echo "scp $SCP_ARGS $ADDR:$FILES $TARGET" | sh
}

fetch-results () {
	# fetch-results <IP-ADDRESS> [TARGET-DIR]
	local ADDR="$1"
	local TARGETDIR="${2:-.}"
	mkdir -p "$TARGETDIR"
	declare -a FILES=(
		ucs-test.log
		test-reports
		artifacts
		'/var/log/univention/management*'
		'/var/log/univention/{join,setup,listener,appcenter,actualise,system-stats,updater,directory-manager-cmd}.log'
		'/var/log/{syslog,auth.log}'
		'/var/log/univention/connector*'
		'/var/log/samba/*'
		'/var/log/{mail,dovecot,daemon}.log'
		'/var/log/univention/ucs-windows-tools.log'
	)
	local FILE
    # ipv6 !
    if [[ $ADDR =~ .*:.* ]]; then
        ADDR="\\[$ADDR\\]"
    fi
	for FILE in "${FILES[@]}"; do
		fetch-files root@${ADDR} "$FILE" "$TARGETDIR"
	done
	fetch-files root@${ADDR} /var/log/univention/config-registry.replog "$TARGETDIR/config-registry.replog.log"
	fetch-files root@${ADDR} /var/log/apache2/error.log "$TARGETDIR/apache2-error.log"
	# selenium
	mkdir -p "$TARGETDIR/selenium-screendumps/"
	fetch-files root@${ADDR} "/usr/share/ucs-test/*/selenium-screendumps/*" "$TARGETDIR/selenium/"
	return 0
}

fetch-coverage () {
	local ADDR="$1"
	local TARGETDIR="${2:-.}"
	mkdir -p "$TARGETDIR"
	fetch-files root@${ADDR} "htmlcov/" "$TARGETDIR"
}

ec2-start-job-async () {
	# Start a job asynchronously
	# <EXAMPLE>: update all servers at once instead of waiting for each one
	# in command N on all affected servers:
	# commandN:
	#   LOCAL utils/utils-local.sh ec2-start-job-async job-upgrade [hostX_IP] hostX ". utils.sh; upgrade_to_latest --updateto 3.2-99"
	# Now all async jobs are running. Wait for them in command N+1 on one server:
	# commandN+1:
	#   LOCAL utils/utils-local.sh ec2-wait-for-async-job job-upgrade
	# </Example>
	# Warning: this will make your logfile mostly useless for the timespan a job is run on multiple hosts
	#   as the logs will get mixed. Use only for predictable jobs (update, serverjoin, ...)
	# Write a server-local file to indicate job is finished
	# Write a local file to keep track of all servers which started this job
	local JOBNAME="$1"
	local ADDR="$2"
	local THISSERVER="$3"
	local COMMAND="$4"
	ssh -f -i "$SSH_KEY" -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@${ADDR} nohup "bash -c '($COMMAND; touch $THISSERVER-$JOBNAME-finished) &'"
	echo "$THISSERVER $ADDR" >> "$JOBNAME-local"
}

ec2-wait-for-async-job () {
	local JOBNAME="$1"
	echo "Waiting for job $JOBNAME to finish on all hosts"
	while true
	do
		local FINISHED=true SERVER ADDR
		while IFS=' ' read SERVER ADDR; do
			local fname="${SERVER}-${JOBNAME}-finished"
			[ -e "$fname" ] || continue
			# check and copy
			if fetch-files "[${ADDR}]" "$fname" . >/dev/null 2>&1 && [ -e "$fname" ]
			then
				echo -n " $SERVER"
			else
				FINISHED=false
			fi
		done < "$JOBNAME-local"
		"$FINISHED" && break
		sleep 10
	done
	echo
}

# === MAIN ===

ACTION="$1"
shift || exit 1

case "$ACTION" in
	fetch-results)
		fetch-results "$@"
		;;
	ucsschool-fetch-results)
		fetch-results "$@"
		;;
	fetch-coverage)
		fetch-coverage "$@"
		;;
	ec2-start-job-async)
		ec2-start-job-async "$@"
		;;
	ec2-wait-for-async-job)
		ec2-wait-for-async-job "$@"
		;;
	*)
		echo "Unknown action: $ACTION"
		;;
esac

# vim:set filetype=sh ts=4:
