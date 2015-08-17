#!/bin/bash
#
# Copyright 2014-2015 Univention GmbH
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

ucsschool-fetch-results () {
	# ucsschool-fetch-results <IP-ADDRESS>
	local ADDR="$1"
	local TARGETDIR="$2"
	if [ -n "$TARGETDIR" ] ; then
		[ ! -d "$TARGETDIR" ] && mkdir -p "$TARGETDIR"
	else
		TARGETDIR="."
	fi
	scp -i ~/ec2/keys/tech.pem -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@${ADDR}:ucs-test.log "$TARGETDIR"
	scp -i ~/ec2/keys/tech.pem -r -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@${ADDR}:test-reports "$TARGETDIR"
	scp -i ~/ec2/keys/tech.pem -r -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@${ADDR}:/var/log/univention/management* "$TARGETDIR"
	scp -i ~/ec2/keys/tech.pem -r -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@${ADDR}:"/var/log/univention/{join,setup,listener,system-stats}.log" "$TARGETDIR"
	scp -i ~/ec2/keys/tech.pem -r -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@${ADDR}:"/var/log/{syslog,auth.log}" "$TARGETDIR"
	scp -i ~/ec2/keys/tech.pem -r -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@${ADDR}:/var/log/univention/connector* "$TARGETDIR"
	scp -i ~/ec2/keys/tech.pem -r -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@${ADDR}:/var/log/samba/* "$TARGETDIR"
	scp -i ~/ec2/keys/tech.pem -r -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@${ADDR}:"/var/log/{mail,dovecot}.log" "$TARGETDIR"
}

ec2-start-job-async () {
	# Start a job asynchronously
	# <EXAMPLE>: update all servers at once instead of waiting for each one
	# in command N on all affected servers:
	# commandN:
	#   LOCAL examples/jenkins/utils/utils-local.sh ec2-start-job-async job-upgrade [hostX_IP] hostX ". utils.sh; upgrade_to_latest --updateto 3.2-99"
	# Now all async jobs are running. Wait for them in command N+1 on one server:
	# commandN+1:
	#   LOCAL examples/jenkins/utils/utils-local.sh ec2-wait-for-async-job job-upgrade
	# </Example>
	# Warning: this will make your logfile mostly useless for the timespan a job is run on multiple hosts
	#   as the logs will get mixed. Use only for predictable jobs (update, serverjoin, ...)
	# Write a server-local file to indicate job is finished
	# Write a local file to keep track of all servers which started this job
	local JOBNAME="$1"
	local ADDR="$2"
	local THISSERVER="$3"
	local COMMAND="$4"
	ssh -f -i ~/ec2/keys/tech.pem -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@${ADDR} nohup "bash -c '($COMMAND; touch $THISSERVER-$JOBNAME-finished) &'"
	echo "$THISSERVER $ADDR" >> "$JOBNAME-local"
}

ec2-wait-for-async-job () {
	local JOBNAME="$1"
	echo "Waiting for job $JOBNAME to finish on all hosts"
	while true
	do
		# echo -n "job $JOBNAME finished on "
		local FINISHED=
		while IFS=' ' read SERVER ADDR; do
			if [ ! -e "$SERVER-$JOBNAME-finished" ]; then
				# check and copy
				scp -i ~/ec2/keys/tech.pem -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@\[${ADDR}\]:${SERVER}-${JOBNAME}-finished . >/dev/null 2>&1
			fi
			if [ ! -e "$SERVER-$JOBNAME-finished" ]; then
				local FINISHED=false
			else
				echo -n "$SERVER "
			fi
		done < "$JOBNAME-local"
		# echo
		[ -z $FINISHED ] && return 0
		sleep 10
	done
}

# === MAIN ===

ACTION="$1"
shift || exit 1

case "$ACTION" in
	ucsschool-fetch-results)
		ucsschool-fetch-results "$@"
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
