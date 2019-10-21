#!/bin/bash
#
# Copyright 2014-2017 Univention GmbH
#
# https://www.univention.de/
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
# <https://www.gnu.org/licenses/>.

: ${SSH_KEY:=$HOME/ec2/keys/tech.pem}

fetch-files () { # [<USER>@]<IP-ADDRESS> <REMOTE-FILE(S)> <DESTINATION> [SCP-ARGS...]
	local ADDR="${1#*@}"
	local USER="${1%$ADDR}"
	local FILES="$2"
	local TARGET="$3"
	shift 3
	[ $# -eq 0 ] && set -- -i "$SSH_KEY" -r -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no

	case "$ADDR" in [![]*:*:*[!]]) ADDR="[$ADDR]" ;; esac

	set -- scp "$@" "${USER:-root@}${ADDR}:${FILES}" "$TARGET"
	echo "$*"
	"$@"
}

fetch-results () { # <IP-ADDRESS> [TARGET-DIR]

	# check env
	if [ -n "$UCS_TEST_RUN" -a "$UCS_TEST_RUN" = "false" ]; then
		echo "ucs-test disabled by env UCS_TEST_RUN=$UCS_TEST_RUN, so no results i guess"
		return 0
	fi

	local ADDR="$1"
	local TARGETDIR="${2:-.}"
	mkdir -p "$TARGETDIR"
	mkdir -p "$TARGETDIR/selenium"
	declare -a FILES=(
		'artifacts'
		'packages-under-test.log'
		'test-reports'
		'ucs-test.log'
		'/usr/share/ucs-test/*/selenium'
		'/var/log/apache2/error.log'='apache2-error.log'
		'/var/log/auth.log*'=
		'/var/log/apt/term.log'
		'/var/log/daemon.log*'=
		'/var/log/dpkg.log'
		'/var/log/kern.log'
		'/var/log/dovecot.log*'=
		'/var/log/journalctl.log'
		'/var/log/mail.log*'=
		'/var/log/samba/*'=
		'/var/log/univention/sysvol-sync.log'
		'/var/log/syslog*'=
		'/var/log/univention/actualise.log'
		'/var/log/univention/appcenter.log'
		'/var/log/univention/config-registry.replog'='config-registry.replog.log'
		'/var/log/univention/connector*'=
		'/var/log/univention/coverage'
		'/var/log/univention/directory-manager-cmd.log'
		'/var/log/univention/join.log'
		'/var/log/univention/listener.log'
		'/var/log/univention/management*'=
		'/var/log/univention/setup.log'
		'/var/log/univention/system-stats.log'
		'/var/log/univention/ucs-windows-tools.log'
		'/var/log/univention/updater.log'
		'/var/log/univention/server_password_change.log'
		'/var/lib/univention-directory-replication/failed.ldif'
	)
	local FILE rc=0
	for FILE in "${FILES[@]}"; do
		fetch-files "root@${ADDR}" "${FILE%=*}" "${TARGETDIR}/${FILE##*[/=]}" || rc=$?
	done
	return 0  # $rc
}

fetch-coverage () {
	local ADDR="$1"
	local TARGETDIR="${2:-.}"
	mkdir -p "$TARGETDIR"
	fetch-files "root@${ADDR}" "htmlcov/" "$TARGETDIR"
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
